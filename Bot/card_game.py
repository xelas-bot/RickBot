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
import numpy
from pymongo import MongoClient
from res.Player import Player
import schedule
from bot import generate_ethereum_wallet

from datetime import datetime
import time

# Mongo auth
with open("auth.json") as f:
    auth = json.load(f)
    global cluster
    cluster = MongoClient(auth["mongo_key"])
    f.close()


# Mongo Database
db = cluster["game"]
db_players = db["players"]
db_market = db["market"]


def update_db_players():
    for x in db_players.find():
        player = Player(id=x["_id"], username=x["username"], currency=x["currency"], cards=x["cards"], last_time=x["last_time"])
        player.set_db()

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

#302515756976046081

# crates
with open('data/crates.json') as f:
    global crates
    crates = json.load(f)
    f.close()

# rarities
with open("data/card_rarity.json") as f:
    global card_rarity
    card_rarity = json.load(f)
    f.close()

# collections
with open("card_collections.json") as f:
    global collections_config
    collections_config = json.load(f)
    f.close()


def update_things():
    with open("data/cards.json", encoding='utf-8') as f:
        global cards
        cards = json.load(f)
        f.close()
    with open("card_config.json", encoding='utf-8') as f:
        global card_config
        card_config = json.load(f)
        f.close()
    with open("help.json") as f:
        global help_msgs
        help_msgs = json.load(f)
        f.close()
    with open('config.json') as f:
        global config
        config = json.load(f)
        f.close()
    with open("data/card_rarity.json") as f:
        global card_rarity
        card_rarity = json.load(f)
        f.close()


def update_players():
    players = {}
    for x in db_players.find():
        player = Player(id=x["_id"], username=x["username"], currency=x["currency"], cards=x["cards"], crates=x["crates"], keys=x["keys"], last_time=x["last_time"])
        players[x["_id"]] = player
    return players

##Market Commands
def update_market():
    market = []
    for x in db_market.find():
        listing = {"user_id": x["user_id"], "card_price": x["card_price"], "card_id": x["card_id"], "type": x["type"]}
        market.append(listing)
    return market

def create_listing(user_id, card_price, card_id):
    listing = {"user_id": user_id, "card_price": card_price, "card_id": card_id, "type": "card"}
    db_market.insert_one(listing)

def remove_listing(listing_id, verify):
    market = update_market()
    query = market[int(listing_id) - 1]
    if query == verify:
        db_market.delete_one(query)
        return True
    else:
        return False

def get_random_rarity(rarity, exclude=[]):
    drops = [x for x in card_rarity[rarity] if not x in exclude]
    if len(drops) <= 0:
        drops = card_rarity[rarity]
    drop = random.choice(drops)
    return drop

