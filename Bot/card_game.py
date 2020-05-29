import json
import discord
import math
import random
import shlex
import asyncio
from discord.ext import commands
import urllib.parse
import json
import pymongo
from pymongo import MongoClient
from res.Player import Player

with open("auth.json") as f:
    auth = json.load(f)
    global cluster
    cluster = MongoClient(auth["mongo_key"])

db = cluster["game"]
db_players = db["players"]

players = []
for x in db_players.find():
    player = Player(x["_id"], x["username"], x["currency"], x["exp"], x["cards"])
    players.append(player)

# Auth bot
bot = discord.Client()
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    print('Bot is running')

# config options
with open('config.json') as f:
    global config
    config = json.load(f)
    f.close()

# bot message
@bot.event
async def on_message(message):
    # spawn a card
    # rarity 1 -> 5%
    # rarity

    # only run commands
    if message.author == bot.user:
        return
    try:
        if message.content[0] != config["prefix"]:
            return
    except Exception:
        return
    
    try:
        args = shlex.split(message.content)
    except Exception:
        print('someone is obese')
        return
    
    command = args[0][1:]
    del args[0]

    # !gamestart cards
    if command == "create":
        player = Player(message.author.id, message.author.name)
        players.append(player)
        await message.channel.send("Welcome to the jungle, " + message.author.name)

    if command == "help":
        pass

    if command == "list":
        embed=discord.Embed(title="Your Cards", description="These are your cards")
        await message.channel.send(embed=embed)
        
        

with open("auth.json") as f:
    auth = json.load(f)
    bot.run(auth["token"])
    f.close()