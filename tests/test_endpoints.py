import os
from unittest import TestCase


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
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "<h3>Usage</h3>",
            response.get_data(as_text=True),
            "Expected index content to be returned",
        )

    def test_view_log_simple(self):
        FILE_NAME = "example.log"
        response = self.client.get(f"/var/log/{FILE_NAME}")
        self.assertEqual(response.status_code, 200)
        with open(f"tests/logs/{FILE_NAME}") as fd:
            lines_expected = fd.readlines()[-3:]
            for line in lines_expected:
                self.assertIn(
                    line, response.get_data(as_text=True), "Expected exact logs content"
                )

    def test_zipped_not_supported(self):
        response = self.client.get("/var/log/zippy.tar.gz")
        self.assertEqual(response.status_code, 400, "HTTP 400 if zipped extension")
        self.assertIn(
            "Zipped files are not supported",
            response.get_data(as_text=True),
            "Expected file zipped file error",
        )
        response = self.client.get("/var/log/zippy.zip")
        self.assertEqual(response.status_code, 400, "HTTP 400 if zipped extension")
        self.assertIn(
            "Zipped files are not supported",
            response.get_data(as_text=True),
            "Expected file zipped file error",
        )

    def test_file_with_no_extension(self):
        response = self.client.get("/var/log/plain")
        self.assertEqual(
            response.status_code, 404, "HTTP 404 and not 400 as passes extension check"
        )
        self.assertIn(
            "file not found",
            response.get_data(as_text=True),
            "Expected HTTP 404 and not 400 as passes extension check",
        )

    def test_file_not_found(self):
        response = self.client.get("/var/log/doesnt_exist.log")
        self.assertEqual(response.status_code, 404, "Return HTTP 404 if file not found")
        self.assertIn(
            "not found",
            response.get_data(as_text=True),
            "Expected file not found error",
        )

    def test_malicious_path_encoded_parent(self):
        # https://owasp.org/www-community/attacks/Path_Traversal
        response = self.client.get("/var/log/%2e%2e%2f%2e%2e%2fetc/passwd")
        self.assertIsNotNone(self.ctx)
        self.assertIn(
            "not found",
            response.get_data(as_text=True),
            "Expected file not found error",
        )
        self.assertEqual(response.status_code, 404, "Return HTTP 404 if file not found")

    def test_malicious_path_parent(self):
        response = self.client.get("/var/log/../../etc/passwd")
        self.assertIsNotNone(self.ctx)
        self.assertIn(
            "not found",
            response.get_data(as_text=True),
            "Expected file not found error",
        )
        self.assertEqual(response.status_code, 404, "Return HTTP 404 if file not found")

    def test_view_log_characters(self):
        FILE_NAME = "example_characters.log"
        response = self.client.get(f"/var/log/{FILE_NAME}")
        self.assertEqual(response.status_code, 200)

        with open(f"tests/logs/{FILE_NAME}") as fd:
            expected = list(reversed(fd.readlines()))
            returned = response.get_data(as_text=True).split()
            for line_expected, line_retuned in zip(
                expected,
                returned,
            ):
                self.assertEqual(
                    line_expected.strip(),
                    line_retuned.strip(),
                    "Expected exact logs content but in reverse",
                )

    def test_search_bad_arguments_keyword(self):
        response = self.client.get(f"/var/log/example_characters.log?keyword=1")
        self.assertEqual(response.status_code, 400, "HTTP 400 bad request")
        self.assertIn(
            "Search keyword must be strictly 1 &lt; n &lt; 1001",
            response.get_data(as_text=True),
            "Expected error for invalid parameter keyword value",
        )

    def test_search_bad_arguments_n(self):
        response = self.client.get(f"/var/log/example_characters.log?keyword=11&n=0")
        self.assertEqual(response.status_code, 400, "HTTP 400 bad request")
        self.assertIn(
            "n must be strictly 0 &lt; n &lt; 100000001",
            response.get_data(as_text=True),
            "Expected error for invalid parameter n value",
        )

    def test_no_keyword_found_in_response(self):
        response = self.client.get(f"/var/log/example_characters.log?keyword=00")
        self.assertEqual(
            response.status_code, 200, "HTTP 200 expected regardless of results"
        )
        self.assertEqual(
            "",
            response.get_data(as_text=True),
            "Expected empty results in response due to not matching",
        )

    def test_keyword_with_results(self):
        response = self.client.get(f"/var/log/example_characters.log?keyword=a1")
        self.assertEqual(response.status_code, 200, "Keyword is in content")
        self.assertIn(
            "a1",
            response.get_data(as_text=True),
            "Expected search keyword in response",
        )
