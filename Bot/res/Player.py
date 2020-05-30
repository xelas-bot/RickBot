from discord.ext import commands
import pymongo
from pymongo import MongoClient
import urllib.parse
import json
import random

# auth
with open("auth.json") as f:
    auth = json.load(f)
    global cluster
    cluster = MongoClient(auth["mongo_key"])
    f.close()

# cards
with open("data/cards.json") as f:
    global card_data
    card_data = json.load(f)
    f.close()

# rarities
with open("data/card_rarity.json") as f:
    global card_rarity
    card_rarity = json.load(f)
    f.close()

# card config
with open("card_config.json") as f:
    global card_config
    card_config = json.load(f)
    f.close()

db = cluster["game"]
collection = db["players"]

class Player:
    def __init__(self, id, username, currency=100, cards=[]):
        self.id = id
        self.username = username
        self.currency = currency
        self.cards = cards

    def create_player(self):
        post = {"_id": self.id, "username": self.username, "currency": self.currency, "cards": self.cards}
        collection.insert_one(post)
        print("Created player")

    def change_Currency(self, new_currency):
        self.currency = new_currency
        self.set_db()
    

    def set_db(self):
        myquery = {"_id": self.id}
        newvalues = { "$set": {"currency": self.currency, "cards": self.cards}}
        collection.update_one(myquery, newvalues)
    
    def get_db(self):
        data = collection.find_one({"_id": self.id})
        self.currency = data["currency"]
        self.cards = data["cards"]
    
    def delete(self, cards):
        self.cards = [x for i, x in enumerate(self.cards) if not str(i + 1) in cards]
        self.set_db()
    
    def spawn(self, rarity):
        self.get_db()
        drops = card_rarity[rarity]
        drop = random.choice(drops)
        print(self.username + " got a " + card_data[drop]["name"] + " (" + card_data[drop]["rarity"] + ")")
        self.card_data.append(drop)
        self.currency += card_config[rarity]["currency"]
        self.set_db()
        return drop
    
    def give(self, card):
        try:
            if int(card) >= 1 and int(card) <= len(card_data):
                self.cards.append(str(card))
                print(self.username + " got a " + card_data[str(card)]["name"] + " (" + card_data[str(card)]["rarity"] + ")")
            else:
                print("Invalid card id")
        except Exception:
            print("Not a card id")
        self.set_db()