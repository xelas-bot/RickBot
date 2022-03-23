import requests

SUMMONER_ID = "5g7AofZD7-9SPHDovoqHl-wp3oqD7d3hoKjpxyHCeNTtQOU"
PUUID = "7p-tNgLl0yuLm4LSafNuRtsz2SIpTLdQ5ZW-ril-t5sHMqD6U3hu7XIGWn4UnRoyCCTxCo2nQg5wug"


print("hello")
base= "https://na1.api.riotgames.com"
payload = { 'api_key' : 'RGAPI-1d397228-52bc-446c-8263-22abaa0a9ca9'}

champions = base + "/lol/platform/v3/champion-rotations"
curr_match = base + "/lol/spectator/v4/active-games/by-summoner/" + SUMMONER_ID
response = requests.get(curr_match,params=payload)
print(response.json())