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


# Mongo auth
with open("auth.json") as f:
    auth = json.load(f)
    global cluster
    cluster = MongoClient(auth["mongo_key"])
    f.close()

# card config
with open("card_config.json") as f:
    global card_config
    card_config = json.load(f)
    f.close()

# card data
with open("data/cards.json") as f:
    global cards
    cards = json.load(f)
    f.close()

# help
with open("help.json") as f:
    global help_msgs
    help_msgs = json.load(f)
    f.close()

# config options
with open('config.json') as f:
    global config
    config = json.load(f)
    f.close()


# Mongo Database
db = cluster["game"]
db_players = db["players"]

# Auth bot
bot = discord.Client()
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    print('Bot is running')

# bot message
@bot.event
async def on_message(message):
    # ignore bot
    if message.author == bot.user:
        return

    # spawn a card
    # rarity 1 -> 0.038075
    # rarity 2 -> 0.011925
    # rarity 3 -> 0.003075
    # rarity 4 -> 0.000675
    # rarity 5 -> 0.000075

    # Load players
    players = {}
    for x in db_players.find():
        player = Player(x["_id"], x["username"], x["currency"], x["cards"])
        players[x["_id"]] = player
    
    # only commands
    try:
        if message.content[0] != config["prefix"]:
            x = random.random()
            if x < card_config["Common"]["drop"] and message.author.id in players:
                spawn = random.random()
                drop = ''
                if spawn >= card_config["Legendary"]["drop"]:
                    drop = players[message.author.id].spawn("Legendary")
                elif spawn >= card_config["Epic"]["drop"]:
                    drop = players[message.author.id].spawn("Epic")
                elif spawn >= card_config["Rare"]["drop"]:
                    drop = players[message.author.id].spawn("Rare")
                elif spawn >= card_config["Uncommon"]["drop"]:
                    drop = players[message.author.id].spawn("Uncommon")
                else:
                    drop = players[message.author.id].spawn("Common")
                await message.channel.send('You got a ' + drop + '!!!')
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
        if message.author.id in players:
            await message.channel.send("You are already in the jungle you bum!")
        else:
            player = Player(message.author.id, message.author.name)
            player.create_player()
            players[message.author.id] = player
            await message.channel.send("Welcome to the jungle, **" + message.author.name + ("**"))

    if command == "help":
        msg = ''
        for x in help_msgs:
           msg += '\n' + config['prefix'] + x + ': ' + help_msgs[x]
        await message.channel.send(msg)

    if command == "update_rarities":
        rarities = {
            "Common"   : [],
            "Uncommon" : [],
            "Rare"     : [],
            "Epic"     : [],
            "Legendary": []
        }
        for x in cards:
            rarities[cards[str(x)]["rarity"]].append(str(x))
        
        with open("data/card_rarity.json", "w") as f:
            json.dump(rarities, f)
            f.close()
        
        await message.channel.send('Rarities have been updated!')

    if command == "list":
        ## Finding Player Owned Cards
        tempID = message.author.id
        myquery = { "_id": tempID }
        tempDic = db_players.find_one(myquery)
        print(tempDic)
        card_collection = tempDic["cards"]
        
        total = len(card_collection)
        desc = ''
        for i, x in enumerate(card_collection):
            desc += '**' + cards[str(x)]["name"] + '** | ' + cards[str(x)]["rarity"] + " | " + str(i + 1) + '/' + str(total) + '\n'

        embed=discord.Embed(title="Your Cards", description=desc)
        await message.channel.send(embed=embed)

    if command == "show":
        try:
            x = int(args[0]) - 1
            myquery = { "_id": message.author.id }
            tempDic = db_players.find_one(myquery)
            card_collection = tempDic["cards"]
            card_id = card_collection[x]
            
            embed = discord.Embed(description="He WILL fuck your bitch", color=card_config[cards[card_id]["rarity"]]["color"])
            embed.set_author(name="ZeKenneth", icon_url="https://cdn.discordapp.com/icons/674470460200845335/feefeef9d25bd8043f7afee10c7877f3.png?size=256")
            embed.set_thumbnail(url=message.author.avatar_url)   
            embed.set_image(url="https://i.imgur.com/iZBbjem.jpg")
            embed.add_field(name="Weight", value="0", inline=True)
            embed.add_field(name="Power", value="0", inline=True)
            embed.add_field(name="Sex Appeal", value="4", inline=True)
            embed.add_field(name="Negro", value="True", inline=True)
            embed.add_field(name="Lethal", value="False", inline=True)
            embed.add_field(name="DLZ", value="1000", inline=True)

            await message.channel.send("Your Card:")
            await message.channel.send(embed=embed)
        except Exception:
            await message.channel.send('Use [' + config['prefix'] + 'show id] to show a card!')
        
        
        
        
        
        
    
        
        


        
        

with open("auth.json") as f:
    auth = json.load(f)
    bot.run(auth["token"])
    f.close()