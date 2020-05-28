import discord
import io

import os.path



client = discord.Client()

@client.event
async def on_ready():
    print('Login success as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        file = discord.File("C:/Users/Shrey Patel/Downloads/zeken.png", "zeken.jpg")
        embed = discord.Embed()
        embed.set_image(url="attachment://zeken.jpg")
        await message.channel.send("u suck")
        await message.channel.send(file=file, embed=embed)


client.run('NzE1MzQwMzA2MTQ4NjIyNDk2.XtAeeA.aCOhO1po4aFiditxB7LS_AdyCM4')