import os
from unittest import TestCase
from itertools import zip_longest


class TestEndpoints(TestCase):
    def setUp(self) -> None:
        os.environ["LC_VAR_LOG_DIR"] = "tests/logs/"
        from log_collection import app as flask_app

        self.ctx = flask_app.app.app_context()
        self.ctx.push()
        self.client = flask_app.app.test_client()
        return super().setUp()

    def tearDown(self) -> None:
        self.ctx.pop()
        return super().tearDown()

    def test_index(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert "<h3>Usage</h3>" in response.get_data(
            as_text=True
        ), "Expected index content to be returned"

    def test_view_log_simple(self):
        response = self.client.get("/var/log/example.log")
        assert response.status_code == 200
        with open("tests/logs/example.log") as fd:
            lines_expected = fd.readlines()[-3:]
            for line in lines_expected:
                assert line in response.get_data(
                    as_text=True
                ), "Expected exact logs content"

    def test_file_not_found(self):
        response = self.client.get("/var/log/doesnt_exist.log")
        assert "not found" in response.get_data(
            as_text=True
        ), "Expected file not found error"
        assert response.status_code == 404, "Return HTTP 404 if file not found"
