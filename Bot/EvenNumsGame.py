import random
import discord
import json
evenFlag = 1
game = False
client = discord.Client()
x = 0

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('gamestart'):
        global x
        x = random.randrange(1, 10)

        playerAns = 0
        if x%2 == 0:
            global evenFlag
            evenFlag = 2


        await message.channel.send('Welcome to ze ez game, is ze following number ze even or ze odd: ' + str(x))
        global game
        game = True
    if game:
        if message.content.startswith('!even') and x % 2 == 0:
            await message.channel.send("u mfking genius")
            return
        elif message.content.startswith('!even') and x % 2 != 0:

            await message.channel.send("ur name must be ricky!")
            return

        if message.content.startswith('!odd') and x % 2 == 1:
            await message.channel.send("u mfking genius")
            return
        elif message.content.startswith("!odd") and x % 2 != 1:
            await message.channel.send("ur name must be ricky!")
            return

with open("auth.json") as f:
    data = json.load(f)
    client.run(data["token"])