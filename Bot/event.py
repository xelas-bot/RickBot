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
        match_list[match_id] = data['info']['participants'][i]
    with open('{puuid}_games.json'.format(puuid=puuid), 'w', encoding='utf-8') as f:
        json.dump(match_list, f, ensure_ascii=False, indent=4)

pull_recent_games(PUUID)