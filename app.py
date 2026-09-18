from pathlib import Path
import tempfile, uuid
import pandas as pd
import streamlit as st
from core import CodeKnowledgeBase, Store, cited_answer, create_demo

st.set_page_config(page_title='CodePath', page_icon='🧭', layout='wide')
st.markdown('''<style>.block-container{max-width:1200px;padding-top:2rem}.hero{padding:1.2rem 1.5rem;border-radius:18px;background:linear-gradient(120deg,#132238,#1f5064);color:white}.small{color:#65758b}.stProgress>div>div{background:#21a179}</style>''', unsafe_allow_html=True)
if 'kb' not in st.session_state: st.session_state.kb = CodeKnowledgeBase()
if 'sid' not in st.session_state: st.session_state.sid = str(uuid.uuid4())[:8]
if 'done' not in st.session_state: st.session_state.done = set()
db = Store()
kb = st.session_state.kb

st.markdown('<div class="hero"><h1>🧭 CodePath</h1><p>From first day to first trusted change — with evidence from the code.</p></div>', unsafe_allow_html=True)
with st.sidebar:
    st.header('Repository')
    path = st.text_input('Local repository path', placeholder='/path/to/repository')
    c1,c2=st.columns(2)
    if c1.button('Index', use_container_width=True):
        try:
            n=kb.index(path); db.log(st.session_state.sid,'indexed',path,n); st.success(f'{n} chunks indexed')
        except Exception as e: st.error(str(e))
    if c2.button('Use demo', use_container_width=True):
        demo=str(Path(tempfile.gettempdir())/'codepath_demo'); create_demo(demo); n=kb.index(demo); st.success(f'Demo indexed: {n} chunks')
    st.divider()
    st.caption('Session '+st.session_state.sid)
    st.caption('Local retrieval • cited evidence')

tabs=st.tabs(['Home','Ask the codebase','Architecture','Guided journey','Evaluation'])
with tabs[0]:
    st.subheader('Your onboarding cockpit')
    tasks=['orientation','entrypoint','trace','first_change']
    st.progress(len(st.session_state.done)/len(tasks), text=f'{len(st.session_state.done)} of {len(tasks)} milestones completed')
    a,b,c=st.columns(3)
    a.metric('Indexed chunks',len(kb.chunks)); b.metric('Files',len(set(x.path for x in kb.chunks))); c.metric('Milestones',len(st.session_state.done))
    st.info('Start with **Architecture**, then ask “Where should I start?” and complete the guided journey.')

with tabs[1]:
    st.subheader('Ask a question')
    q=st.text_input('Examples: How does authentication work? Where is the main entry point? What tests cover checkout?')
    if st.button('Find answer', type='primary') and q:
        hits=kb.search(q); db.log(st.session_state.sid,'question',q,len(hits)); st.markdown(cited_answer(q,hits))
        for i,(chunk,score) in enumerate(hits,1):
            with st.expander(f'[{i}] {chunk.path}:{chunk.start}–{chunk.end} · {score:.2f}'):
                st.code(chunk.text, language=Path(chunk.path).suffix.lstrip('.'))

with tabs[2]:
    st.subheader('Architecture map')
    if not kb.chunks: st.warning('Index a repository first.')
    else:
        ov=kb.overview(); st.session_state.done.add('orientation')
        c1,c2=st.columns([1,2])
        with c1:
            st.markdown('**Languages / formats**'); st.dataframe(pd.DataFrame(ov['languages'].items(),columns=['Extension','Files']),hide_index=True,use_container_width=True)
        with c2:
            st.markdown('**Repository tree**'); st.code('\n'.join(ov['files'][:120]) or 'No supported files')
        st.markdown('**Python symbols**'); st.write(', '.join(ov['symbols']) or 'No Python symbols detected.')
        if ov['imports']:
            st.markdown('**Import relationships**'); st.dataframe(pd.DataFrame(ov['imports'],columns=['Source','Imports']),hide_index=True,use_container_width=True)

with tabs[3]:
    st.subheader('First-day journey')
    journey=[
      ('orientation','1. Orient','Inspect the repository map. Identify the dominant language and the top-level documentation.'),
      ('entrypoint','2. Find an entry point','Ask the assistant where execution begins. Verify the answer by opening its citation.'),
      ('trace','3. Trace one behavior','Choose a user-visible behavior and trace it from entry point to business logic and test.'),
      ('first_change','4. Plan a safe first change','Name the file, expected behavior, relevant test, and rollback approach before editing.')]
    for key,title,desc in journey:
        with st.container(border=True):
            st.markdown(f'#### {"✅" if key in st.session_state.done else "○"} {title}')
            st.write(desc)
            note=st.text_area('Evidence / notes',key='note_'+key,placeholder='Record file paths, symbols, and what you learned…')
            if st.button('Complete milestone',key='btn_'+key):
                st.session_state.done.add(key); db.log(st.session_state.sid,'milestone',key,1,note); st.rerun()
    st.markdown('#### Self-check')
    ans=st.radio('What should a trustworthy codebase answer include?', ['A confident explanation only','File/line evidence and uncertainty','The longest possible response'],index=None)
    if st.button('Check answer'):
        ok=ans=='File/line evidence and uncertainty'; db.log(st.session_state.sid,'self_check','evidence',float(ok)); st.success('Correct — evidence makes the answer verifiable.') if ok else st.error('Look for verifiable evidence and explicit uncertainty.')

with tabs[4]:
    st.subheader('Newcomer evaluation')
    confidence=st.slider('How confident are you navigating this codebase?',1,5,3)
    escalated=st.checkbox('I needed help from an experienced developer')
    feedback=st.text_area('Where did you get stuck? What explanation was missing?')
    if st.button('Save evaluation',type='primary'):
        db.log(st.session_state.sid,'evaluation','confidence',confidence,feedback); db.log(st.session_state.sid,'escalation','needed_help',float(escalated)); st.success('Evaluation saved.')
    rows=db.rows(); df=pd.DataFrame(rows,columns=['session','event','item','value','note','timestamp'])
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button('Download evaluation CSV',df.to_csv(index=False),'codepath_evaluation.csv','text/csv')

