import unittest
import os
import json
import re
from unittest.mock import patch, MagicMock, mock_open, call
import sys
import time

# Add the current directory to the path so we can import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the discord and flask modules before importing main
sys.modules['discord'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
flask_mock = MagicMock()
sys.modules['flask'] = flask_mock

# Now we can import from main
from main import save_data, get_data, DATA_FILE, info, DiscordBot, bot_status, app, INDEX_HTML_TEMPLATE
from main import check_bot_status, start_watchdog, manually_terminated, last_token, watchdog_interval

class TestDiscordBot(unittest.TestCase):
    
    def setUp(self):
        # Reset global variables before each test
        global manually_terminated, last_token
        manually_terminated = False
        last_token = None
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('os.makedirs')
    def test_save_data(self, mock_makedirs, mock_json_dump, mock_file_open):
        # Test that save_data calls the right functions
        save_data()
        
        # Check if the directory was created
        mock_makedirs.assert_called_once()
        
        # Check if the file was opened for writing
        mock_file_open.assert_called_once_with(DATA_FILE, 'w')
        
        # Check if json.dump was called with the right arguments
        mock_json_dump.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_data_with_token(self, mock_json_dump, mock_file_open):
        # Set a token
        global last_token
        last_token = "test_token"
        
        # Call save_data
        save_data()
        
        # Check if json.dump was called with a dictionary containing the token
        args, _ = mock_json_dump.call_args
        self.assertIn('last_token', args[0])
        self.assertEqual(args[0]['last_token'], "test_token")
        
    @patch('builtins.open', new_callable=mock_open, read_data='{"channel_id": 123456789}')
    @patch('json.load', return_value={"channel_id": 123456789})
    def test_get_data(self, mock_json_load, mock_file_open):
        # Reset info to empty dict
        global info
        info.clear()
        
        # Test that get_data loads data correctly
        get_data()
        
        # Check if the file was opened for reading
        mock_file_open.assert_called_once_with(DATA_FILE, 'r')
        
        # Check if json.load was called
        mock_json_load.assert_called_once()
        
        # Check if info was updated
        self.assertEqual(info, {"channel_id": 123456789})
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"channel_id": 123456789, "last_token": "test_token"}')
    @patch('json.load', return_value={"channel_id": 123456789, "last_token": "test_token"})
    def test_get_data_with_token(self, mock_json_load, mock_file_open):
        # Reset info and token
        global info, last_token
        info.clear()
        last_token = None
        
        # Test that get_data loads data correctly
        get_data()
        
        # Check if the token was extracted
        self.assertEqual(last_token, "test_token")
        
        # Check if info doesn't contain the token
        self.assertNotIn("last_token", info)
        
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_get_data_file_not_found(self, mock_file_open):
        # Reset info to empty dict
        global info
        info.clear()
        
        # Test that get_data handles FileNotFoundError
        get_data()
        
        # Check if info remains empty
        self.assertEqual(info, {})
    
    def test_discord_bot_init(self):
        # Test that DiscordBot initializes correctly
        bot = DiscordBot("test_token")
        
        # Check if token is stored
        self.assertEqual(bot.token, "test_token")
        
        # Check if bot is initialized
        self.assertIsNotNone(bot.bot)
        
        # Check if running is False
        self.assertFalse(bot.running)
        
        # Check if error is None
        self.assertIsNone(bot.error)
    
    def test_bot_status_initial_values(self):
        # Test that bot_status has the correct initial values
        self.assertFalse(bot_status["running"])
        self.assertIsNone(bot_status["error"])
        
    def test_bot_status_has_deployment_id(self):
        # Test that bot_status has a deploymentId property
        self.assertIn("deploymentId", bot_status)
        # Test that deploymentId is a string
        self.assertIsInstance(bot_status["deploymentId"], str)
        # Test that deploymentId is a valid UUID
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
        self.assertTrue(uuid_pattern.match(bot_status["deploymentId"]))
    
    def test_flask_app_exists(self):
        # Test that the Flask app is properly defined
        self.assertIsNotNone(app)
        # Verify that app is a Flask application (mocked)
        self.assertTrue(hasattr(app, 'run'))
        
    def test_index_html_template_exists(self):
        # Test that the INDEX_HTML_TEMPLATE is properly defined
        self.assertIsNotNone(INDEX_HTML_TEMPLATE)
        # Verify that it contains expected content
        self.assertIn('Discord Bot Control Panel', INDEX_HTML_TEMPLATE)
        self.assertIn('{% if status.running %}', INDEX_HTML_TEMPLATE)
        self.assertIn('{% if status.error %}', INDEX_HTML_TEMPLATE)
        
    def test_token_input_is_password_type(self):
        # Test that the token input field is of type "password" for security
        self.assertIn('input type="password" id="token" name="token"', INDEX_HTML_TEMPLATE)
    
    def test_deployment_id_in_template(self):
        # Test that the deploymentId is included in the index.html template
        self.assertIn('Deployment ID: {{ status.deploymentId }}', INDEX_HTML_TEMPLATE)
        # Test that there's a CSS class for styling the deployment info
        self.assertIn('.deployment-info', INDEX_HTML_TEMPLATE)
    
    @patch('main.bot_instance')
    @patch('main.bot_thread')
    def test_check_bot_status_no_restart_when_running(self, mock_thread, mock_bot):
        # Setup
        global last_token, manually_terminated
        last_token = "test_token"
        manually_terminated = False
        mock_bot.running = True
        
        # Call the function
        check_bot_status()
        
        # Verify that stop was not called
        mock_bot.stop.assert_not_called()
    
    @patch('main.bot_instance')
    @patch('main.bot_thread')
    def test_check_bot_status_no_restart_when_manually_terminated(self, mock_thread, mock_bot):
        # Setup
        global last_token, manually_terminated
        last_token = "test_token"
        manually_terminated = True
        mock_bot.running = False
        
        # Call the function
        check_bot_status()
        
        # Verify that stop was not called
        mock_bot.stop.assert_not_called()
    
    @patch('time.sleep')
    @patch('main.DiscordBot')
    @patch('main.bot_instance')
    @patch('main.bot_thread')
    def test_check_bot_status_restart_when_not_running(self, mock_thread, mock_bot, mock_discord_bot, mock_sleep):
        # Setup
        global last_token, manually_terminated, bot_status
        last_token = "test_token"
        manually_terminated = False
        mock_bot.running = False
        
        # Mock the new bot instance
        new_bot = MagicMock()
        new_bot.running = True
        new_bot.error = None
        mock_discord_bot.return_value = new_bot
        
        # Mock the thread
        new_thread = MagicMock()
        new_bot.start.return_value = new_thread
        
        # Call the function
        check_bot_status()
        
        # Verify that a new bot was created with the last token
        mock_discord_bot.assert_called_once_with("test_token")
        
        # Verify that the new bot was started
        new_bot.start.assert_called_once()
        new_thread.start.assert_called_once()
        
        # Verify that bot_status was updated
        self.assertTrue(bot_status["running"])
        self.assertIsNone(bot_status["error"])
    
    @patch('threading.Thread')
    @patch('time.sleep')
    def test_start_watchdog(self, mock_sleep, mock_thread):
        # Setup
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Call the function
        result = start_watchdog()
        
        # Verify that a thread was created
        mock_thread.assert_called_once()
        
        # Verify that the thread was started
        mock_thread_instance.start.assert_called_once()
        
        # Verify that the thread is daemon
        self.assertTrue(mock_thread_instance.daemon)
        
        # Verify that the function returned the thread
        self.assertEqual(result, mock_thread_instance)

if __name__ == '__main__':
    unittest.main()