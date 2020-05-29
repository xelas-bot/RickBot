from discord.ext import commands
import pymongo
from pymongo import MongoClient
import urllib.parse
import json
playerCreated = False


with open("auth.json") as f:
    auth = json.load(f)
    global cluster
    cluster = MongoClient(auth["mongo_key"])

db = cluster["game"]
collection = db["players"]

class Player:
    def __init__(self, id, username, currency=500, exp=0, cards=[]):
        self.id = id
        self.username = username
        self.currency = currency
        self.cards = cards

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
        

##user = collection.find(query)
##            for result in user:
 ##               score = result["score"]
  ##              experience = result["EXP"]
  ##          score = score + 1
  ##          experience = experience + 100
   ##         collection.update_one({"_id": ctx.author.id}, {"$set": {"score": score}})
   ##         collection.update_one({"_id": ctx.author.id}, {"$set": {"EXP": experience}})





