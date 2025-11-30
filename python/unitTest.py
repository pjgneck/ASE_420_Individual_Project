import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from tkinter import Tk
from command_manager import CommandManagerApp  # assuming your class is in this file
from requests.exceptions import RequestException

class TestCommandManagerApp(unittest.TestCase):
    def setUp(self):
        self.root = Tk()
        self.commands = [{"id": 1, "command": "ls", "description": "list files", "last_used": "2025-01-01"}]
        self.devices = [{"id": 1, "device": "Router", "ip": "192.168.1.1"}]
        self.app = CommandManagerApp(self.root, self.commands, self.devices, token="c2f2b8a9-ebda-4fbe-b46c-08736d08d609", username="tester")

    @patch("requests.get")
    @patch("tkinter.messagebox.showerror")
    def test_fetch_data_success(self, mock_error, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"success": True, "commands": self.commands}

        result = self.app._fetch_data("/commands")
        self.assertEqual(result["commands"], self.commands)
        mock_error.assert_not_called()

    @patch("requests.get")
    @patch("tkinter.messagebox.showerror")
    def test_fetch_data_failure(self, mock_error, mock_get):
        # Raise a RequestException so _fetch_data catches it
        mock_get.side_effect = RequestException("Connection failed")
        
        result = self.app._fetch_data("/commands")
        
        self.assertIsNone(result)
        mock_error.assert_called_once_with("Connection Error", "Failed to connect to server: Connection failed")

    @patch("requests.request")
    @patch("ttkbootstrap.dialogs.Messagebox.show_info")
    @patch("tkinter.messagebox.showerror")
    def test_send_data_post_success(self, mock_error, mock_info, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {"success": True}

        data = {"command": "test"}
        result = self.app._send_data("/commands/add", data)
        self.assertTrue(result)
        mock_info.assert_called_once()
        mock_error.assert_not_called()

    @patch("tkinter.filedialog.askopenfilename")
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([{"command": "new", "description": "desc"}]))
    @patch.object(CommandManagerApp, "_send_data", return_value=True)
    @patch.object(CommandManagerApp, "refresh_commands_table")
    def test_import_commands_success(self, mock_refresh, mock_send, mock_file, mock_dialog):
        mock_dialog.return_value = "dummy.json"
        self.app.import_commands()
        mock_send.assert_called_once()
        mock_refresh.assert_called_once()

    @patch("tkinter.filedialog.asksaveasfilename")
    @patch("builtins.open", new_callable=mock_open)
    @patch("ttkbootstrap.dialogs.Messagebox.show_info")
    def test_export_commands_success(self, mock_info, mock_file, mock_dialog):
        mock_dialog.return_value = "export.json"
        self.app.export_commands()
        mock_file.assert_called_once_with("export.json", "w")
        mock_info.assert_called_once()

    @patch.object(CommandManagerApp, "_fetch_data", return_value={"commands": [{"id": 2, "command": "echo", "description": "print"}]})
    def test_refresh_commands_table_filters(self, mock_fetch):
        self.app.cmd_search_var.set("echo")
        self.app.cmd_filter_var.set("command")
        self.app.refresh_commands_table()
        items = self.app.cmd_tree.get_children()
        self.assertEqual(len(items), 1)
        self.assertEqual(self.app.cmd_tree.item(items[0])["values"][1], "echo")

if __name__ == "__main__":
    unittest.main()
