import app

# Test Hello World
def test_app():
    web = app.app.test_client()

    rv = web.get("/")
    assert rv.status == "200 OK"
    assert rv.data == b"<p>Hello, World!</p>"
