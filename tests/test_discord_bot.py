import unittest
from unittest.mock import patch, AsyncMock
from discord_bot.main import bot
import discord
import asyncio

class TestDiscordBot(unittest.TestCase):

    def test_bot_created(self):
        self.assertIsNotNone(bot)

    def test_ping_command_exists(self):
        self.assertIsNotNone(bot.get_command("ping"))

    @patch('requests.post')
    def test_search_command_with_results(self, mock_post):
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
        
        ctx = AsyncMock()
        search_command = bot.get_command("search")
        asyncio.run(search_command.callback(ctx, query="test"))
        
        ctx.send.assert_called_once()
        self.assertIsInstance(ctx.send.call_args.kwargs['embed'], discord.Embed)

    @patch('requests.post')
    def test_search_command_no_results(self, mock_post):
        mock_post.return_value.json.return_value = {"results": []}
        
        ctx = AsyncMock()
        search_command = bot.get_command("search")
        asyncio.run(search_command.callback(ctx, query="test"))
        
        ctx.send.assert_called_once_with("No results found.")

if __name__ == '__main__':
    unittest.main()
