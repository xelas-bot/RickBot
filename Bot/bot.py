import json
import discord
import math
import random


# Auth bot
bot = discord.Client()
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    print('ssp is super obese like 100 tons')

# config options
with open('config.json') as f:
    config = json.load(f)
    global prefix 
    prefix = config['prefix']
    f.close()

# bot message
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content[0] != prefix:
        return
    
    args = message.content.split(' ')
    print(args)


with open("auth.json") as f:
    auth = json.load(f)
    bot.run(auth["token"])
    f.close()

