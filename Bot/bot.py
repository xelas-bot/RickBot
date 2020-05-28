import json
import discord
import math
import random
import shlex
import asyncio


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
        file = discord.File("C:/Users/Shrey Patel/Downloads/zeken.png", "zeken.jpg")
        embed = discord.Embed()
        embed.set_image(url="attachment://zeken.jpg")
        await message.channel.send("u suck")
        await message.channel.send(file=file, embed=embed)
        

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

