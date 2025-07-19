import discord
from discord.ext import commands
import httpx
import yaml
from ttrpg_assistant.logger import logger

# Load configuration
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}')

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def search(ctx, *, query: str):
    logger.info(f"Received search command from Discord: '{query}'")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/tools/search",
            json={"query": query}
        )
        if response.status_code == 200:
            results = response.json()["results"]
            if results:
                reply = "\n\n".join([f"**{r['content_chunk']['title']}**\n{r['content_chunk']['content']}" for r in results])
                await ctx.send(reply)
            else:
                await ctx.send("No results found.")
        else:
            await ctx.send("Error performing search.")

if __name__ == "__main__":
    bot.run(config["discord"]["token"])
