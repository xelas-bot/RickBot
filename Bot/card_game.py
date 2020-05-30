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
with open("card_config.json", encoding='utf-8') as f:
    global card_config
    card_config = json.load(f)
    f.close()

# card data
with open("data/cards.json", encoding='utf-8') as f:
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

def update_players():
    players = {}
    for x in db_players.find():
        player = Player(id=x["_id"], username=x["username"], currency=x["currency"], cards=x["cards"])
        players[x["_id"]] = player
    return players

# Mongo Database
db = cluster["game"]
db_players = db["players"]

# Auth bot
bot = discord.Client()
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    print('Bot is running')

def check_rarity(card):
    with open('data/card_rarity.json') as f:
        card_rarity = json.load(f)
        f.close()
        for x in card_rarity:
            if card in card_rarity[x]:
                return x
        print("Update rarities dummy")
    return "Error"

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
    players = update_players()
    
    # only commands
    try:
        if message.content[0] != config["prefix"]:
            random.seed(a=None)
            x = random.random()
            if x < card_config["Drop_Rate"] and message.author.id in players:
                random.seed(a=message.id)
                spawn = random.random()
                drop = ''
                if spawn >= card_config["EX"]["drop"]:
                    drop = players[message.author.id].spawn("EX")
                elif spawn >= card_config["Legendary"]["drop"]:
                    drop = players[message.author.id].spawn("Legendary")
                elif spawn >= card_config["Epic"]["drop"]:
                    drop = players[message.author.id].spawn("Epic")
                elif spawn >= card_config["Rare"]["drop"]:
                    drop = players[message.author.id].spawn("Rare")
                elif spawn >= card_config["Uncommon"]["drop"]:
                    drop = players[message.author.id].spawn("Uncommon")
                else:
                    drop = players[message.author.id].spawn("Common")
                
                embed = discord.Embed(title=cards[drop]["name"],description="*" + cards[drop]["desc"] + "*", color=card_config[cards[drop]["rarity"]]["color"])
                if message.channel.guild.icon_url == None:
                    embed.set_author(name="You caught a:", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                else:
                    embed.set_author(name="You caught a:", icon_url=message.channel.guild.icon_url)
                embed.set_thumbnail(url=message.author.avatar_url)
                embed.set_image(url=cards[drop]["image"])

                await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
            return
    except Exception:
        return
    
    try:
        args = shlex.split(message.content)
    except Exception:
        await message.channel.send("Some quotes are broken...")
        print('shrey is obese and ate the command')
        return
    
    command = args[0][1:]
    del args[0]

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
        embed = discord.Embed(description=msg, color=4605510)
        embed.set_author(name="Help", icon_url="https://img.icons8.com/carbon-copy/2x/question-mark.png")
        await message.channel.send(embed=embed)

    if command == "update_rarities":
        rarities = {
            "Common"   : [],
            "Uncommon" : [],
            "Rare"     : [],
            "Epic"     : [],
            "Legendary": [],
            "EX"       : []
        }
        for x in cards:
            rarities[cards[str(x)]["rarity"]].append(str(x))
        
        with open("data/card_rarity.json", "w") as f:
            json.dump(rarities, f, ensure_ascii=False)
            f.close()
        
        await message.channel.send('Rarities have been updated!')

    if command == "tradeup":
        if message.author.id in players:
            if len(args) < 10:
                await message.channel.send("Select 10 cards of the same quality to trade up! Use + [" + config["prefix"] + "tradeup id1 id2 ... id10]")
            else:
                player_cards = players[message.author.id].cards
                same_rarity = True
                rarity = ''
                
                try:
                    rarity = check_rarity(player_cards[int(args[0]) - 1])
                    print(rarity)
                    for x in args[1:10]:
                        if check_rarity(player_cards[int(x) - 1]) != rarity:
                            print(player_cards[int(x) - 1])
                            print(check_rarity(player_cards[int(x) - 1]))
                            same_rarity = False
                except Exception:
                    await message.channel.send("Select 10 cards of the same quality to trade up! Use + [" + config["prefix"] + "tradeup id1 id2 ... id10]")
                
                if same_rarity:
                    if rarity == "EX":
                        await message.channel.send("You cannot tradeup EX cards!")
                    else:
                        desc = ''
                        for x in args[:10]:
                            desc += cards[player_cards[int(x) - 1]]["name"] + '\n'
                        embed=discord.Embed(title="You are trading up 10 " + rarity + "s", description=desc)
                        embed.set_footer(text="Type *" + config["prefix"] + "tradeup_confirm* to tradeup!")
                        await message.channel.send(embed=embed)
                        user = message.author
                        def check_tradeup(message):
                            return message.author == user and "!tradeup" in message.content
                        try:
                            response = await bot.wait_for('message',timeout=30.0,check=check_tradeup)
                            if response.content == "!tradeup_confirm":
                                players = update_players()
                                players[user.id].delete(args[:10])
                                if rarity == "Common":
                                    drop = players[user.id].spawn("Uncommon")
                                elif rarity == "Uncommon":
                                    drop = players[user.id].spawn("Rare")
                                elif rarity == "Rare":
                                    drop = players[user.id].spawn("Epic")
                                elif rarity == "Epic":
                                    drop = players[user.id].spawn("Legendary")
                                elif rarity == "Legendary":
                                    drop = players[user.id].spawn("EX")
                                embed = discord.Embed(title=cards[drop]["name"],description="*" + cards[drop]["desc"] + "*", color=card_config[cards[drop]["rarity"]]["color"])
                                if message.channel.guild.icon_url == None:
                                    embed.set_author(name="You traded up to a:", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                                else:
                                    embed.set_author(name="You traded up to a:", icon_url=message.channel.guild.icon_url)
                                embed.set_thumbnail(url=message.author.avatar_url)
                                embed.set_image(url=cards[drop]["image"])
                                await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
                            else:
                                await message.channel.send("Do only one tradeup at a time! First tradeup is cancelled.")
                        except Exception:
                            await message.channel.send("Tradeup cancelled!")
                else:
                    await message.channel.send("The cards must be of the same quality!")
        else:
            await message.channel.send(config["join_msg"].replace("%", config["prefix"]))

    if command == "reroll":
        if message.author.id in players:
            if len(args) < 3:
                await message.channel.send("Select 3 cards of the same quality to reroll! Use [" + config["prefix"] + "reroll id1 id2 id3]")
            else:
                player_cards = players[message.author.id].cards
                same_rarity = True
                rarity = ''
                try:
                    rarity = check_rarity(player_cards[int(args[0]) - 1])
                    print(rarity)
                    for x in args[1:3]:
                        if check_rarity(player_cards[int(x) - 1]) != rarity:
                            print(player_cards[int(x) - 1])
                            print(check_rarity(player_cards[int(x) - 1]))
                            same_rarity = False
                except Exception:
                    await message.channel.send("Select 3 cards of the same quality to reroll! Use [" + config["prefix"] + "reroll id1 id2 id3]")
                
                if same_rarity:
                    desc = ''
                    for x in args[:3]:
                        desc += cards[player_cards[int(x) - 1]]["name"] + '\n'
                    embed=discord.Embed(title="You are rerolling 3 " + rarity + "s", description=desc)
                    embed.set_footer(text="Type *" + config["prefix"] + "reroll_confirm* to tradeup!")
                    await message.channel.send(embed=embed)
                    user = message.author
                    def check_reroll(message):
                        return message.author == user and "!reroll" in message.content
                    try:
                        response = await bot.wait_for('message',timeout=30.0,check=check_reroll)
                        if response.content == "!reroll_confirm":
                            players = update_players()
                            players[user.id].delete(args[:3])
                            if rarity == "Common":
                                drop = players[user.id].spawn("Common")
                            elif rarity == "Uncommon":
                                drop = players[user.id].spawn("Uncommon")
                            elif rarity == "Rare":
                                drop = players[user.id].spawn("Rare")
                            elif rarity == "Epic":
                                drop = players[user.id].spawn("Epic")
                            elif rarity == "Legendary":
                                drop = players[user.id].spawn("Legendary")
                            elif rarity == "EX":
                                drop = players[user.id].spawn("EX")
                            embed = discord.Embed(title=cards[drop]["name"],description="*" + cards[drop]["desc"] + "*", color=card_config[cards[drop]["rarity"]]["color"])
                            if message.channel.guild.icon_url == None:
                                embed.set_author(name="You rerolled a:", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                            else:
                                embed.set_author(name="You rerolled a:", icon_url=message.channel.guild.icon_url)
                            embed.set_thumbnail(url=message.author.avatar_url)
                            embed.set_image(url=cards[drop]["image"])
                            await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
                        else:
                            await message.channel.send("Do only one reroll at a time! First reroll is cancelled.")
                    except Exception:
                        await message.channel.send("Reroll cancelled!")
                else:
                    await message.channel.send("The cards must be of the same quality!")
        else:
            await message.channel.send(config["join_msg"].replace("%", config["prefix"]))

    if command == "bal":
        if message.author.id in players:
            embed = discord.Embed(description="Your current balance is: " + str(players[message.author.id].currency), color=4605510)
            embed.set_author(name="Money", icon_url="https://w0.pngwave.com/png/944/747/coins-png-clip-art.png")
            await message.channel.send(embed=embed)
        else:
            await message.channel.send(config["join_msg"].replace("%", config["prefix"]))

    
            
    if command == "list":
        if message.author.id in players:
            if len(args) >= 1:
                try:
                    other = bot.get_user(int(args[0][3:-1]))
                    page = 0
                    page_len = config["page_len"]
                    while True:
                        players = update_players()
                        card_collection = players[other.id].cards
                        total = len(card_collection)
                        desc = ''
                        for i, x in enumerate(card_collection[page * page_len: page * page_len + page_len]):
                            desc += '**' + cards[str(x)]["name"] + '** | ' + cards[str(x)]["rarity"] + " | " + str(i + 1 + page * page_len) + '/' + str(total) + '\n'
                        embed=discord.Embed(title="Their Cards", description=desc)
                        embed.set_footer(text="You are on page " + str(page + 1) + "/" + str(total // page_len + 1) + ". Use *!back* and *!next* to scroll through the list!")
                        embed.set_author(name=other.name, icon_url=other.avatar_url)
                        await message.channel.send(embed=embed)
                        user = message.author
                        def check_list(message):
                            return message.author == user and (message.content == "!back" or message.content == "!next")
                        try:
                            response = await bot.wait_for("message",timeout = 60.0, check=check_list)
                            if response.content == "!back":
                                if page <= 0:
                                    return
                                else:
                                    page -= 1
                            if response.content == "!next":
                                if page * page_len + page_len > total:
                                    return
                                else:
                                    page += 1
                        except Exception:
                            return
                except Exception:
                    page = 0
                    page_len = config["page_len"]

                    while True:
                        players = update_players()
                        card_collection = players[message.author.id].cards
                        total = len(card_collection)
                        desc = ''
                        for i, x in enumerate(card_collection[page * page_len: page * page_len + page_len]):
                            desc += '**' + cards[str(x)]["name"] + '** | ' + cards[str(x)]["rarity"] + " | " + str(i + 1 + page * page_len) + '/' + str(total) + '\n'
                        embed=discord.Embed(title="Your Cards", description=desc)
                        embed.set_footer(text="You are on page " + str(page + 1) + "/" + str(total // page_len + 1) + ". Use *!back* and *!next* to scroll through the list!")
                        embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                        await message.channel.send(embed=embed)
                        user = message.author
                        def check_list(message):
                            return message.author == user and (message.content == "!back" or message.content == "!next")
                        try:
                            response = await bot.wait_for("message",timeout = 60.0, check=check_list)
                            if response.content == "!back":
                                if page <= 0:
                                    return
                                else:
                                    page -= 1
                            if response.content == "!next":
                                if page * page_len + page_len > total:
                                    return
                                else:
                                    page += 1
                        except Exception:
                            return
            else:
                page = 0
                page_len = config["page_len"]

                while True:
                    players = update_players()
                    card_collection = players[message.author.id].cards
                    total = len(card_collection)
                    desc = ''
                    for i, x in enumerate(card_collection[page * page_len: page * page_len + page_len]):
                        desc += '**' + cards[str(x)]["name"] + '** | ' + cards[str(x)]["rarity"] + " | " + str(i + 1 + page * page_len) + '/' + str(total) + '\n'
                    embed=discord.Embed(title="Your Cards", description=desc)
                    embed.set_footer(text="You are on page " + str(page + 1) + "/" + str(total // page_len + 1) + ". Use *!back* and *!next* to scroll through the list!")
                    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                    await message.channel.send(embed=embed)
                    user = message.author
                    def check_list(message):
                        return message.author == user and (message.content == "!back" or message.content == "!next")
                    try:
                        response = await bot.wait_for("message",timeout = 60.0, check=check_list)
                        if response.content == "!back":
                            if page <= 0:
                                return
                            else:
                                page -= 1
                        if response.content == "!next":
                            if page * page_len + page_len > total:
                                return
                            else:
                                page += 1
                    except Exception:
                        return
        else:
            await message.channel.send(config["join_msg"].replace("%", config["prefix"]))

    if command == "show":
        if message.author.id in players:
            try:
                x = int(args[0]) - 1
                if x >= 0 and x < len(players[message.author.id].cards):
                    card_id = players[message.author.id].cards[x]

                    embed = discord.Embed(title=cards[card_id]["name"],description="*" + cards[card_id]["desc"] + "*", color=card_config[cards[card_id]["rarity"]]["color"])
                    if message.channel.guild.icon_url == None:
                        embed.set_author(name="Your Card:", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                    else:
                        embed.set_author(name="Your Card:", icon_url=message.channel.guild.icon_url)
                    embed.set_thumbnail(url=message.author.avatar_url)
                    embed.set_image(url=cards[card_id]["image"])
                    embed.add_field(name="Rarity", value=cards[card_id]["rarity"], inline=True)

                    for x in cards[card_id]:
                        if not x in ["name", "desc", "image", "rarity"]:
                            if len(str(x)) == 1:
                                embed.add_field(name=str(x), value=str(cards[card_id][x]), inline=True)
                            else:
                                name = str(x)[0].upper() + str(x)[1:]
                                embed.add_field(name=name, value=str(cards[card_id][x]), inline=True)
                    await message.channel.send(embed=embed)
                else:
                    await message.channel.send("Enter a valid id (1-" + str(len(players[message.author.id].cards)) + ")")
            except Exception:
                await message.channel.send("Enter a valid id (1-" + str(len(players[message.author.id].cards)) + ")")
        else:
            await message.channel.send(config["join_msg"].replace("%", config["prefix"]))
    
    if command == 'drop':
        if message.author.id in config["administrators"]:
            drop = 0
            if len(args) == 1:
                try:
                    players[message.author.id].give(args[0])
                    drop = str(args[0])
                except Exception:
                    print("Something went wrong")
            else:
                roll = random.randrange(1,6)
                if(roll == 1):
                    drop = players[message.author.id].spawn("Common")
                elif(roll == 2):
                    drop = players[message.author.id].spawn("Uncommon")
                elif(roll == 3):
                    drop = players[message.author.id].spawn("Rare")
                elif(roll == 4):
                    drop = players[message.author.id].spawn("Epic")
                elif(roll == 5):
                    drop = players[message.author.id].spawn("Legendary")
                else:
                    drop = players[message.author.id].spawn("Ex")
            embed = discord.Embed(title=cards[drop]["name"],description="*" + cards[drop]["desc"] + "*", color=card_config[cards[drop]["rarity"]]["color"])
            if message.channel.guild.icon_url == None:
                embed.set_author(name="You caught a:", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
            else:
                embed.set_author(name="You caught a:", icon_url=message.channel.guild.icon_url)
            embed.set_thumbnail(url=message.author.avatar_url)
            embed.set_image(url=cards[drop]["image"])

            await message.channel.send("<@" + str(message.author.id) + ">", embed=embed)


with open("auth.json") as f:
    auth = json.load(f)
    bot.run(auth["token"])
    f.close()