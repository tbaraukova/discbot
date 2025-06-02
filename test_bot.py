import unittest
import os
import json
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add the current directory to the path so we can import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the discord module before importing main
sys.modules['discord'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Now we can import from main
from main import save_data, get_data, DATA_FILE, info

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
mock_file_open.assert_called_once_with(DATA_FILE, 'w')
        
        # Check if json.dump was called with the right arguments
        mock_json_dump.assert_called_once()
        
    @patch('builtins.open', new_callable=mock_open, read_data='{"channel_id": 123456789}')
    @patch('json.load', return_value={"channel_id": 123456789})
    def test_get_data(self, mock_json_load, mock_file_open):
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
        # Test that get_data handles FileNotFoundError
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
        
if __name__ == '__main__':
    unittest.main()