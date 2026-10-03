from core import CodeKnowledgeBase, Store, create_demo


def test_index_search_and_overview(tmp_path):
    create_demo(str(tmp_path))
    kb = CodeKnowledgeBase()
    assert kb.index(str(tmp_path)) >= 3
    hits = kb.search('discount checkout')
    assert hits and hits[0][0].path in {'service.py', 'README.md', 'test_service.py'}
    assert 'service.py' in kb.overview()['files']


def test_demo_retrieval_benchmark(tmp_path):
    create_demo(str(tmp_path))
    kb = CodeKnowledgeBase()
    kb.index(str(tmp_path))

    cases = [
        ('Where is the checkout function implemented?', 'service.py'),
        ('What discount is applied to orders above 100?', 'service.py'),
        ('Which test verifies the discount behavior?', 'test_service.py'),
        ('What should I run before changing discount behavior?', 'README.md'),
    ]

    for query, expected_path in cases:
        hits = kb.search(query, k=3)
        assert hits, query
        assert hits[0][0].path == expected_path, (query, [h[0].path for h in hits])
        assert expected_path in [h[0].path for h in hits], query


def test_metrics_store(tmp_path):
    store = Store(str(tmp_path / 'events.db'))
    store.log('s1', 'evaluation', 'confidence', 4, 'clear')
    assert store.rows()[0][3] == 4
