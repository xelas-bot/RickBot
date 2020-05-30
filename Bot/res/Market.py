from discord.ext import commands
import pymongo
from pymongo import MongoClient
import urllib.parse
import json
import random



class Market:
    def __init__(self, ):



        post = {"_cardid": "15", "_id": self.id, "currency": currency, "cards": self.cards}

    def create_listing(self,userID=,cardprice=,CardID=  ):
        post = {"_cardid": "15", "_id": self.id, "currency": currency, "cards": self.cards}

    def show_market():

        embed = discord.Embed(description="Current Market Listings", color=00000000)



        embed.set_author(name="Market Listing", icon_url="https://www.howtogeek.com/wp-content/uploads/2018/06/shutterstock_1006988770.png")
        embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")

        embed.add_field(name="Weight", value="0", inline=True)
        embed.add_field(name="Power", value="0", inline=True)
        embed.add_field(name="Sex Appeal", value="4", inline=True)
        embed.add_field(name="Negro", value="True", inline=True)
        embed.add_field(name="Lethal", value="False", inline=True)
        embed.add_field(name="DLZ", value="1000", inline=True)

        await message.channel.send(embed=embed)
        pass
    def update_market():
        pass

    if command == "marketshow":
        pass
