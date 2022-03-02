"""Tests for app.py"""
import app


def test_app():
    """Test Hello World"""
    web = app.app.test_client()

    response = web.get("/")
    assert response.status == "200 OK"
    assert response.data == b"<p>Hello, World!</p>"
