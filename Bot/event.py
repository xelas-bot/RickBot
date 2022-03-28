import requests
import json
import time
from collections import Counter
import datetime

SUMMONER_ID = "5g7AofZD7-9SPHDovoqHl-wp3oqD7d3hoKjpxyHCeNTtQOU"
PUUID = "7p-tNgLl0yuLm4LSafNuRtsz2SIpTLdQ5ZW-ril-t5sHMqD6U3hu7XIGWn4UnRoyCCTxCo2nQg5wug"
SUM_NAME = 'dlz9345'
base_na1= "https://na1.api.riotgames.com"
base_americas = 'https://americas.api.riotgames.com'
payload = { 'X-Riot-Token' : 'RGAPI-1d397228-52bc-446c-8263-22abaa0a9ca9'}


champions = base_na1 + "/lol/platform/v3/champion-rotations"
curr_match = base_na1 + "/lol/spectator/v4/active-games/by-summoner/" + SUMMONER_ID

def get_profile_endpoint(id):
   return f'http://ddragon.leagueoflegends.com/cdn/12.5.1/img/profileicon/{id}.png'

def match_list_by_puuid(puuid):
    return base_americas + '/lol/match/v5/matches/by-puuid/{puuid}/ids'.format(puuid = puuid)   

def match_url_by_id(matchid):
    return base_americas + '/lol/match/v5/matches/{matchId}'.format(matchId = matchid)

def profile_info_by_name(sum_name):
    return base_na1 + f'/lol/summoner/v4/summoners/by-name/{sum_name}'

def profile_info_by_id(sum_id):
    return base_na1 + '/lol/summoner/v4/summoners/{encryptedSummonerId}'.format(encryptedSummonerId=sum_id)

def profile_info_ranked(sum_id):
    return base_na1 + f'/lol/league/v4/entries/by-summoner/{sum_id}'

def get_spectator_endpoint(sum_id):
    return base_na1 + '/lol/spectator/v4/active-games/by-summoner/{encryptedSummonerId}'.format(encryptedSummonerId=sum_id)

def pull_profile_info(sum_id=SUMMONER_ID):
    #fix this if you need more users
    f = open('Bot/data/LOLDATA/user_data/users.json')
    p_info = json.load(f)
    f.close()
    p_info[sum_id] = {}
    p_info[sum_id]['prof_info'] = requests.get(profile_info_by_id(sum_id=sum_id), headers=payload).json()
    p_info[sum_id]['ranked_info'] = requests.get(profile_info_ranked(sum_id), headers=payload).json()

    with open('Bot/data/LOLDATA/user_data/users.json', 'w', encoding='utf-8') as f:
        json.dump(p_info, f, ensure_ascii=False, indent=4)

def pull_recent_games(ctx, *args):
    if args:
        f = open('Bot/data/userdata/userdata.json')
        player_info = json.load(f)[str(ctx.author.id)]
        f.close()
    else:
        player_info = {
            'summonerId' : SUMMONER_ID,
            'puuid' : PUUID,
            'summonerName' : SUM_NAME
        }
    pull_profile_info(player_info['summonerId'])
    match_list = {}
    match_list['last-update'] = time.time()
    match_ids = requests.get(match_list_by_puuid(player_info['puuid']), headers=payload).json()
    for match_id in match_ids:
        data = requests.get(match_url_by_id(matchid = match_id), headers=payload).json()
        i = data['metadata']['participants'].index(player_info['puuid'])
        duration = data["info"]["gameDuration"]
        match_start = data["info"]["gameCreation"]
        
        data['info']['participants'][i]["gameDuration"] = float(duration/60)
        data['info']['participants'][i]["gameCreation"] = str(datetime.datetime.fromtimestamp(int(match_start/1000)).strftime('%Y-%m-%d %H:%M:%S'))
        match_list[match_id] = data['info']['participants'][i]
    #maybe store all games in the file for ML
    with open('{puuid}_games.json'.format(puuid=player_info['puuid']), 'w', encoding='utf-8') as f:
        json.dump(match_list, f, ensure_ascii=False, indent=4)
        f.close()

def calculate_general_stats(puuid):
    f = open('{puuid}_games.json'.format(puuid = puuid))
    player_data = json.load(f)
    f.close()
    data = {}
    # There's a better way to do this but I am too lazy to implement it
    data['average_kda'] = sum([player_data[keys]['challenges']['kda'] for keys in list(player_data.keys())[1:]]) / 20
    champs_played = Counter(player_data[key]['championName'] for key in list(player_data.keys())[1:])
    data['most_played_champ'] = max(champs_played, key=champs_played.get)
    data['win_rate'] = sum([int(player_data[keys]['win']) for keys in list(player_data.keys())[1:]]) / 20
    data['average_cpm'] = sum([player_data[keys]['totalMinionsKilled'] / (player_data[keys]['timePlayed'] / 60) for keys in list(player_data.keys())[1:]]) / 20
    roles = Counter(player_data[key]['role'] for key in list(player_data.keys())[1:])
    data['most_played_role'] = max(roles, key=roles.get)
    data['longest_time_alive'] = max([player_data[keys]['longestTimeSpentLiving'] for keys in list(player_data.keys())[1:]])
    data['hd_skillshot_ratio'] = sum([player_data[keys]['challenges']['skillshotsHit'] for keys in list(player_data.keys())[1:]]) / sum([player_data[keys]['challenges']['skillshotsDodged'] for keys in list(player_data.keys())[1:]])

    return data

#pull_recent_games(PUUID)
#d = calculate_general_stats(puuid=PUUID)
#print(d)

import discord

async def build_embed(ctx, *args):
    
    f = open('Bot/data/LOLDATA/user_data/users.json')
    player_data = json.load(f)
    player_info = {}
    if args:
        f = open('Bot/data/userdata/userdata.json')
        player_info = json.load(f)[str(ctx.author.id)]
        f.close()
    else:
        player_info = {
            'summonerId' : SUMMONER_ID,
            'puuid' : PUUID,
            'summonerName' : SUM_NAME
        }
    # summonerV4
    prof_id = player_data[player_info['summonerId']]['prof_info']['profileIconId']
    rank = 'unranked'
    if player_data[player_info['summonerId']]['ranked_info']:
        rank = player_data[player_info['summonerId']]['ranked_info'][1]['tier']
    file_path = f'Bot/data/LOLDATA/icons/emblem_{rank}.png'
    file = discord.File(file_path, filename='rank.png')

    data = calculate_general_stats(player_info['puuid'])
    embed = discord.Embed(title='dlzStats', description='Your last 20 games')
    embed.set_author(name=player_info['summonerName'],icon_url = get_profile_endpoint(prof_id))
    embed.set_thumbnail(url='attachment://rank.png')
    for d in data:
        embed.add_field(name=d, value=data[d], inline=True)
    await ctx.send(file = file, embed=embed)

def get_spectator_info(sum_id=SUMMONER_ID):
    data = requests.get(get_spectator_endpoint(sum_id=sum_id), headers=payload).json()
    # print(data)
    return data