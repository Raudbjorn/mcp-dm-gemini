import unittest
from unittest.mock import patch, MagicMock
import asyncio
from discord.ext import commands
import discord
from discord_bot.main import bot

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

class TestDiscordBot(unittest.TestCase):

    @patch('httpx.AsyncClient.post')
    async def test_search_command_with_results(self, mock_post):
        mock_post.return_value.__aenter__.return_value.status_code = 200
        mock_post.return_value.__aenter__.return_value.json.return_value = {
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
        await search_command.callback(ctx, query="test")

        ctx.send.assert_called_once()
        self.assertIn("Test Title", ctx.send.call_args[0][0])

    @patch('httpx.AsyncClient.post')
    async def test_search_command_no_results(self, mock_post):
        mock_post.return_value.__aenter__.return_value.status_code = 200
        mock_post.return_value.__aenter__.return_value.json.return_value = {"results": []}

        ctx = AsyncMock()
        search_command = bot.get_command("search")
        await search_command.callback(ctx, query="test")

        ctx.send.assert_called_once_with("No results found.")

if __name__ == '__main__':
    unittest.main()
