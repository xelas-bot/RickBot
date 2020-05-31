from discord.ext import commands
import pymongo
from pymongo import MongoClient
import urllib.parse
import json
import random
from datetime import datetime, timedelta

# auth
with open("./Bot/auth.json") as f:
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

# crates config
with open("data/crates.json") as f:
    global crates_config
    crates_config = json.load(f)
    f.close()

db = cluster["game"]
collection = db["players"]

class Player:
    def __init__(self, id, username, currency=100, cards=[], crates=[], keys=[], last_time=datetime.today() - timedelta(1)):
        self.id = id
        self.username = username
        self.currency = currency
        self.cards = cards
        self.crates = crates
        self.keys = keys
        self.last_time = last_time

    def create_player(self):
        post = {"_id": self.id, "username": self.username, "currency": self.currency, "cards": self.cards, "crates": self.crates, "keys": self.keys, "last_time": self.last_time}
        collection.insert_one(post)
        print("Created player")

    def add_currency(self, currency):
        self.get_db()
        self.currency += currency
        self.set_db()
        return currency
    
    def set_currency(self, currency):
        self.get_db()
        self.currency = currency
        self.set_db()
        return currency

    def set_db(self):
        myquery = {"_id": self.id}
        newvalues = { "$set": {"currency": self.currency, "cards": self.cards, "crates": self.crates, "keys": self.keys, "last_time": self.last_time}}
        collection.update_one(myquery, newvalues)
    
    def get_db(self):
        data = collection.find_one({"_id": self.id})
        self.currency = data["currency"]
        self.cards = data["cards"]
        self.crates = data["crates"]
        self.keys = data["keys"]
        self.last_time = data["last_time"]
    
    def daily(self):
        self.get_db()
        if datetime.date(self.last_time) == datetime.date(datetime.today()):
            return False
        print(datetime.date(self.last_time))
        self.last_time = datetime.today()
        self.set_db()
        return True

    def reset_daily(self):
        self.get_db()
        self.last_time = datetime.today() - timedelta(1)
        self.set_db()
        return True
    
    def compare(self, index, card_ids):
        print(index)
        print(card_ids)
        self.get_db()
        same = True
        for i, c in zip(index, card_ids):
            if int(i) > len(self.cards) or int(i) < 1 or self.cards[int(i) - 1] != c:
                same = False
        return same

    def delete(self, cards):
        self.get_db()
        self.cards = [x for i, x in enumerate(self.cards) if not str(i + 1) in cards]
        self.set_db()
    
    def remove(self, card):
        self.get_db()
        if int(card) >= 1 and int(card) <= len(self.cards):
            del self.cards[int(card) - 1]
            self.set_db()
            return True
        else:
            return False
    
    def reward(self, rarity):
        self.get_db()
        money = random.randint(card_config[rarity]["currency"] * (1 - card_config["Coin_Dev"]), card_config[rarity]["currency"] * (1 + card_config["Coin_Dev"]))
        self.currency += money
        self.set_db()
        return money
    
    def spawn(self, rarity, exclude = [], currency = False):
        self.get_db()
        drops = [x for x in card_rarity[rarity] if not x in exclude]
        if len(drops) <= 0:
            drops = card_rarity[rarity]
        drop = random.choice(drops)
        print(self.username + " got a " + card_data[drop]["name"] + " (" + card_data[drop]["rarity"] + ")")
        self.cards.append(drop)
        if currency:
            self.currency += card_config[rarity]["currency"] * (1 - card_config["Sell_Rate"])
        self.set_db()
        return drop
    
    def give(self, card):
        self.get_db()
        try:
            if int(card) >= 1 and int(card) <= len(card_data):
                self.cards.append(str(card))
                print(self.username + " got a " + card_data[str(card)]["name"] + " (" + card_data[str(card)]["rarity"] + ")")
            else:
                print("Invalid card id")
        except Exception:
            print("Not a card id")
        self.set_db()
    
    def give_key(self, key):
        self.get_db()
        self.keys.append(key)
        self.set_db()
    
    def has_currency(self, currency):
        self.get_db()
        return self.currency >= currency
    
    def get_card_len(self):
        return len(self.cards)
    
    def get_rarities(self, rarity):
        self.get_db()
        return [(i, x) for i, x in enumerate(self.cards) if card_data[x]["rarity"] == rarity]
    
    def get_crates(self):
        self.get_db()
        crates = {}
        for x in self.crates:
            if x in crates:
                crates[x] += 1
            else:
                crates[x] = 1
        return crates
    
    def get_keys(self):
        self.get_db()
        keys = {}
        for x in self.keys:
            if x in keys:
                keys[x] += 1
            else:
                keys[x] = 1
        return keys
    
    @staticmethod
    def update_rarities():
        with open("data/card_rarity.json") as f:
            global card_rarity
            card_rarity = json.load(f)
            f.close()
