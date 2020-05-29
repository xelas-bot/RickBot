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

    if message.content.startswith('!mycard'):
        file = discord.File("C:/Users/Shrey Patel/Downloads/zeken.png", "zeken.jpg")
        embed = discord.Embed(description="He WILL fuck your bitch", color=15592839)
        embed.set_author(name="ZeKenneth", icon_url="https://www.howtogeek.com/wp-content/uploads/2018/06/shutterstock_1006988770.png")
        embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")

        embed.add_field(name="Weight", value="0", inline=True)
        embed.add_field(name="Power", value="0", inline=True)
        embed.add_field(name="Sex Appeal", value="4", inline=True)
        embed.add_field(name="Negro", value="True", inline=True)
        embed.add_field(name="Lethal", value="False", inline=True)
        embed.add_field(name="DLZ", value="1000", inline=True)



        embed.set_image(url="attachment://zeken.jpg")


        await message.channel.send("Your Card:")
        await message.channel.send(file=file, embed=embed)


client.run('NzE1MzQwMzA2MTQ4NjIyNDk2.XtAeeA.aCOhO1po4aFiditxB7LS_AdyCM4')