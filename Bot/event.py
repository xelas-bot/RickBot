import requests

SUMMONER_ID = "5g7AofZD7-9SPHDovoqHl-wp3oqD7d3hoKjpxyHCeNTtQOU"
PUUID = "7p-tNgLl0yuLm4LSafNuRtsz2SIpTLdQ5ZW-ril-t5sHMqD6U3hu7XIGWn4UnRoyCCTxCo2nQg5wug"


print("hello")
base_na1= "https://na1.api.riotgames.com"
base_americas = 'https://americas.api.riotgames.com'
payload = { 'X-Riot-Token' : 'RGAPI-1d397228-52bc-446c-8263-22abaa0a9ca9'}

champions = base_na1 + "/lol/platform/v3/champion-rotations"
curr_match = base_na1 + "/lol/spectator/v4/active-games/by-summoner/" + SUMMONER_ID

def match_list_by_puuid(puuid):
    return base_americas + '/lol/match/v5/matches/by-puuid/{puuid}/ids'.format(puuid = puuid)   

def match_url_by_id(matchid):
    return base_americas + '/lol/match/v5/matches/{matchId}'.format(matchId = matchid)

#response = requests.get(match_list_by_puuid(PUUID), headers=payload)
#print(response.json())
#latest_match = response.json()
#m = requests.get(match_url_by_id(matchid= latest_match), headers=payload)
#print(m.json())

#import json
#with open('sampledata.json', 'w', encoding='utf-8') as f:
#    json.dump(m.json(), f, ensure_ascii=False, indent=4)

import json
import time
import datetime

#f = open('sampledata.json')

#data = json.load(f)

#f.close()
#i = data['metadata']['participants'].index(PUUID)
#print(i)
#playerdata = data['info']['participants'][i]
#kda = (playerdata['kills'] + playerdata['assists']) / playerdata['deaths']
#print('{kda:.2f}:1'.format(kda=kda))

def pull_recent_games(puuid):
    match_list = {}
    match_list['last-update'] = time.time()
    match_ids = requests.get(match_list_by_puuid(puuid), headers=payload).json()
    for match_id in match_ids:
        data = requests.get(match_url_by_id(matchid = match_id), headers=payload).json()
        i = data['metadata']['participants'].index(PUUID)
        duration = data["info"]["gameDuration"]
        match_start = data["info"]["gameCreation"]
        
        data['info']['participants'][i]["gameDuration"] = float(duration/60)
        data['info']['participants'][i]["gameCreation"] = str(datetime.datetime.fromtimestamp(int(match_start/1000)).strftime('%Y-%m-%d %H:%M:%S'))
        match_list[match_id] = data['info']['participants'][i]
    #maybe store all games in the file for ML
    with open('{puuid}_games.json'.format(puuid=puuid), 'w', encoding='utf-8') as f:
        json.dump(match_list, f, ensure_ascii=False, indent=4)

def calculate_general_stats(puuid):
    f = open('{puuid}_games.json'.format(puuid = puuid))
    player_data = json.load(f)
    data = {}
    
    # There's a better way to do this but I am too lazy to implement it
    data['average_kda'] = sum([player_data[keys]['challenges']['kda'] for keys in list(player_data.keys())[1:]]) / 20
    champs_played = {}
    champs_played = {player_data[key]['championName'] : champs_played['championName'] + 1 if player_data[key]['championName'] in champs_played else 1 for key in list(player_data.keys())[1:]}
    data['most_played_champ'] = max(champs_played, key=champs_played.get)
    data['win_rate'] = sum([int(player_data[keys]['win']) for keys in list(player_data.keys())[1:]]) / 20
    data['average_cpm'] = sum([player_data[keys]['totalMinionsKilled'] / (player_data[keys]['timePlayed'] / 60) for keys in list(player_data.keys())[1:]]) / 20
    roles = {}
    roles = {player_data[key]['role'] : champs_played['role'] + 1 if player_data[key]['role'] in champs_played else 1 for key in list(player_data.keys())[1:]}
    data['most_played_role'] = max(roles, key=roles.get)
    data['longest_time_alive'] = max([player_data[keys]['longestTimeSpentLiving'] for keys in list(player_data.keys())[1:]])

    return data

pull_recent_games(PUUID)
d = calculate_general_stats(puuid=PUUID)
print(d)