import discord
from discord.ext import commands
import yaml
import requests
import json

# Load configuration
with open("config/config.yaml", 'r') as f:
    config = yaml.safe_load(f)

# Set up the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def search(ctx, *, query: str):
    """Search for rulebook content."""
    payload = {"query": query}
    response = requests.post("http://localhost:8000/tools/search", json=payload)
    data = response.json()

    if data.get("results"):
        for result in data["results"]:
            embed = discord.Embed(
                title=result['content_chunk']['title'],
                description=result['content_chunk']['content'],
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Rulebook: {result['content_chunk']['rulebook']}, Page: {result['content_chunk']['page_number']}")
            await ctx.send(embed=embed)
    else:
        await ctx.send("No results found.")

def run_bot():
    bot.run(config['discord']['token'])

if __name__ == "__main__":
    run_bot()