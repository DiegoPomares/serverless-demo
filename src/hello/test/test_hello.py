from index import handler


def test_hello():
    event = {'params': {'querystring': {}}}
    assert handler(event, None) == "Hello World!"
