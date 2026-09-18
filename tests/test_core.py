from core import CodeKnowledgeBase, Store, create_demo

def test_index_search_and_overview(tmp_path):
    create_demo(str(tmp_path))
    kb=CodeKnowledgeBase()
    assert kb.index(str(tmp_path)) >= 3
    hits=kb.search('discount checkout')
    assert hits and hits[0][0].path in {'service.py','README.md','test_service.py'}
    assert 'service.py' in kb.overview()['files']

def test_metrics_store(tmp_path):
    store=Store(str(tmp_path/'events.db'))
    store.log('s1','evaluation','confidence',4,'clear')
    assert store.rows()[0][3] == 4