async def show_card(message, card_id, title, show_desc=True, footer=None, mention=False):
    embed = discord.Embed(title=cards[card_id]["name"],description="*" + cards[card_id]["desc"] + "*", color=card_config[cards[card_id]["rarity"]]["color"])
    if message.channel.guild.icon_url == None:
        embed.set_author(name=title, icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
    else:
        embed.set_author(name=title, icon_url=message.channel.guild.icon_url)
    embed.set_thumbnail(url=message.author.avatar_url)
    embed.set_image(url=cards[card_id]["image"])

    if show_desc:
        embed.add_field(name="Rarity", value=cards[card_id]["rarity"], inline=True)
        for x in cards[card_id]:
            if not x in ["name", "desc", "image", "rarity"]:
                if len(str(x)) == 1:
                    embed.add_field(name=str(x), value=str(cards[card_id][x]), inline=True)
                else:
                    name = str(x)[0].upper() + str(x)[1:]
                    embed.add_field(name=name, value=str(cards[card_id][x]), inline=True)
    
    if footer != None:
        embed.set_footer(text=footer)

    if mention:
        await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
    else:
        await message.channel.send(embed=embed)

# Auth bot
bot = discord.Client()
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    print('Bot is running')

def check_rarity(card):
    with open('./Bot/data/card_rarity.json') as f:
        card_rarity = json.load(f)
        f.close()
        for x in card_rarity:
            if card in card_rarity[x]:
                return x
        print("Update rarities dummy")
    return "Error"


with open('data/market_bot.json') as f:
    global market_bot
    market_bot = json.load(f)
    f.close()


def create_market_listing():
    total = 0
    for x in market_bot:
        total += x["weight"]
    
    weights = []
    for x in market_bot:
        weights.append(x["weight"] / total)

    choice = numpy.random.choice(market_bot, 1, p=weights)[0]
    price = random.randrange(choice["price_lower"], choice["price_upper"])
    listing = {"user_id": -1, "card_price": price, "card_id": choice["card_id"], "type": choice["type"]}
    db_market.insert_one(listing)
    if choice["type"] == "card":
        print("Market added a " + cards[choice["card_id"]]["name"] + " to the market!")
    else:
        print("Market added a " + crates["crates"][choice["card_id"]]["name"] + " to the market!")

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

    #update market
    schedule.run_pending()

    if random.random() <= card_config["Market_Drop"]:
        create_market_listing()
    
    # only commands
    try:
        if message.content[0] != config["prefix"] and message.author.id in players:
            x = random.random()
            if(card_config['event']):
                x = x / 2
            if x < card_config["Drop_Rate"]:
                choice_drop = random.random()
                if choice_drop < card_config["Coin_Rate"]:
                    spawn = random.random()
                    drop = 0
                    if spawn >= card_config["EX"]["drop"]:
                        drop = players[message.author.id].reward("EX")
                    elif spawn >= card_config["Legendary"]["drop"]:
                        drop = players[message.author.id].reward("Legendary")
                    elif spawn >= card_config["Epic"]["drop"]:
                        drop = players[message.author.id].reward("Epic")
                    elif spawn >= card_config["Rare"]["drop"]:
                        drop = players[message.author.id].reward("Rare")
                    elif spawn >= card_config["Uncommon"]["drop"]:
                        drop = players[message.author.id].reward("Uncommon")
                    else:
                        drop = players[message.author.id].reward("Common")
                    embed = discord.Embed(description=message.author.name + " got " + str(drop) + " cash monies", color=config["embed_color"])
                    embed.set_author(name="Cash Monies", icon_url="https://w0.pngwave.com/png/944/747/coins-png-clip-art.png")
                    await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
                elif choice_drop < card_config["Special_Rate"]:
                    special_drop = random.random()
                    if special_drop < card_config["Special_Drop"]["Key"]:
                        drops = [str(x + 1) for x in range(len(crates["keys"]["weights"]))]
                        drop = numpy.random.choice(drops, 1, p=crates["keys"]["weights"])[0]
                        players[message.author.id].give_key(drop)
                        embed = discord.Embed(description=message.author.name + " got a " + crates["keys"][drop]["name"] + " worth $" + str(crates["keys"][drop]["price"]), color=config["embed_color"])
                        embed.set_author(name="Crates", icon_url="https://i.imgur.com/ZVQTsnh.png")
                        await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
                        print(message.author.name + " got a " + crates["keys"][drop]["name"] + " worth $" + str(crates["keys"][drop]["price"]))
                    else:
                        drops = [str(x + 1) for x in range(len(crates["crates"]["weights"]))]
                        sum_probs = sum(crates["crates"]["weights"])
                        probs = [x / sum_probs for x in crates["crates"]["weights"]]
                        drop = numpy.random.choice(drops, 1, p=probs)[0]
                        players[message.author.id].give_crate(drop)
                        embed = discord.Embed(description=message.author.name + " got a " + crates["crates"][drop]["name"], color=config["embed_color"])
                        embed.set_author(name="Crates", icon_url="https://i.imgur.com/ZVQTsnh.png")
                        await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
                        print(message.author.name + " got a " + crates["crates"][drop]["name"])
                else:
                    spawn = random.random()
                    drop = ''
                    if spawn >= card_config["EX"]["drop"]:
                        drop = players[message.author.id].spawn("EX", currency=True)
                    elif spawn >= card_config["Legendary"]["drop"]:
                        drop = players[message.author.id].spawn("Legendary", currency=True)
                    elif spawn >= card_config["Epic"]["drop"]:
                        drop = players[message.author.id].spawn("Epic", currency=True)
                    elif spawn >= card_config["Rare"]["drop"]:
                        drop = players[message.author.id].spawn("Rare", currency=True)
                    elif spawn >= card_config["Uncommon"]["drop"]:
                        drop = players[message.author.id].spawn("Uncommon", currency=True)
                    else:
                        drop = players[message.author.id].spawn("Common", currency=True)
                    await show_card(message, drop, message.author.name + " caught a:", False, None, True)
                
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
    # print(command)
    # print(args)
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
        embed = discord.Embed(description=msg, color=config["embed_color"])
        embed.set_author(name="Help", icon_url="https://img.icons8.com/carbon-copy/2x/question-mark.png")
        await message.channel.send(embed=embed)
    if command == "claimETH":
        playerid = message.author.id
        private_key, public_key = generate_ethereum_wallet()

        myquery = { "_id": playerid }
        newvalues = { "$set": { "private_key": private_key } }
        db_players.update_one(myquery,newvalues)

        embed=discord.Embed(title="Ethereum Wallet Generator", url="https://metamask.io/", description="Visit https://metamask.io/ to check your wallets balance or visit the blockchain to check its balance! Your private key has been DMed to you.", color=0x09bad2)
        embed.add_field(name="Public Wallet Address", value=public_key, inline=False)
        embed.add_field(name="Balance", value="0 - 0.00001 ETH in wallet", inline=True)
        await message.author.send(mention_author=True,content= "Your private key (DO NOT SHARE) is " + str(private_key))
        await message.channel.send(embed=embed)

    if command == "update":
        update_things()
        rarities = {
            "Common"   : [],
            "Uncommon" : [],
            "Rare"     : [],
            "Epic"     : [],
            "Legendary": [],
            "EX"       : [],
            "Special"  : []
        }
        for x in cards:
            rarities[cards[str(x)]["rarity"]].append(str(x))
        
        with open("./Bot/data/card_rarity.json", "w") as f:
            json.dump(rarities, f, ensure_ascii=False)
            f.close()
        
        Player.update_rarities()

        market_drops = []
        weights = {}
        for x in card_config:
            if x in ["Common", "Uncommon", "Rare", "Epic", "Legendary", "EX", "Special"]:
                weights[x] = card_config[x]["weight"]

        for x in cards:
            rarity = cards[x]["rarity"]
            weight = weights[rarity]
            market_drops.append(
                {"card_id": x , "price_lower": card_config[rarity]["currency"] * (1 - card_config["Card_Dev"]), "price_upper": card_config[rarity]["currency"] * (1 + card_config["Card_Dev"]), "weight": weight, "type": "card"}
                )
        for x in crates["crates"]:
            if x != "weights":
                market_drops.append(
                    {"card_id": x, "price_lower": crates["crates"][x]["price"] * (1 - card_config["Card_Dev"]), "price_upper": crates["crates"][x]["price"] * (1 + card_config["Card_Dev"]), "weight": crates["crates"]["weights"][int(x) - 1], "type": "crate"}
                )

        with open("./Bot/data/market_bot.json", "w") as f:
            json.dump(market_drops, f, ensure_ascii=False)
            f.close()

        await message.channel.send('Cards have been updated!')

    if command == "tradeup":
        if message.author.id in players:
            if len(args) < 10:
                await message.channel.send("Select 10 cards of the same quality to trade up! Use `" + config["prefix"] + "tradeup <id1> <id2> ... <id10>`")
            else:
                player_cards = players[message.author.id].cards
                same_rarity = True
                rarity = ''
                
                try:
                    rarity = check_rarity(player_cards[int(args[0]) - 1])
                    card_types = []
                    card_ids = []
                    for x in args[:10]:
                        if x in card_ids:
                            await message.channel.send("Cannot select the same id to tradeup!")
                            return False
                        if check_rarity(player_cards[int(x) - 1]) != rarity:
                            same_rarity = False
                        card_types.append(player_cards[int(x) - 1])
                        card_ids.append(x)
                except Exception:
                    await message.channel.send("Select 10 cards of the same quality to trade up! Use `" + config["prefix"] + "tradeup <id1> <id2> ... <id10>`")
                
                if same_rarity:
                    if rarity == "EX":
                        await message.channel.send("You cannot tradeup EX cards!")
                    else:
                        desc = ''
                        for x in args[:10]:
                            desc += cards[player_cards[int(x) - 1]]["name"] + '\n'
                        embed=discord.Embed(title="You are trading up 10 " + rarity + "s", description=desc)
                        embed.set_footer(text="Type `" + config["prefix"] + "tradeup_confirm` to tradeup!")
                        await message.channel.send(embed=embed)
                        user = message.author
                        def check_tradeup(message):
                            return message.author == user and "!tradeup" in message.content
                        try:
                            response = await bot.wait_for('message',timeout=30.0,check=check_tradeup)
                            if response.content == "!tradeup_confirm":
                                players = update_players()
                                if not players[user.id].compare(args[:10], card_types):
                                    await message.send("A Card is missing from your collection!")
                                    return
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
                                
                                await show_card(message, drop, message.author.name + " traded up to a:", False, None, True)
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
                await message.channel.send("Select 3 cards of the same quality to reroll! Use `" + config["prefix"] + "reroll <id1> <id2> <id3>`")
            else:
                player_cards = players[message.author.id].cards
                same_rarity = True
                rarity = ''
                card_types = []
                try:
                    rarity = check_rarity(player_cards[int(args[0]) - 1])
                    card_ids = []
                    for x in args[:3]:
                        if x in card_ids:
                            await message.channel.send("Cannot select the same id to reroll!")
                        if check_rarity(player_cards[int(x) - 1]) != rarity:
                            same_rarity = False
                        card_types.append(player_cards[int(x) - 1])
                        card_ids.append(x)
                except Exception:
                   await message.channel.send("Select 3 cards of the same quality to reroll! Use `" + config["prefix"] + "reroll <id1> <id2> <id3>`")
                if same_rarity:
                    desc = ''
                    for x in args[:3]:
                        desc += cards[player_cards[int(x) - 1]]["name"] + '\n'
                    embed=discord.Embed(title="You are rerolling 3 " + rarity + "s", description=desc)
                    embed.set_footer(text="Type `" + config["prefix"] + "reroll_confirm` to tradeup!")
                    await message.channel.send(embed=embed)
                    user = message.author
                    def check_reroll(message):
                        return message.author == user and "!reroll" in message.content
                    try:
                        response = await bot.wait_for('message',timeout=30.0,check=check_reroll)
                        if response.content == "!reroll_confirm":
                            players = update_players()
                            if not players[user.id].compare(args[:3], card_types):
                                await message.channel.send("A Card is missing from your collection!")
                                return
                            players[user.id].delete(args[:3])
                            if rarity == "Common":
                                drop = players[user.id].spawn("Common", exclude=card_types)
                            elif rarity == "Uncommon":
                                drop = players[user.id].spawn("Uncommon", exclude=card_types)
                            elif rarity == "Rare":
                                drop = players[user.id].spawn("Rare", exclude=card_types)
                            elif rarity == "Epic":
                                drop = players[user.id].spawn("Epic", exclude=card_types)
                            elif rarity == "Legendary":
                                drop = players[user.id].spawn("Legendary", exclude=card_types)
                            elif rarity == "EX":
                                drop = players[user.id].spawn("EX", exclude=card_types)
                            print(drop)
                            await show_card(message, drop, message.author.name + " rerolled a:", False, None, True)
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
            embed = discord.Embed(description="Your current balance is: " + str(players[message.author.id].currency), color=config["embed_color"])
            embed.set_author(name="Cash Monies", icon_url="https://w0.pngwave.com/png/944/747/coins-png-clip-art.png")
            await message.channel.send("<@" + str(message.author.id) + ">", embed=embed)
        else:
            await message.channel.send(config["join_msg"].replace("%", config["prefix"]))
    
    if command == "list":
        if message.author.id in players:
            if len(args) >= 1:
                if args[0].lower() in ["common", "uncommon", "rare", "epic", "legendary", "ex", "commons", "uncommons", "rares", "epics", "legendaries", "exs"]:
                    page = 0
                    page_len = config["page_len"]
                    rarity = "Common"
                    if args[0].lower() in ["commons", "uncommons", "rares", "epics"]:
                        rarity = args[0][0].upper() + args[0][1:-1].lower()
                    elif args[0].lower() == "legendaries":
                        rarity = "Legendary"
                    elif args[0].lower() == "exs":
                        rarity = "EX"
                    elif args[0].lower() == "ex":
                        rarity = "EX"
                    else:
                        rarity = args[0][0].upper() + args[0][1:].lower()
                    while True:
                        players = update_players()
                        card_collection = players[message.author.id].get_rarities(rarity)
                        total = len(card_collection)
                        total_cards = players[message.author.id].get_card_len()
                        desc = ''
                        embed = None
                        if total == 0:
                            desc = 'You have no cards! Go out and get some!'
                        else:
                            for i, x in card_collection[page * page_len: page * page_len + page_len]:
                                desc += '**' + cards[str(x)]["name"] + '**\t|\t' + cards[str(x)]["rarity"] + "\t|\t" + str(i + 1 + page * page_len) + '/' + str(total_cards) + '\n'
                        if rarity == "Legendary":
                            embed=discord.Embed(title="Your Cards (Legendaries)", description=desc)
                        else:
                            embed=discord.Embed(title="Your Cards (" + rarity + "s)", description=desc)
                        if total > 0:
                            embed.set_footer(text="You are on page " + str(page + 1) + "/" + str((total - 1) // page_len + 1) + ". Use `!back` and `!next` to scroll through the list!")
                        embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                        await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
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
                                if page * page_len + page_len > total - 1:
                                    return
                                else:
                                    page += 1
                        except Exception:
                            return
                try:
                    other = bot.get_user(int(args[0][3:-1]))
                    page = 0
                    page_len = config["page_len"]
                    while True:
                        players = update_players()
                        card_collection = players[other.id].cards
                        total = len(card_collection)
                        desc = ''
                        if total == 0:
                            desc = 'You have no cards! Go out and get some!'
                        else:
                            for i, x in enumerate(card_collection[page * page_len: page * page_len + page_len]):
                                desc += '**' + cards[str(x)]["name"] + '**\t|\t' + cards[str(x)]["rarity"] + "\t|\t" + str(i + 1 + page * page_len) + '/' + str(total) + '\n'
                        embed=discord.Embed(title=other.name + "'s Cards", description=desc)
                        if total > 0:
                            embed.set_footer(text="You are on page " + str(page + 1) + "/" + str((total - 1) // page_len + 1) + ". Use `!back` and `!next` to scroll through the list!")
                        embed.set_author(name=other.name, icon_url=other.avatar_url)
                        await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
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
                                if page * page_len + page_len > total - 1:
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
                        if total == 0:
                            desc = 'You have no cards! Go out and get some!'
                        else:
                            for i, x in enumerate(card_collection[page * page_len: page * page_len + page_len]):
                                desc += '**' + cards[str(x)]["name"] + '**\t|\t' + cards[str(x)]["rarity"] + "\t|\t" + str(i + 1 + page * page_len) + '/' + str(total) + '\n'
                        embed=discord.Embed(title="Your Cards", description=desc)
                        if total > 0:
                            embed.set_footer(text="You are on page " + str(page + 1) + "/" + str((total - 1) // page_len + 1) + ". Use `!back` and `!next` to scroll through the list!")
                        embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                        await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
                        user = message.author
                        def check_list(message):
                            return message.author == user and (message.content == "!back" or message.content == "!next" or "!list" in message.content)
                        try:
                            response = await bot.wait_for("message",timeout = 60.0, check=check_list)
                            if response.content == "!back":
                                if page <= 0:
                                    return
                                else:
                                    page -= 1
                            elif response.content == "!next":
                                if page * page_len + page_len > total - 1:
                                    return
                                else:
                                    page += 1
                            else:
                                return
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
                    if total == 0:
                        desc = 'You have no cards! Go out and get some!'
                    else:
                        for i, x in enumerate(card_collection[page * page_len: page * page_len + page_len]):
                            desc += '**' + cards[str(x)]["name"] + '** | ' + cards[str(x)]["rarity"] + " | " + str(i + 1 + page * page_len) + '/' + str(total) + '\n'
                    embed=discord.Embed(title="Your Cards", description=desc)
                    if total > 0:
                        embed.set_footer(text="You are on page " + str(page + 1) + "/" + str((total - 1) // page_len + 1) + ". Use `!back` and `!next` to scroll through the list!")
                    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                    await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
                    user = message.author
                    def check_list(message):
                        return message.author == user and (message.content == "!back" or message.content == "!next" or "!list" in message.content)
                    try:
                        response = await bot.wait_for("message",timeout = 60.0, check=check_list)
                        if response.content == "!back":
                            if page <= 0:
                                return
                            else:
                                page -= 1
                        elif response.content == "!next":
                            if page * page_len + page_len > total - 1:
                                return
                            else:
                                page += 1
                        else:
                            return
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
                    await show_card(message, card_id, message.author.name + " Card:", True, None, True)
                else:
                    await message.channel.send("Enter a valid id (1-" + str(len(players[message.author.id].cards)) + ")")
            except Exception:
                await message.channel.send("Enter a valid id (1-" + str(len(players[message.author.id].cards)) + ")")
        else:
            await message.channel.send(config["join_msg"].replace("%", config["prefix"]))
    
    if command == 'inspect':
        if len(args) == 0:
            await message.channel.send("Use `" + config["prefix"] + "inspect <id>` to view a card!")
        else:
            try:
                await show_card(message, args[0], 'View Card:', True, None, True)
            except Exception:
                await message.channel.send("Use a valid id (1-" + str(len(cards)) + ")")

    if command == 'drop':
        if message.author.id in config["administrators"]:
            drop = 1
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
                    drop = players[message.author.id].spawn("EX")
            
            await show_card(message, drop, message.author.name + " caught a:", False, None, True)

    if command == "cash_monies":
        if message.author.id in config["administrators"]:
            try:
                players[message.author.id].set_currency(int(args[0]))
            except Exception:
                await message.channel.send("Hello administrator. I don't want to expose your low iq, but the command is `" + config["prefix"] + "cash_monies <money>` to set your money.")

    if command == "sell":
        if message.author.id in players:
            if len(args) == 0:
                await message.channel.send("Use [" + config["prefix"] + "sell id] to sell a card for some quick money! *This is not a listing on a market, use [" + config["prefix"] + "market] instead!")
            else:
                player_cards = players[message.author.id].cards
                if int(args[0]) >= 1 and int(args[0]) <= len(player_cards):
                    card_id = player_cards[int(args[0]) - 1]
                    rarity = cards[card_id]["rarity"]
                    price = int(card_config["Sell_Rate"] * card_config[rarity]["currency"])
                    embed=discord.Embed(title="You are selling a " + rarity + " " + cards[card_id]["name"] + " for $" + str(price))
                    embed.set_footer(text="Type *" + config["prefix"] + "sell_confirm* to sell!")
                    await message.channel.send(embed=embed)
                    user = message.author
                    def check_sell(message):
                        return message.author == user and "!sell" in message.content
                    try:
                        response = await bot.wait_for('message',timeout=30.0,check=check_sell)
                        if response.content == "!sell_confirm":
                            players = update_players()
                            player_cards = players[user.id].cards
                            if player_cards[int(args[0]) - 1] == card_id:
                                players[user.id].delete([args[0]])
                                players[user.id].add_currency(price)
                                embed=discord.Embed(title="You sold a " + rarity + " " + cards[card_id]["name"] + " for $" + str(price))
                                await message.channel.send(embed=embed)
                            else:
                                await message.channel.send("Card is missing from your collection!")
                        else:
                            await message.channel.send("Sell only one card at a time! First sell is cancelled.")
                    except Exception:
                        await message.channel.send("Sell cancelled!")
                else:
                    await message.channel.send("Enter a valid id (1-" + str(len(player_cards)))
                    await message.channel.send("Sell cancelled!")
        else:
            await message.channel.send(config["join_msg"].replace("%", config["prefix"]))       

    if command == "market": #!market search #
        if message.author.id in players:
            market = update_market()
            if len(args) == 0:
                page = 0
                page_len = config["page_len"]
                while True:
                    market = update_market()
                    total = len(market)
                    desc = ''
                    if total == 0:
                        desc = 'There are no listings on the market'
                    else:
                        for i, x in enumerate(market[page * page_len: page * page_len + page_len]):
                            seller_name = 'market'
                            try:
                                if x["user_id"] != -1:
                                    seller_name = bot.get_user(int(x["user_id"])).name
                            except Exception:
                                print("Someone has an invalid id")
                                pass
                            if x["type"] == "card":
                                desc += '**' + cards[x["card_id"]]["name"] + '** | ' + cards[x["card_id"]]["rarity"] + " | Seller: " + seller_name + " | id: "  + str(i + 1 + page * page_len) + " | Price: " + str(x["card_price"]) + " " + '\n'
                            else:
                                desc += '**' + crates["crates"][x["card_id"]]["name"] + '** | Crate | Seller: ' + seller_name + " | id: "  + str(i + 1 + page * page_len) + " | Price: " + str(x["card_price"]) + " " + '\n'
                    embed=discord.Embed(description=desc)
                    if total > 0:
                        embed.set_footer(text="You are on page " + str(page + 1) + "/" + str((total - 1) // page_len + 1) + ". Use `!market back` and `!market next` to scroll through the list!")
                    embed.set_author(name="Current Market Listings", icon_url="https://melmagazine.com/wp-content/uploads/2019/07/Screen-Shot-2019-07-31-at-5.47.12-PM.png")
                    await message.channel.send(embed=embed)
                    user = message.author
                    def check_list(message):
                        return message.author == user and (message.content == "!market back" or message.content == "!market next" or "!market" in message.content)
                    try:
                        response = await bot.wait_for("message",timeout = 60.0, check=check_list)
                        if response.content == "!market back":
                            if page <= 0:
                                return
                            else:
                                page -= 1
                        elif response.content == "!market next":
                            if page * page_len + page_len > total - 1:
                                return
                            else:
                                page += 1
                        else:
                            return
                    except Exception:
                        return
            
            elif args[0] == "buy":
                try:
                    card_list = update_market()
                    if int(args[1]) >= 1:
                        selected_card = card_list[int(args[1]) - 1]
                        cost = selected_card["card_price"]
                        print(message.author.name + " bought from the market!")
                        if message.author.id == selected_card["user_id"] or players[message.author.id].has_currency(currency=cost):
                            if selected_card["type"] == "card":
                                ##remove listing
                                if remove_listing(args[1], selected_card):
                                    players[message.author.id].add_currency(-int(cost))
                                    players[message.author.id].give(selected_card["card_id"])
                                    if message.author.id == selected_card["user_id"]:
                                        await message.channel.send("You have removed your " + cards[selected_card["card_id"]]["name"] + " from the market")
                                    else:
                                        await message.channel.send("You have purchased a " + cards[selected_card["card_id"]]["name"])
                                    if selected_card["user_id"] != -1:
                                        players[selected_card["user_id"]].add_currency(int(cost)) * config["tax"]
                                else:
                                    await message.channel.send("Item has already been purchased")
                            else:
                                if remove_listing(args[1], selected_card):
                                    players[message.author.id].add_currency(-int(cost))
                                    players[message.author.id].give_crate(selected_card["card_id"])
                                    if message.author.id == selected_card["user_id"]:
                                        await message.channel.send("You have removed your " + crates["crates"][selected_card["card_id"]]["name"] + " from the market")
                                    else:
                                        await message.channel.send("You have purchased a " + crates["crates"][selected_card["card_id"]]["name"])
                                    if selected_card["user_id"] != -1:
                                        players[selected_card["user_id"]].add_currency(int(cost)) * config["tax"]
                                else:
                                    await message.channel.send("Item has already been purchased")
                        else:
                            await message.channel.send("Hey you! You have NO monies!")
                except Exception:
                    await message.channel.send("That's not a valid id!")
            
            elif args[0] == "sell":
                try:
                    card_list = update_market()
                    price = int(args[2])
                    card_id = players[message.author.id].cards[int(args[1]) - 1]
                    if players[message.author.id].remove(args[1]):
                        create_listing(message.author.id, price, card_id)
                        await message.channel.send("Made a listing for a " + cards[card_id]["rarity"] + " " + cards[card_id]["name"] + " for $" + str(price))
                    else:
                        await message.channel.send("Card is not in your collection")
                except Exception:
                    await message.channel.send("That's not a valid id or money!")
        else:
            await message.channel.send(config["join_msg"].replace("%", config["prefix"]))
    
    if command == "worth":
        desc = ''
        for x in card_config:
            if x in ["Common", "Uncommon", "Rare", "Epic", "Legendary", "EX", "Special"]:
                desc += x + " is worth at least $" + str(card_config[x]["currency"]) + '\n'
        embed = discord.Embed(description=desc, color=config["embed_color"])
        embed.set_author(name="Card Value", icon_url="https://w0.pngwave.com/png/944/747/coins-png-clip-art.png")
        await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)

    if command == "daily":
        author = players[message.author.id]
        random.seed(a=message.id)
        d = random.random()
        if(len(args) != 0):
            if message.author.id in config["administrators"]:
                if(args[0].lower() == 'reset'):
                    author.reset_daily()
                else:
                    author.reset_daily()
                    d = float(args[0])
        if(author.daily()):
            embed=discord.Embed(title="Daily Reward", description="You collected your rewards! You got: ", color=0x8400ff)
            w = crates["daily"]["weight"]
            print(str(d))
            if d < w[0]:
                m = author.add_currency(random.randrange(200,300))
                embed.add_field(name="Money", value=m, inline=True)
            elif d < w[1]:
                drop = author.spawn("Common", currency=False)
                embed.add_field(name="Card", value=cards[drop]["name"] + " (Common)", inline=True)
            elif d < w[2]:
                drop = author.spawn("Uncommon", currency=False)
                embed.add_field(name="Card", value=cards[drop]["name"] + " (Uncommon)", inline=True)
            elif d < w[3]:
                drop= author.spawn("Common",currency=False)
                embed.add_field(name="Card", value=cards[drop]["name"] + " (Common)", inline=True)
                drop= author.spawn("Uncommon", currency=False)
                embed.add_field(name="Card", value=cards[drop]["name"] + " (Uncommon)", inline=True)
            elif d < w[4]:
                m = author.add_currency(random.randrange(500,750))
                embed.add_field(name="Money", value=m, inline=True)
            elif d < w[5]:
                drop = author.spawn("Epic", currency=False)
                embed.add_field(name="Card", value=cards[drop]["name"] + " (Epic)", inline=True)
                m = author.add_currency(1000)
                embed.add_field(name="Money", value=m, inline=True)
            else:
                drop = author.spawn("Legendary", currency=False)
                embed.add_field(name="Card", value=cards[drop]["name"] + " (Legendary)", inline=True)
                m = author.add_currency(2000)
                embed.add_field(name="Money", value=m, inline=True)
            random.seed()
            await message.channel.send("<@" + str(message.author.id) + ">", embed=embed)
        else:
            await message.channel.send("You have already claimed your daily reward today. You can claim it again tomorrow.")

    def isFloat(string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    if command == "bet":
        user = message.author
        if(len(args) < 2):
            await message.channel.send("Not enough arguments. Usage: `bet <amount> <chance>`.")
        else:
            if(isFloat(args[0]) and isFloat(args[1])):
                if(float(args[1]) > 1 or float(args[1]) < 0):
                    await message.channel.send("Proportion must be greater than 0 and less than 1.")
                elif(float(args[0]) < 0 or float(args[0]) > players[user.id].currency):
                    await message.channel.send("You don't have enough money to make this bet. You only have %s money." % players[user.id].currency)
                else:
                    if '--over' in message.content:
                        roll_limit = (1-float(args[1])) + config["bet_rig_alpha"]
                        if roll_limit >= 1:
                            roll_limit = 1
                        win_amount = int((1 / roll_limit * float(args[0]) - float(args[0])) * config["bet_rig_beta"])
                    else:
                        roll_limit = float(args[1]) + config["bet_rig_alpha"]
                        if roll_limit >= 1:
                            roll_limit = 1
                        win_amount = int((1 / roll_limit * float(args[0]) - float(args[0])) * config["bet_rig_beta"])
                    if win_amount <= 0:
                        win_amount = 0
                    await message.channel.send(
                        "Betting `%s` with chance `%s`. Type `%sbet_confirm` to confirm your bet. Type `%sbet_cancel` to cancel your bet. Potential win: `%s`" % (
                            args[0],
                            args[1] if not '--over' in message.content else str(round(1.0-(float(args[1])),2)),
                            config["prefix"],
                            config["prefix"],
                            str(win_amount)
                        )
                    )
                    try:
                        def check_list(m):
                                return m.author == user and (m.content == '!bet_confirm' or m.content == '!bet_cancel')
                        response = await bot.wait_for("message",timeout = 60.0, check=check_list)
                        if(response.content == "!bet_confirm"):
                            if '--over' in message.content:
                                result = random.random()
                                print('Chance: ' + args[1] + '\tResult: ' + str(result))
                                if(result >= float(args[1])):
                                    win = players[user.id].add_currency(win_amount)
                                    embed = discord.Embed(title="You WIN!", description="You won " + str(win) + "!", color=0x00ff00)
                                    await message.channel.send(embed=embed)
                                else:
                                    embed = discord.Embed(title="You LOSE.", description="You lost " + str(args[0]) + "!", color=0xff0000)
                                    players[user.id].add_currency(-1 * float(args[0]))
                                    await message.channel.send(embed=embed)
                            else:
                                result = random.random()
                                print('Chance: ' + args[1] + '\tResult: ' + str(result))
                                if(result <= float(args[1])):
                                    win = players[user.id].add_currency(win_amount)
                                    embed = discord.Embed(title="You WIN!", description="You won " + str(win) + "!", color=0x00ff00)
                                    await message.channel.send(embed=embed)
                                else:
                                    embed = discord.Embed(title="You LOSE.", description="You lost " + str(args[0]) + "!", color=0xff0000)
                                    players[user.id].add_currency(-1 * float(args[0]))
                                    await message.channel.send(embed=embed)
                        else:
                            await message.channel.send("Betting cancelled.")
                    except Exception:
                        await message.channel.send("There was an error with the bet.")
    
    
    if command == "coinflip":
        if len(args) < 2:
            await message.channel.send("Not enough arguments. Usage: `!coinflip @user <amount>`")
        elif not int(args[0][3:-1]) in players or not players[message.author.id].has_currency(float(args[1])) or not players[int(args[0][3:-1])].has_currency(float(args[1])):
            await message.channel.send("There was an error making this coinflip.")
        else:
            await message.channel.send("Awaiting response...")
            def check_list(m):
                return m.author.id == int(args[0][3:-1]) and (m.content == '!coinflip_accept' or m.content == '!coinflip_reject')
            response = await bot.wait_for("message",timeout = 60.0, check=check_list)
            print(response.content)
            if response.content == '!coinflip_accept':
                people = [message.author.id, int(args[0][3:-1])]
                winner = random.choice(people)
                people.remove(winner)
                win = config["tax"] * int(2 * float(args[1]))
                print("Winner: %s" % players[winner].username)
                await message.channel.send("The winner is: **%s**, winning %d." % (players[winner].username, win))
                players[winner].add_currency(config["tax"] * int(float(args[1])))
                players[int(people[0])].add_currency(-1 * int(float(args[1])))
            else:
                await message.channel.send("The coinflip has been rejected.")

    if command == "crates":
        player = players[message.author.id]
        player_crates = player.get_crates()
        player_keys = player.get_keys()

        if len(args) == 0:
            desc = '**Crates:**\n'
            for x in crates["crates"]:
                if x != "weights":
                    if x in player_crates:
                        desc += 'id: ' + x + ' | ' + crates["crates"][x]["name"] + " (" + crates["keys"][crates["crates"][x]["key"]]["name"] + ") x" + str(player_crates[x]) + '\n'
                    else:
                        desc += 'id: ' + x + ' | ' + crates["crates"][x]["name"] + " (" + crates["keys"][crates["crates"][x]["key"]]["name"] + ") x0\n"
            desc += '\n**Keys:**\n'
            for x in crates["keys"]:
                if x != "weights":
                    if x in player_keys:
                        desc += 'id: ' + x + ' | ' + crates["keys"][x]["name"] + " ($" + str(crates["keys"][x]["price"]) + ") x" + str(player_keys[x]) + '\n'
                    else:
                        desc += 'id: ' + x + ' | ' + crates["keys"][x]["name"] + " ($" + str(crates["keys"][x]["price"]) + ") x0\n"

            embed = discord.Embed(title="Your Crates and Keys:", description=desc, color=config["embed_color"])
            embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
            await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
            return
        
        if args[0] == 'buy':
            try:
                if int(args[1]) >= 1 and int(args[1]) <= len(crates["keys"]) - 1:
                    if player.has_currency(crates["keys"][args[1]]["price"]):
                        player.add_currency(-crates["keys"][args[1]]["price"])
                        player.give_key(args[1])
                        embed = discord.Embed(description=message.author.name + " bought a " + crates["keys"][args[1]]["name"], color=config["embed_color"])
                        embed.set_author(name="Crates", icon_url="https://i.imgur.com/ZVQTsnh.png")
                        await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
                    else:
                        await message.channel.send("You don't have enough money!")
                else:
                    await message.channel.send("Please enter a valid id (1-" + str(len(crates["keys"]) - 1) + ")")
            except Exception:
                print("Something went wrong with buying keys")
        
        if args[0] == 'info':
            try:
                if int(args[1]) >= 1 and int(args[1]) <= len(crates["crates"]) - 1:
                    embed = discord.Embed(description=crates["crates"][args[1]]["desc"], color=config["embed_color"])
                    embed.set_author(name=crates["crates"][args[1]]["name"] + " (" + crates["keys"][crates["crates"][args[1]]["key"]]["name"] + ")", icon_url="https://i.imgur.com/ZVQTsnh.png")
                    await message.channel.send("<@" + str(message.author.id) + ">",embed=embed)
                else:
                    await message.channel.send("Please enter a valid id (1-" + str(len(crates["crates"]) - 1) + ")")
            except Exception:
                print("Something went wrong with listing crates")
        
        if args[0] == 'open':
            if int(args[1]) >= 1 and int(args[1]) <= len(crates["crates"]) - 1:
                key = crates["keys"][crates["crates"][args[1]]["key"]]
                crate = crates["crates"][args[1]]
                if player_crates[args[1]] >= 1:
                    if player_keys[crates["crates"][args[1]]["key"]] >= 1:
                        if not player.open_crate(args[1]):
                            await message.channel.send("You are missing a crate or key")
                            return
                        print(message.author.name + " is opening a " + crate["name"] + " with a " + key["name"])
                        if crate["type"] == "Rarity":
                            num_rolls = crate["rolls"]
                            for x in range(num_rolls):
                                t = 0
                                next_t = 10
                                card_id = get_random_rarity(numpy.random.choice(crates["rarities"], 1, p=crate["weights"])[0])
                                embed = discord.Embed(title=cards[card_id]["name"],description="*" + cards[card_id]["desc"] + "*", color=card_config[cards[card_id]["rarity"]]["color"])
                                if message.channel.guild.icon_url == None:
                                    embed.set_author(name=message.author.name + " is rolling:", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                                else:
                                    embed.set_author(name=message.author.name + " is rolling:", icon_url=message.channel.guild.icon_url)
                                embed.set_thumbnail(url=message.author.avatar_url)
                                embed.set_image(url=cards[card_id]["image"])
                                roll_message = await message.channel.send(embed=embed)
                                await asyncio.sleep(1)
                                while next_t <= 100:
                                    t += 2 * math.sqrt(110 - next_t) * random.random() + 3
                                    if t > next_t:
                                        next_t += 10
                                        card_id = get_random_rarity(numpy.random.choice(crates["rarities"], 1, p=crate["weights"])[0])
                                        embed = discord.Embed(title=cards[card_id]["name"],description="*" + cards[card_id]["desc"] + "*", color=card_config[cards[card_id]["rarity"]]["color"])
                                        if message.channel.guild.icon_url == None:
                                            embed.set_author(name=message.author.name + " is rolling:", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                                        else:
                                            embed.set_author(name=message.author.name + " is rolling:", icon_url=message.channel.guild.icon_url)
                                        embed.set_thumbnail(url=message.author.avatar_url)
                                        embed.set_image(url=cards[card_id]["image"])
                                        await roll_message.edit(embed=embed)
                                    await asyncio.sleep(0.3)
                                card_id = get_random_rarity(numpy.random.choice(crates["rarities"], 1, p=crate["weights"])[0])
                                embed = discord.Embed(title=cards[card_id]["name"],description="*" + cards[card_id]["desc"] + "*", color=card_config[cards[card_id]["rarity"]]["color"])
                                if message.channel.guild.icon_url == None:
                                    embed.set_author(name=message.author.name + " got a:", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                                else:
                                    embed.set_author(name=message.author.name + " got a:", icon_url=message.channel.guild.icon_url)
                                embed.set_thumbnail(url=message.author.avatar_url)
                                embed.set_image(url=cards[card_id]["image"])
                                await roll_message.edit(content="<@" + str(message.author.id) + ">",embed=embed)
                                player.give(card_id)
                        elif crate["type"] == "Collection":
                            num_rolls = crate["rolls"]
                            sum_probs = sum(crate["weights"])
                            probs = [x / sum_probs for x in crate["weights"]]
                            for x in range(num_rolls):
                                t = 0
                                next_t = 10
                                card_id = numpy.random.choice(collections_config[crate["collection"]], 1, p=probs)[0]
                                embed = discord.Embed(title=cards[card_id]["name"],description="*" + cards[card_id]["desc"] + "*", color=card_config[cards[card_id]["rarity"]]["color"])
                                if message.channel.guild.icon_url == None:
                                    embed.set_author(name=message.author.name + " is rolling:", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                                else:
                                    embed.set_author(name=message.author.name + " is rolling:", icon_url=message.channel.guild.icon_url)
                                embed.set_thumbnail(url=message.author.avatar_url)
                                embed.set_image(url=cards[card_id]["image"])
                                roll_message = await message.channel.send(embed=embed)
                                await asyncio.sleep(1)
                                while next_t <= 100:
                                    t += 2 * math.sqrt(110 - next_t) * random.random() + 3
                                    if t > next_t:
                                        next_t += 10
                                        card_id = numpy.random.choice(collections_config[crate["collection"]], 1, p=probs)[0]
                                        embed = discord.Embed(title=cards[card_id]["name"],description="*" + cards[card_id]["desc"] + "*", color=card_config[cards[card_id]["rarity"]]["color"])
                                        if message.channel.guild.icon_url == None:
                                            embed.set_author(name=message.author.name + " is rolling:", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                                        else:
                                            embed.set_author(name=message.author.name + " is rolling:", icon_url=message.channel.guild.icon_url)
                                        embed.set_thumbnail(url=message.author.avatar_url)
                                        embed.set_image(url=cards[card_id]["image"])
                                        await roll_message.edit(embed=embed)
                                    await asyncio.sleep(0.3)
                                card_id = numpy.random.choice(collections_config[crate["collection"]], 1, p=probs)[0]
                                embed = discord.Embed(title=cards[card_id]["name"],description="*" + cards[card_id]["desc"] + "*", color=card_config[cards[card_id]["rarity"]]["color"])
                                if message.channel.guild.icon_url == None:
                                    embed.set_author(name=message.author.name + " got a:", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                                else:
                                    embed.set_author(name=message.author.name + " got a:", icon_url=message.channel.guild.icon_url)
                                embed.set_thumbnail(url=message.author.avatar_url)
                                embed.set_image(url=cards[card_id]["image"])
                                await roll_message.edit(content="<@" + str(message.author.id) + ">",embed=embed)
                                player.give(card_id)
                    else:
                        await message.channel.send("You don't have a " + key["name"])
                else:
                    await message.channel.send("You don't have a " + crate["name"])
            else:
                await message.channel.send("Please enter a valid id (1-" + str(len(crates["crates"]) - 1) + ")")
        
        if args[0] == 'give':
            if message.author.id in config["administrators"]:
                players[message.author.id].give_crate(args[1])
                print("gave " + message.author.name + " a " + crates["crates"][args[1]]["name"])

with open("auth.json") as f:
    auth = json.load(f)
    bot.run(auth["token"])
    f.close()