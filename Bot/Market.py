import json
import discord
import math
import numpy
import random
import shlex
import asyncio
from discord.ext import commands
import urllib.parse
import json
import pymongo
from pymongo import MongoClient
from res.Player import Player
import schedule
from datetime import datetime
import time

print("Market bot on!")

# auth
with open("auth.json") as f:
    auth = json.load(f)
    global cluster
    cluster = MongoClient(auth["mongo_key"])
    f.close()

# Mongo Database
db = cluster["game"]
db_players = db["players"]
db_market = db["market"]

# market_bot options
with open('data/market_bot.json') as f:
    global market_bot
    market_bot = json.load(f)
    f.close()


def refresh_market(t):
    total = 0
    for x in market_bot:
        total += x["weight"]
    
    weights = []
    for x in market_bot:
        weights.append(x["weight"] / total)

    choice = numpy.random.choice(market_bot, 1, p=weights)[0]
    price = random.randrange(choice["price_lower"], choice["price_upper"])
    listing = {"user_id": -1, "card_price": price, "card_id": choice["card_id"]}
    db_market.insert_one(listing)

schedule.every().day.at("08:00").do(refresh_market,'Added listing to market')

while True:
    schedule.run_pending()
    time.sleep(5)