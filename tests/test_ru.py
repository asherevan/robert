import unittest
from unittest import mock

import requests

import ru


class TestRuNetworkHandling(unittest.TestCase):
    def test_send_event_handles_connection_errors(self):
        with mock.patch("requests.post", side_effect=requests.exceptions.ConnectionError("connection refused")):
            with mock.patch("builtins.print") as mocked_print:
                ru.send_event("voice", "voice_command", {"text": "hello"}, priority="high")
        output = "\n".join(call.args[0] for call in mocked_print.call_args_list if call.args)
        self.assertTrue("Connection" in output or "connection refused" in output)

    def test_send_input_handles_connection_errors(self):
        with mock.patch("requests.post", side_effect=requests.exceptions.ConnectionError("connection refused")):
            with mock.patch("builtins.print") as mocked_print:
                ru.send_input("current_time", "2026-08-23 12:00:00")
        output = "\n".join(call.args[0] for call in mocked_print.call_args_list if call.args)
        self.assertTrue("Connection" in output or "connection refused" in output)


if __name__ == "__main__":
    unittest.main()
