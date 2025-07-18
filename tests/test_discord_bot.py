import unittest
from unittest.mock import patch
from discord_bot.main import bot

class TestDiscordBot(unittest.TestCase):

    def test_bot_created(self):
        self.assertIsNotNone(bot)

    def test_ping_command_exists(self):
        self.assertIsNotNone(bot.get_command("ping"))

    @patch('requests.post')
    def test_search_command(self, mock_post):
        mock_post.return_value.json.return_value = {
            "results": [
                {
                    "content_chunk": {
                        "title": "Test Title",
                        "content": "Test Content",
                        "rulebook": "Test Rulebook",
                        "page_number": 1
                    }
                }
            ]
        }
        
        # This is a simplified test that doesn't actually run the bot.
        # It just checks that the command is registered.
        self.assertIsNotNone(bot.get_command("search"))

if __name__ == '__main__':
    unittest.main()