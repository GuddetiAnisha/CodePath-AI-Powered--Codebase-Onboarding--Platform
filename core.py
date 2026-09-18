from __future__ import annotations

import ast
import json
import os
import re
import sqlite3
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

EXTENSIONS = {'.py','.js','.jsx','.ts','.tsx','.java','.go','.rs','.c','.h','.cpp','.hpp','.md','.txt','.yaml','.yml','.json','.toml'}
IGNORE = {'.git','.venv','venv','node_modules','dist','build','__pycache__','.pytest_cache','.idea','.vscode'}

@dataclass
class Chunk:
    path: str
    start: int
    end: int
    text: str

class CodeKnowledgeBase:
    def __init__(self):
        self.root = ''
        self.chunks: list[Chunk] = []
        self.vectorizer = TfidfVectorizer(stop_words='english', token_pattern=r'(?u)\b[\w./:-]{2,}\b')
        self.matrix = None

    def index(self, root: str, chunk_lines: int = 60, overlap: int = 10) -> int:
        base = Path(root).expanduser().resolve()
        if not base.is_dir():
            raise ValueError('Repository path must be an existing directory.')
        self.root, self.chunks = str(base), []
        for path in sorted(base.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in EXTENSIONS or any(p in IGNORE for p in path.parts):
                continue
            try:
                lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
            except OSError:
                continue
            step = max(1, chunk_lines - overlap)
            for start in range(0, len(lines), step):
                block = lines[start:start + chunk_lines]
                if any(x.strip() for x in block):
                    self.chunks.append(Chunk(str(path.relative_to(base)), start + 1, start + len(block), '\n'.join(block)))
                if start + chunk_lines >= len(lines): break
        docs = [f'{c.path}\n{c.text}' for c in self.chunks] or ['empty']
        self.matrix = self.vectorizer.fit_transform(docs)
        return len(self.chunks)

    def search(self, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
        if not self.chunks or self.matrix is None: return []
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        order = scores.argsort()[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in order if scores[i] > 0]

    def overview(self) -> dict:
        files = sorted({c.path for c in self.chunks})
        languages = {}
        for f in files: languages[Path(f).suffix or 'none'] = languages.get(Path(f).suffix or 'none', 0) + 1
        symbols, edges = [], []
        for f in files:
            if not f.endswith('.py'): continue
            try: tree = ast.parse((Path(self.root) / f).read_text(errors='ignore'))
            except (SyntaxError, OSError): continue
            symbols += [f'{f}: {n.name}' for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))][:20]
            for n in ast.walk(tree):
                if isinstance(n, ast.Import): edges += [(f, a.name) for a in n.names]
                elif isinstance(n, ast.ImportFrom) and n.module: edges.append((f, n.module))
        return {'files': files, 'languages': languages, 'symbols': symbols[:80], 'imports': edges[:100]}

def cited_answer(question: str, hits: list[tuple[Chunk, float]]) -> str:
    if not hits: return 'I could not find relevant evidence in the indexed repository. Try naming a component, symbol, endpoint, or file.'
    evidence = '\n\n'.join(f'[{i}] {c.path}:{c.start}-{c.end}\n{c.text[:1800]}' for i,(c,_) in enumerate(hits,1))
    key = os.getenv('OPENAI_API_KEY')
    if key:
        prompt = ('Answer using only the evidence. Explain for a newcomer, mention uncertainty, and cite every factual claim with [n].\n\n'
                  f'Question: {question}\n\nEvidence:\n{evidence}')
        body = json.dumps({'model':os.getenv('OPENAI_MODEL','gpt-4.1-mini'),'messages':[{'role':'user','content':prompt}],'temperature':0.1}).encode()
        req = urllib.request.Request(os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')+'/chat/completions', data=body,
            headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)['choices'][0]['message']['content']
        except Exception as exc:
            return f'LLM request failed ({type(exc).__name__}); showing retrieved evidence instead.\n\n' + evidence
    previews = []
    for i,(c,score) in enumerate(hits,1):
        meaningful = next((x.strip() for x in c.text.splitlines() if x.strip()), 'Relevant code')
        previews.append(f'- **{meaningful[:180]}** [{i}] — relevance {score:.2f}')
    return 'Most relevant codebase evidence:\n\n' + '\n'.join(previews) + '\n\nOpen the cited excerpts below to verify the answer.'

class Store:
    def __init__(self, path='codepath.db'):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, session TEXT, event TEXT, item TEXT, value REAL, note TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
        self.db.commit()
    def log(self, session, event, item='', value=0.0, note=''):
        self.db.execute('INSERT INTO events(session,event,item,value,note) VALUES(?,?,?,?,?)',(session,event,item,value,note)); self.db.commit()
    def rows(self):
        return self.db.execute('SELECT session,event,item,value,note,created_at FROM events ORDER BY id DESC').fetchall()

def create_demo(root: str):
    base = Path(root); base.mkdir(parents=True, exist_ok=True)
    (base/'service.py').write_text('''from dataclasses import dataclass\n\n@dataclass\nclass Order:\n    id: str\n    total: float\n\ndef calculate_discount(order: Order) -> float:\n    """Orders above 100 receive a ten percent discount."""\n    return order.total * 0.10 if order.total > 100 else 0.0\n\ndef checkout(order: Order) -> float:\n    return order.total - calculate_discount(order)\n''')
    (base/'README.md').write_text('# Demo shop\n\n`checkout` is the public entry point. Business rules live in `service.py`. Run `pytest` before changing discount behavior.\n')
    (base/'test_service.py').write_text('from service import Order, checkout\n\ndef test_discount():\n    assert checkout(Order("A1", 200)) == 180\n')

