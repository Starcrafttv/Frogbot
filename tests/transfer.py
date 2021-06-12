import datetime
import os
import sqlite3 as sql
import time

if os.path.isfile('database.db'):
    os.remove('database.db')

new_conn = sql.connect('database.db')
new_c = new_conn.cursor()


print("Creating new database ...")
with new_conn:
    new_c.execute("PRAGMA foreign_keys = ON;")
    # bot stats table
    new_c.execute("CREATE TABLE botStats ("
                  "Date VARCHAR(16) NOT NULL UNIQUE,"
                  "Guilds INTEGER,CommandsUsed INT,"
                  "PRIMARY KEY (Date))")
    # discord active table
    new_c.execute("CREATE TABLE discordActive ("
                  "UserID VARCHAR(32) NOT NULL,"
                  "GuildID VARCHAR(32),"
                  "ChannelID VARCHAR(32),"
                  "Start TIMESTAMP NOT NULL,"
                  "Stop TIMESTEMP NOT NULL,"
                  "FOREIGN KEY (GuildID) REFERENCES guilds(GuildID),"
                  "FOREIGN KEY (UserID) REFERENCES users(UserID))")
    # discord afk table
    new_c.execute("CREATE TABLE discordAfk ("
                  "UserID VARCHAR(32) NOT NULL,"
                  "GuildID VARCHAR(32),"
                  "ChannelID VARCHAR(32),"
                  "Start TIMESTAMP NOT NULL,"
                  "Stop TIMESTEMP NOT NULL,"
                  "FOREIGN KEY (GuildID) REFERENCES guilds(GuildID),"
                  "FOREIGN KEY (UserID) REFERENCES users(UserID))")
    # discord messages table
    new_c.execute("CREATE TABLE discordMessages ("
                  "UserID VARCHAR(32) NOT NULL,"
                  "GuildID VARCHAR(32),"
                  "ChannelID VARCHAR(32),"
                  "Send TIMESTAMP NOT NULL,"
                  "FOREIGN KEY (GuildID) REFERENCES guilds(GuildID),"
                  "FOREIGN KEY (UserID) REFERENCES users(UserID))")
    # Guilds table
    new_c.execute("CREATE TABLE guilds ("
                  "GuildID VARCHAR(32) NOT NULL UNIQUE,"
                  "Prefix VARCHAR(32) DEFAULT '!',"
                  "GuildPrivileges INTEGER(8) DEFAULT 0,"
                  "MusicChannelId INTEGER DEFAULT 0,"
                  "Volume INTEGER DEFAULT 50,"
                  "Timeout INTEGER DEFAULT 300,"
                  "ReqRole INTEGER DEFAULT 0,"
                  "PRIMARY KEY (GuildID))")
    # lol table
    new_c.execute("CREATE TABLE leagueOfLegends ("
                  "SummonerPUUID VARCHAR(128) NOT NULL UNIQUE,"
                  "SummonerName VARCHAR(32) NOT NULL,"
                  "DiscordID VARCHAR(32) NOT NULL,"
                  "Region VARCHAR(8) NOT NULL,"
                  "FOREIGN KEY (DiscordID) REFERENCES users(UserID))")
    # User Table
    new_c.execute("CREATE TABLE users ("
                  "UserID VARCHAR(32) NOT NULL UNIQUE,"
                  "UserPrivileges INTEGER(8) DEFAULT 0,"
                  "Timezone INTEGER(8) DEFAULT 0,"
                  "PRIMARY KEY (UserID))")

    # Playlist Table
    new_c.execute("CREATE TABLE playlists ("
                  "PlaylistID INTEGER PRIMARY KEY NOT NULL,"
                  "PlaylistName VARCHAR(32),"
                  "CreatorID VARCHAR(32),"
                  "FOREIGN KEY (CreatorID) REFERENCES users(UserID))")

    new_c.execute("CREATE TABLE playlistsConnection ("
                  "PlaylistID INTEGER PRIMARY KEY NOT NULL,"
                  "GuildID VARCHAR(32),"
                  "FOREIGN KEY (GuildID) REFERENCES guilds(GuildID),"
                  "FOREIGN KEY (PlaylistID) REFERENCES playlists(PlaylistID))")

    # dms Table
    new_c.execute("CREATE TABLE dms ("
                  "UserID VARCHAR(32) PRIMARY KEY NOT NULL,"
                  "ChannelID VARCHAR(32),"
                  "FOREIGN KEY (UserID) REFERENCES users(UserID))")


"""
old_conn = sql.connect('databaseold.db')
old_c = old_conn.cursor()

print("Starting transfer...")

start = time.time()
# Write all users from old to new database
old_c.execute("SELECT UserID, UserPrivileges, Timezone FROM users")
for user in old_c.fetchall():
    with new_conn:
        new_c.execute(f"INSERT INTO users (UserID, Timezone) VALUES ('{user[0]}', {int(user[2])})")
print("1. Finished: users in " + str(round(time.time()-start, 2)))
start = time.time()

start = time.time()
# Write all activetimes from old to new database
old_c.execute("SELECT UserID, GuildID, Start, Stop FROM discordActive")
for user in old_c.fetchall():
    with new_conn:
        new_c.execute(
            f"INSERT INTO discordActive (UserID, GuildID, Start, Stop) VALUES ('{str(user[0])}', '{str(user[1])}', {int(user[2])},  {int(user[3])})")
print("2. Finished: active in " + str(round(time.time()-start, 2)))
start = time.time()

start = time.time()
# Write all afktimes from old to new database
old_c.execute("SELECT UserID, GuildID, Start, Stop FROM discordAfk")
for user in old_c.fetchall():
    with new_conn:
        new_c.execute(
            f"INSERT INTO discordAfk (UserID, GuildID, Start, Stop) VALUES ('{str(user[0])}', '{str(user[1])}', {int(user[2])},  {int(user[3])})")
print("3. Finished: afk in " + str(round(time.time()-start, 2)))
start = time.time()

start = time.time()
# Write all messages from old to new database
old_c.execute("SELECT UserID, GuildID, Send FROM discordMessages")
for user in old_c.fetchall():
    with new_conn:
        new_c.execute(
            f"INSERT INTO discordMessages (UserID, GuildID, Send) VALUES ('{str(user[0])}', '{str(user[1])}', {int(user[2])})")
print("4. Finished: messages in " + str(round(time.time()-start, 2)))
start = time.time()

"""
print("DONE")
