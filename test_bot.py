import unittest
import os
import json
import re
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add the current directory to the path so we can import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the discord and flask modules before importing main
sys.modules['discord'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
flask_mock = MagicMock()
sys.modules['flask'] = flask_mock

# Now we can import from main
from main import save_data, get_data, DATA_FILE, info, DiscordBot, bot_status, app, INDEX_HTML_TEMPLATE

class TestDiscordBot(unittest.TestCase):
    
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

if __name__ == '__main__':
    unittest.main()