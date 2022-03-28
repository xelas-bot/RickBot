import json
import random
import discord
from discord.ext.commands import Bot
import json
import random
from datetime import datetime, timezone

from event import build_embed, pull_recent_games, get_spectator_info

states = {
    'in_game' : False,
    'ongoing_bet' : False
}

# load userdata
with open('Bot/data/userdata/userdata.json', encoding='utf8') as f:
    global userdata
    userdata = json.load(f)

# load champion data
with open('Bot/data/LOLDATA/champion.json', encoding='utf8') as f:
    global LOL_CHAMPION_INFO
    LOL_CHAMPION_INFO = json.load(f)['data']

# config options
with open('config.json') as f:
    config = json.load(f)
    global prefix 
    prefix = config['prefix']

intents = discord.Intents().all()
bot = Bot(prefix, intents=intents)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.event
async def on_member_update(before, after):
    if before.id == 348149413618647040:
        if after.activities:
            after_activity = next(activity for activity in after.activities)
            if after_activity.start:
                if not states['in_game']:
                    print('{} started playing {} at {}'.format(after.name, after_activity.name, after_activity.start))
                    states['in_game'] = True
                    if after_activity.name == 'League of Legends':
                        sum_id = userdata[str(after.id)]['summonerId']
                        info = get_spectator_info(sum_id=sum_id)
                        player = next(participant for participant in info['participants'] if participant['summonerId'] == sum_id)
                        champion = next(champ for champ in LOL_CHAMPION_INFO if LOL_CHAMPION_INFO[champ]['key'] == str(player['championId']))
                        print('{} is playing {}, {}.'.format(after.name, champion, LOL_CHAMPION_INFO[champion]['title']))

        else:
            if states['in_game']:
                before_activity = next(activity for activity in before.activities)
                states['in_game'] = False
                print('{} stopped playing {} at {}'.format(before.name, before_activity.name, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))

# Removed outdated commands

@bot.command()
async def roll(ctx, *args):
    if len(args) < 1:
        await ctx.send('Random float: {number}'.format(number=random.random))
    elif len(args) == 1:
        await ctx.send('Random number from 0 to {number}: {result} '.format(number=args[0], result=random.randint(0, int(args[0]))))
    else:
        await ctx.send('Random number from {} to {}: {}'.format(args[0], args[1], random.randint(args[0], args[1])))

@bot.command()
async def pickone(ctx, *args):
    await ctx.send('Picked \'{}\''.format(random.choice(args)))

@bot.command()
async def updatestats(ctx, *args):
    pull_recent_games(ctx, *args)
    await ctx.send('Updated Games')

@bot.command()
async def stalklol(ctx, *args):
    await build_embed(ctx, *args)
 
with open("bot/auth.json") as f:
    auth = json.load(f)
    bot.run(auth["token"])
    f.close()