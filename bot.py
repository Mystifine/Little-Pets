from discord.ext import commands, tasks
from colors import color_data;
from monsterdata import monster_data;
from util import get_embedded_message_data, get_jsondata_from_file, set_jsondata_to_file;
from emoji import emoji_data;

import settings;
import discord;
import application_commands;
import os;
import firebase;
import asyncio;
  
def update_presence(client):
  guilds = client.guilds;
  users = client.users;
  game = discord.Game(f"Watching over {len(users)} member(s) and {len(guilds)} server(s)!")
  return client.change_presence(activity=game)

def init_bot():
  BOT_TOKEN = os.getenv("BOT_TOKEN");
  client = commands.Bot(allow_application_commands=True,command_prefix="/",intents=discord.Intents.all());

  @tasks.loop(seconds=600)
  async def change_status():
    await update_presence(client);

  @client.event
  async def on_ready():
    # Main thread

    # Finds all the servers the bot is in.
    for guild in client.guilds:
      for channel in guild.text_channels: #getting only text channels
        if channel.permissions_for(guild.me).create_instant_invite: #checking if you have permissions
          
          bot_stats = get_jsondata_from_file("bot-stats.json");

          # create a dictionary if it doesn't already exist
          if not "Discord Servers" in bot_stats:
            bot_stats['Discord Servers'] = {}

          if not guild.name in bot_stats['Discord Servers']:
            invite = await channel.create_invite(max_uses=1, temporary=False)
            bot_stats['Discord Servers'][guild.name] = invite.url;
            print(f"{guild.name}'s Invite: {invite.url} has been added to bot stats!")          

          set_jsondata_to_file('bot-stats.json', bot_stats);
               
    await update_presence(client)
    await application_commands.setup(client);
    change_status.start(); # initiate background loop
    print(f"{client.user} is now running!");

  client.run(BOT_TOKEN);

