import datetime


def get_last_days(c, userID: int, username: str, requestedDays: int, guildID: int, raw=False) -> list:
    # Get the timezone from the user id
    c.execute(f"SELECT Timezone FROM users WHERE UserID = '{userID}'")
    timezone = c.fetchone()[0]
    # Create a string if a guild is specified
    GuildString = f" AND GuildID = '{guildID}'" if guildID else ""
    # Get all information about the user
    c.execute(f"SELECT Start, Stop FROM discordActive WHERE UserID = '{userID}'" + GuildString)
    active = [[entry[0]+(timezone*3600), entry[1]-entry[0]] for entry in c.fetchall()]
    c.execute(f"SELECT Start, Stop FROM discordAfk WHERE UserID = '{userID}'" + GuildString)
    afk = [[entry[0]+(timezone*3600), entry[1]-entry[0]] for entry in c.fetchall()]
    c.execute(f"SELECT Send FROM discordMessages WHERE UserID = '{userID}'" + GuildString)
    messages = [entry[0]+(timezone*3600) for entry in c.fetchall()]
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


def sec_to_time(sec):
    # Convert seconds to a normalized string
    m, s = divmod(round(sec), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if d > 1:
        if s < 10:
            s = f'0{s}'
        if m < 10:
            m = f'0{m}'
        return f'{d} days, {h}:{m}:{s}'
    elif d == 1:
        if s < 10:
            s = f'0{s}'
        if m < 10:
            m = f'0{m}'
        return f'{d} day, {h}:{m}:{s}'
    elif h > 0:
        if s < 10:
            s = f'0{s}'
        if m < 10:
            m = f'0{m}'
        return f'{h}:{m}:{s}'
    elif m > 0:
        if s < 10:
            s = f'0{s}'
        return f'{m}:{s}'
    else:
        return f'{s}'
