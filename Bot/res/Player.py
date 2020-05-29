import discord
from discord.ext import commands
import pymongo
from pymongo import MongoClient
import urllib.parse
cluster = MongoClient("mongodb+srv://dbAdmin:cisd1158@disc-valqe.gcp.mongodb.net/test")

db = cluster["game"]

collection = db["players"]





client = discord.Client()


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')





@client.event
async def on_message(ctx):
    print(f"{ctx.channel}: {ctx.author}: {ctx.author.name}: {ctx.content}")
    myquery = {"_id": ctx.author.id}
    if (collection.count_documents(myquery) == 0):
        if "!createplayer" in str(ctx.content.lower()):
            post = {"_id": ctx.author.id, "score": 1, "EXP": 100}
            collection.insert_one(post)
            await ctx.channel.send('You are in!')
    else:
        if "!createplayer" in str(ctx.content.lower()):
            query = {"_id": ctx.author.id}


            await ctx.channel.send('You have already created a character, please choose your starter deck with !choose')


##user = collection.find(query)
##            for result in user:
 ##               score = result["score"]
  ##              experience = result["EXP"]
  ##          score = score + 1
  ##          experience = experience + 100
   ##         collection.update_one({"_id": ctx.author.id}, {"$set": {"score": score}})
   ##         collection.update_one({"_id": ctx.author.id}, {"$set": {"EXP": experience}})





client.run("NzE1MzQwMzA2MTQ4NjIyNDk2.XtAeeA.aCOhO1po4aFiditxB7LS_AdyCM4")