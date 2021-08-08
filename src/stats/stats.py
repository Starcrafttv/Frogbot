import datetime

import data.config as config
import requests
from src.bot.__tokens__ import __tokens__


async def get_last_days(userID: int, username: str, requestedDays: int, guildID: int, raw=False) -> list:
    # Get the timezone from the user id
    response = requests.get(f'{config.base_api_url}discord/user/',
                            params={'id': userID}, headers={'token': __tokens__['frogbot_api']}).json()
    timezone = response['items'][0]['timezone'] if response.get('items') else 0
    # Get all information about the user
    header = {'token': __tokens__['frogbot_api']}
    params = {'userId': userID}
    if guildID:
        params['guildId'] = guildID
    active = [
        [entry['start'] + (timezone * 3600), entry['stop'] - entry['start']]
        for entry in requests.get(
            f'{config.base_api_url}discord/active/',
            params=params,
            headers=header,
        )
        .json()
        .get('items', [])
    ]

    afk = [
        [entry['start'] + (timezone * 3600), entry['stop'] - entry['start']]
        for entry in requests.get(
            f'{config.base_api_url}discord/afk/',
            params=params,
            headers=header,
        )
        .json()
        .get('items', [])
    ]

    messages = [
        entry['sent'] + (timezone * 3600)
        for entry in requests.get(
            f'{config.base_api_url}discord/message/',
            params=params,
            headers=header,
        )
        .json()
        .get('items', [])
    ]

    if raw:
        return [username, timezone, requestedDays, active, afk, messages]
    # Create the return list and calculate the stats for each day
    output = [[userID, username, 0, 0, 0]]
    for i in range(requestedDays):
        output.append([str((datetime.datetime.utcnow() + datetime.timedelta(days=-i, hours=timezone)).date()), 0, 0, 0])
    for entry in active:
        output[0][2] += entry[1]
        for i in range(1, requestedDays+1):
            if output[i][0] == str(datetime.datetime.utcfromtimestamp(entry[0]).date()):
                output[i][1] += entry[1]
    for entry in afk:
        output[0][3] += entry[1]
        for i in range(1, requestedDays+1):
            if output[i][0] == str(datetime.datetime.utcfromtimestamp(entry[0]).date()):
                output[i][2] += entry[1]
    for entry in messages:
        output[0][4] += 1
        for i in range(1, requestedDays+1):
            if output[i][0] == str(datetime.datetime.utcfromtimestamp(entry).date()):
                output[i][3] += 1
    return output
