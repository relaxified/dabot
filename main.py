import aiohttp
import asyncio
import datetime
import db
import discord
import json
import logging
import os

LOG = logging.getLogger("log")
LOG.info("Testing.")


class Bot(discord.Client):
    def __init__(self):
        super().__init__()
        self.EMOJI = dict()
        self.activity = discord.Activity(name='pepega', url='https://www.twitch.tv/relaxified', type=3)
        self.bg_task = self.loop.create_task(self._is_live())
        print(discord.utils.oauth_url(client_id='421387430017368074', permissions=discord.Permissions(1580727376)))
        webhook_url = "https://discordapp.com/api/oauth2/authorize?client_id=421387430017368074" \
                      "&state=00100&redirect_uri=http%3A%2F%2Fgg.relaxified.com%2Factivate%2F" \
                      "&response_type=code&scope=webhook.incoming"
        print(webhook_url)

    async def _is_live(self):
        """Retrieves stream info from https://api.twitch.tv/"""
        api_endpoint = 'https://api.twitch.tv/helix/'
        streamers = ['moonmoon_ow', 'shroud', 'chocotaco', 'sodapoppin', 'ninja', 'DizzyKitten', 'DrDisrespect',
                     'xchocobars', 'lethalfrag']
        headers = {'Client-ID': os.environ['twitch']}
        streamer_url = api_endpoint + "streams?user_login="
        user_url = api_endpoint + "users?login="
        for stream in streamers:
            if stream == streamers[0]:
                streamer_url += stream
                user_url += stream
            else:
                streamer_url += f"&user_login={stream}"
                user_url += f"&login={stream}"
        while True:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(streamer_url) as r:
                    body = await r.json()
                    async with session.get(user_url) as u:
                        user = await u.json()
                    with open(f'twitch/user.json', 'w') as f:
                        json.dump(user, f, indent=4)
                    with open(f'twitch/live_status.json', 'w') as f:
                        json.dump(body, f, indent=4)
                    if body['data']:
                        game_url = api_endpoint + "games?id="
                        for i in body['data']:
                            if i == body['data'][0]:
                                game_url += i['game_id']
                            else:
                                game_url += f"&id={i['game_id']}"
                        async with session.get(game_url) as g:
                            game_info = await g.json()
                            with open(f'twitch/game_info.json', 'w') as f:
                                json.dump(game_info, f, indent=4)
                await session.close()
            await asyncio.sleep(60)

    @staticmethod
    async def _embed():
        webhooks = db.get_webhooks()
        header = {'Content-Type': 'application/json'}
        api_endpoint = 'https://discordapp.com/api/webhooks/'
        box_art = "https://static-cdn.jtvnw.net/ttv-static/404_boxart-188x250.jpg"
        game_name = "?"
        icon_url = ""
        started = dict()
        with open(f'twitch/live_status.json', 'r') as k:
            live_status = json.load(k)
        with open(f'twitch/user.json', 'r') as u:
            user_info = json.load(u)
        with open(f'twitch/game_info.json', 'r') as g:
            game_info = json.load(g)
        with open(f'twitch/started_at.json', 'r') as s:
            started_at = json.load(s)
            started.update(started_at)
        if not live_status['data']:
            return
        for stream in live_status['data']:
            for game in game_info['data']:
                if stream['game_id'] == game['id']:
                    box_art = game['box_art_url'].replace("{width}x{height}", "188x250")
                    game_name = game['name']
            for user in user_info['data']:
                if stream['user_id'] == user['id']:
                    icon_url = user['profile_image_url']
            embeds = {'embeds': []}
            embed = {
                "color": 6570405,
                "author": {
                    "name": f"{stream['user_name']} went live!",
                    "url": f"https://www.twitch.tv/{stream['user_name']}",
                    "icon_url": icon_url
                },
                "title": stream['title'],
                "description": f"[Watch live on Twitch!](https://www.twitch.tv/{stream['user_name']})",
                "fields": [
                    {
                        "name": "Playing",
                        "value": game_name,
                        "inline": True
                    },
                    {
                        "name": "Viewers",
                        "value": stream['viewer_count'],
                        "inline": True
                    }
                ],
                "thumbnail": {
                    "url": box_art
                },
                "image": {
                    "url": stream['thumbnail_url'].replace("{width}x{height}", "1920x1080")
                }
            }
            embeds['embeds'].append(embed)
            if stream['user_name'] not in started_at or\
                    stream['started_at'] != started_at[stream['user_name']]['started_at']:
                async with aiohttp.ClientSession(headers=header) as session:
                    for hook in webhooks:
                        url = f"{api_endpoint}{hook[0]}/{hook[1]}"
                        async with session.post(url, json=embeds) as resp:
                            response = await resp.text()
                            try:
                                response = json.loads(response)
                                if 'code' in response and response['code'] == 10015:
                                    db.del_webhook(hook[0], hook[1])
                            except json.JSONDecodeError as e:
                                pass
                    await session.close()
                started.update({stream['user_name']: {'started_at': stream['started_at']}})
                with open('twitch/started_at.json', 'w') as s:
                    json.dump(started, s, indent=4)

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

        if message.content.startswith("--embed"):
            await self._embed()

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
        # TODO finish role assignment with reactions
        msg = message.content.split()
        emojis = list()
        roles = list()
        print(message.content)
        embed = discord.Embed(color=discord.Color.green(), title="Select your role!")

        def check(m):
            return m.channel == message.channel and m.author == message.author

        await message.channel.send("Type the emoji with the role you want to use.\n eg.\n"
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
        channel = self.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        guild = msg.guild
        member = guild.get_member(payload.user_id)
        info = db.retrieve(guild.id, payload.message_id, payload.emoji.name)
        if info is not None and info[1] == guild.id and info[2] == payload.message_id and info[4] == payload.emoji.name:
            role = guild.get_role(info[3])
            if role is None:
                return await channel.send(f"Could not find a role with the id: {info[3]}.")
            if role not in member.roles:
                await member.add_roles(role)
            else:
                await member.remove_roles(role)
            await msg.remove_reaction(payload.emoji, member)


if __name__ == "__main__":
    TOKEN = os.environ["DiscordToken"]
    start = Bot()
    start.run(TOKEN)
