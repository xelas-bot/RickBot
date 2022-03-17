import json
import discord
import math
import random
import shlex
import asyncio
from discord.ext import commands
import pymongo
from pymongo import MongoClient
import urllib.parse
import json
from secrets import token_bytes
from coincurve import PublicKey
from sha3 import keccak_256

playerCreated = False


with open("auth.json") as f:
    auth = json.load(f)
    global cluster
    cluster = MongoClient(auth["mongo_key"])

db = cluster["game"]

collection = db["players"]
playerinfo = db["playerinfo"]

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

def not_bot(message):
    return message.author != bot.user


def generate_ethereum_wallet():


    private_key = keccak_256(token_bytes(32)).digest()
    public_key = PublicKey.from_valid_secret(private_key).format(compressed=False)[1:]
    addr = keccak_256(public_key).digest()[-20:]

    print('private_key:', private_key.hex())
    print('eth addr: 0x' + addr.hex())

    return private_key.hex(), addr.hex()



    ### Output ###
    # private_key: 7bf19806aa6d5b31d7b7ea9e833c202e51ff8ee6311df6a036f0261f216f09ef
    # eth addr: 0x3db763bbbb1ac900eb2eb8b106218f85f9f64a13


# bot message
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    try:
        if message.content[0] != prefix:
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

    if command == 'addseller':
        file = discord.File("data/zeken.png", "zeken.jpg")
        embed = discord.Embed()
        embed.set_image(url="attachment://zeken.jpg")
        await message.channel.send("u suck")
        await message.channel.send(file=file, embed=embed)

    if command == 'claimETH':
        playerid = message.author.id
        private_key, public_key = generate_ethereum_wallet()

        myquery = { "_id": playerid }
        newvalues = { "$set": { "private_key": private_key } }
        collection.update_one(myquery,newvalues)

        embed=discord.Embed(title="Ethereum Wallet Generator", url="https://metamask.io/", description="Visit https://metamask.io/ to check your wallets balance or visit the blockchain to check its balance! Your private key has been DMed to you.", color=0x09bad2)
        embed.add_field(name="Public Wallet Address", value=public_key, inline=False)
        embed.add_field(name="Balance", value="0 - 0.00001 ETH in wallet", inline=True)
        await message.author.send(mention_author=True,content= "Your private key (DO NOT SHARE) is " + str(private_key))
        await message.channel.send(embed=embed)
        

    if command == 'roll':
        if len(args) > 0 and args[0].isdigit() and int(args[0]) > 1:
            await message.channel.send(message.author.name + ' rolled a ' + str(random.randrange(1,int(args[0]))))
        else:
            await message.channel.send(message.author.name + ' rolled a ' + str(random.randrange(1,100)))
    if command == "evennums":
        x = random.randrange(1, 10)
        await message.channel.send("Is the following number even or odd: " + str(x))
        user = message.author
        def check(message):
            return message.author != bot.user and message.author == user and message.content.lower() == "odd" or message.content.lower() == "even"
        
        try:
            response = await bot.wait_for('message',timeout=30.0,check=check)
        except Exception:
            await message.channel.send('You didn\'t get it in time :(')
        
        if x % 2 == 0 and response.content.lower() == 'even' or x % 2 == 1 and response.content.lower() == 'odd':
            await message.channel.send('wow u almost have dlz\'s iq')
        else:
            await message.channel.send('ur dumbness is almost as big as shrey\'s weight')


    
 

with open("auth.json") as f:
    auth = json.load(f)
    bot.run(auth["token"])
    f.close()