from time import time


class Active():
    def __init__(self, user_id: int, channel_id: int, guild_id: int):
        self.__user_id = user_id
        self.__channel_id = channel_id
        self.__guild_id = guild_id
        self.__start = time()
        self.__stop = None

    def setStart(self):
        self.__start = time()

    def save(self, conn, c):
        self.__stop = time()
        with conn:
            c.execute(
                f"INSERT INTO discordActive (UserID, GuildID, ChannelID, Start, Stop) VALUES ('{self.__user_id}', '{self.__guild_id}', '{self.__channel_id}', {self.__start}, {self.__stop})")


class Afk():
    def __init__(self, user_id: int, channel_id: int, guild_id: int):
        self.__user_id = user_id
        self.__channel_id = channel_id
        self.__guild_id = guild_id
        self.__start = time()
        self.__stop = None

    def setStart(self):
        self.__start = time()

    def save(self, conn, c):
        self.__stop = time()
        with conn:
            c.execute(
                f"INSERT INTO discordAfk (UserID, GuildID, ChannelID, Start, Stop) VALUES ('{self.__user_id}', '{self.__guild_id}', '{self.__channel_id}', {self.__start}, {self.__stop})")


def saveMessage(user_id, channel_id, guild, conn, c):
    with conn:
        c.execute(
            f"INSERT INTO discordMessages (UserID, GuildID, ChannelID, Send) VALUES ('{user_id}', '{guild.id if guild else ''}', '{channel_id}', {time()})")
