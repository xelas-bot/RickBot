import discord
import io

import os.path

file = discord.File("C:/Users/Shrey Patel/Downloads/zeken.png", "zeken.jpg")
embed = discord.Embed()
embed.set_image(url="attachment://zeken.jpg")

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send("u suck")
        await message.channel.send(file=file, embed=embed)


client.run('NzE1MzQwMzA2MTQ4NjIyNDk2.XtAcRA.2ItxydtapLK0WnJzLCQGXoq2JtY')