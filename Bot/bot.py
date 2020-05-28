import json
import discord
import math
import random

bot = discord.Client()
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    print('ssp is super obese like 100 tons')

@client.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    


with open("auth.json") as f:
    auth = json.load(f)
    bot.run(auth["token"])

