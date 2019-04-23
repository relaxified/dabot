import aiohttp
import asyncio
import datetime
import db
import discord
import os


class Bot(discord.Client):
    def __init__(self):
        super().__init__()
        self.EMOJI = dict()
        self.activity = discord.Activity(name='pepega', url='https://www.twitch.tv/relaxified', type=3)
        self.is_live = False

    async def _is_live(self):
        """Retrieves stream info from https://api.twitch.tv/"""
        url = 'https://api.twitch.tv/helix/streams?user_id=190784496'
        headers = {'Client-ID': os.environ['twitch']}
        channel = self.get_channel(422321550973206529)
        while True:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as r:
                    body = await r.json()
                    if len(body['data'][0]) > 0:
                        if 'type' in body['data'][0]:
                            info = body['data'][0]
                            print(body['data'])
                            embed = discord.Embed(type="rich", title=info['title'], color=discord.Color.purple())
                            img_url = info['thumbnail_url'].split("{")
                            img_url[0] += "1920x1080.jpg"
                            embed.set_image(url=img_url[0])
                            embed.add_field(name='Playing', value=info['game_id'])
                            embed.add_field(name='Started at', value=info['started_at'])
                            if not self.is_live:
                                await channel.send(embed=embed)
                                self.is_live = True
                    else:
                        self.is_live = False
                    print(self.is_live)
                await session.close()
            await asyncio.sleep(60)

    async def _react(self, message):
        """Reacts to a designated message with [emoji id].
            Usage:
                --react [message id] [emoji id/name]
                --react 567801448776204298 491068441495863297
            Permissions:
                read_message_history
                add_reactions
        """
        msg = message.content.split()
        await message.delete()
        if len(msg) < 2:
            return
        message.id = msg[1]
        if len(msg) < 3:
            await message.add_reaction(emoji=self.get_emoji(self.EMOJI['praisesun']))
        else:
            for k, v in self.EMOJI.items():
                if msg[2] in k or msg[2] in str(v):
                    await message.add_reaction(emoji=self.get_emoji(self.EMOJI[k]))

    async def _activity(self, message):
        """Changes the bots activity.
        Usage:
            --activity [title|type|url] [string|activity|twitch_url]
            --activity title Hello World
            --activity type 0
            --activity url https://www.twitch.tv/relaxified
        Activity:
            unknown = -1
            playing = 0
            streaming = 1
            listening = 2
            watching = 3
        """
        msg = message.content.split()
        activity = discord.Activity()
        await message.delete()
        if len(msg) < 3:
            return
        if "title" in msg:
            activity.name = msg[2]
        if "url" in msg:
            activity.url = msg[2]
        if "type" in msg:
            if msg[2].lower() == "playing" or msg[2] == "0":
                active_type = discord.ActivityType.playing
            elif msg[2].lower() == "streaming" or msg[2] == "1":
                active_type = discord.ActivityType.streaming
            elif msg[2].lower() == "listening" or msg[2] == "2":
                active_type = discord.ActivityType.listening
            elif msg[2].lower() == "watching" or msg[2] == "3":
                active_type = discord.ActivityType.watching
            else:
                active_type = discord.ActivityType.unknown
            activity.type = active_type
        await self.change_presence(activity=activity)

    async def on_ready(self):
        # self.bg_task = self.loop.create_task(self._is_live())
        print(f"Logged in as: {self.user}")
        print("Writing emojis to a txt file")
        with open('emoji.txt', 'w') as r:
            for i in self.emojis:
                r.write(str(i)+"\n")
        print("Putting emojis into a dictionary")
        for i in self.emojis:
            self.EMOJI[i.name] = i.id
        print("Listening for commands...")

    async def on_message(self, message):
        now = datetime.datetime.now()
        timestamp = datetime.datetime.time(now)
        print(f"{timestamp}\nGuild: {message.guild} - Channel: {message.channel}\n{message.author}: {message.content}")

        if message.author.id == 49291601729556480:  # Artorias (Void)
            await message.add_reaction(self.get_emoji(self.EMOJI['praisesun']))
        elif message.author.id == 79232736220422144:  # Mimi
            await message.add_reaction(self.get_emoji(self.EMOJI['pepega']))

        if message.content.startswith("--react"):
            await self._react(message)

        if message.content.startswith("--avatar"):
            msg = message.content.split()
            user = self.get_user(int(msg[1]))
            await message.channel.send(user.avatar_url)

        if message.author.id not in [49291953782657024, 421387430017368074]:
            return

        if message.content.startswith("--split"):
            print(f"{message.content.split(':')}")

        if message.content.startswith("--activity"):
            await self._activity(message)

        if message.content.startswith("--role"):
            msg = message.content.split()
            if msg[1].lower() == "add" or msg[1].lower() == "remove":
                await self.add_remove_role(message)
            elif msg[1].lower() == "reaction":
                await self.embed_role_reaction(message)

        if message.content.startswith("--kill"):
            """Kills the bot."""
            await message.delete()
            return await self.close()

    @staticmethod
    async def add_remove_role(message):
        """Adds or removes a role from a Member."""
        msg = message.content.split()
        member = message.guild.get_member(int(msg[2]))
        if msg[1].lower() == "remove":
            for role in message.guild.roles:
                if role.name == msg[3]:
                    await member.remove_roles(role)
        elif msg[1].lower() == "add":
            for role in message.guild.roles:
                if role.name == msg[3]:
                    await member.add_roles(role)

    async def embed_role_reaction(self, message):
        msg = message.content.split()
        emojis = list()
        roles = list()
        # msg_id = int(msg[2])
        # for role in message.guild.roles:
        #     if role == msg[3]:
        #         role = role
        print(message.content)
        embed = discord.Embed(color=discord.Color.green(), title="Select your role!")

        def check(m):
            print(m.channel == message.channel and m.author == message.author)
            return m.channel == message.channel and m.author == message.author

        await message.channel.send("Type the emojis with the roles you want to use.\n eg.\n"
                                   "```To get a role id, type \\@role\n:emoji: role_id```")
        reply = await self.wait_for('message', check=check)
        for text in reply.content.split():
            for e in message.guild.emojis:
                if text == str(e):
                    emojis.append(text)
            for r in message.guild.roles:
                for mention in reply.role_mentions:
                    if mention == r:
                        print(mention, r)
                        roles.append(r)
        embed.add_field(name="Roles", value=reply.content)
        await message.channel.send(embed=embed)

    async def on_raw_reaction_add(self, payload):
        print(payload.channel_id, payload.message_id, payload.emoji)
        channel = self.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        guild = msg.guild
        member = guild.get_member(payload.user_id)
        info = db.retrieve(guild.id, payload.message_id)
        if info is not None and info[1] == guild.id and info[2] == payload.message_id:
            role = guild.get_role(info[4])
            if role is None:
                return
            if role not in member.roles:
                await member.add_roles(role)
            else:
                await member.remove_roles(role)
            await msg.remove_reaction(payload.emoji, member)

    async def on_guild_role_create(self, role):
        print(role)

    async def on_guild_role_delete(self, role):
        print(role)

    async def on_guild_role_update(self, before, after):
        print(before, before.id, after, after.id)


if __name__ == "__main__":
    TOKEN = os.environ["TOKEN"]
    start = Bot()
    start.run(TOKEN)
