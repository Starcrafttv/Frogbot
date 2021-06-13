import os
import sqlite3 as sql

if os.path.isfile('database.db'):
    os.remove('database.db')

connection = sql.connect('database.db')
cursor = connection.cursor()


print('Creating new database ...')
with connection:
    # bot stats table
    cursor.execute('CREATE TABLE botStats'
                   ' ('
                   'Date VARCHAR(16) NOT NULL UNIQUE,'
                   'Guilds INTEGER,'
                   'CommandsUsed INTEGER,'
                   'PRIMARY KEY (Date)'
                   ')')

    # discord active table
    cursor.execute('CREATE TABLE discordActive'
                   ' ('
                   'UserID INTEGER NOT NULL,'
                   'GuildID INTEGER,'
                   'ChannelID INTEGER,'
                   'Start TIMESTAMP NOT NULL,'
                   'Stop TIMESTEMP NOT NULL,'
                   'FOREIGN KEY (GuildID) REFERENCES guilds(GuildID),'
                   'FOREIGN KEY (UserID) REFERENCES users(UserID)'
                   ')')

    # discord afk table
    cursor.execute('CREATE TABLE discordAfk'
                   ' ('
                   'UserID INTEGER NOT NULL,'
                   'GuildID INTEGER,'
                   'ChannelID INTEGER,'
                   'Start TIMESTAMP NOT NULL,'
                   'Stop TIMESTEMP NOT NULL,'
                   'FOREIGN KEY (GuildID) REFERENCES guilds(GuildID),'
                   'FOREIGN KEY (UserID) REFERENCES users(UserID)'
                   ')')
    # discord messages table
    cursor.execute('CREATE TABLE discordMessages'
                   ' ('
                   'UserID INTEGER NOT NULL,'
                   'GuildID INTEGER,'
                   'ChannelID INTEGER,'
                   'Send TIMESTAMP NOT NULL,'
                   'FOREIGN KEY (GuildID) REFERENCES guilds(GuildID),'
                   'FOREIGN KEY (UserID) REFERENCES users(UserID)'
                   ')')
    # dms Table
    cursor.execute('CREATE TABLE dms'
                   ' ('
                   'UserID INTEGER PRIMARY KEY NOT NULL,'
                   'ChannelID INTEGER NOT NULL,'
                   'FOREIGN KEY (UserID) REFERENCES users(UserID)'
                   ')')
    # Guilds table
    cursor.execute('CREATE TABLE guilds'
                   ' ('
                   'GuildID INTEGER NOT NULL UNIQUE,'
                   'Prefix VARCHAR(32) DEFAULT \'!\','
                   'GuildPrivileges INTEGER(8) DEFAULT 0,'
                   'MusicChannelId INTEGER DEFAULT 0,'
                   'Volume INTEGER DEFAULT 50,'
                   'Timeout INTEGER DEFAULT 300,'
                   'ReqRole INTEGER DEFAULT 0,'
                   'PRIMARY KEY (GuildID)'
                   ')')
    # lol table
    cursor.execute('CREATE TABLE leagueOfLegends'
                   ' ('
                   'SummonerPUUID VARCHAR(128) NOT NULL UNIQUE,'
                   'SummonerName VARCHAR(32) NOT NULL,'
                   'DiscordID INTEGER NOT NULL,'
                   'Region VARCHAR(8) NOT NULL,'
                   'FOREIGN KEY (DiscordID) REFERENCES users(UserID)'
                   ')')
    # Playlist Table
    cursor.execute('CREATE TABLE playlists'
                   ' ('
                   'PlaylistID INTEGER PRIMARY KEY NOT NULL,'
                   'PlaylistName VARCHAR(32),'
                   'CreatorID INTEGER NOT NULL,'
                   'FOREIGN KEY (CreatorID) REFERENCES users(UserID)'
                   ')')
    # Playlist connection table
    cursor.execute('CREATE TABLE playlistsConnection'
                   ' ('
                   'PlaylistID INTEGER NOT NULL,'
                   'GuildID INTEGER NOT NULL,'
                   'FOREIGN KEY (GuildID) REFERENCES guilds(GuildID),'
                   'FOREIGN KEY (PlaylistID) REFERENCES playlists(PlaylistID)'
                   ')')

    # User Table
    cursor.execute('CREATE TABLE users'
                   ' ('
                   'UserID INTEGER NOT NULL UNIQUE,'
                   'UserPrivileges INTEGER(8) DEFAULT 0,'
                   'Timezone INTEGER(8) DEFAULT 0,'
                   'PRIMARY KEY (UserID)'
                   ')')


print('DONE')
