import datetime
import discord
import os

from lib import strawpoll, twitch

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']


class Bot(discord.Client):
    def __init__(self):
        super().__init__()
        self.EMOJI = dict()
        self.activity = discord.Activity(name='pepega', type=3)
        self.bg_task = None
        # TODO Fix Twitch api access
        # twitch.required_files()
        print(discord.utils.oauth_url(client_id=CLIENT_ID, permissions=discord.Permissions(1580727376)))
        webhook_url = f"https://discordapp.com/api/oauth2/authorize?client_id={CLIENT_ID}" \
                      "&state=00100&redirect_uri=http%3A%2F%2Fgg.relaxified.com%2Factivate%2F" \
                      "&response_type=code&scope=webhook.incoming"
        print(webhook_url)

    async def on_ready(self):
        print(f"Logged in as: {self.user}")
        # TODO Fix Twitch api access
        # print("Starting Twitch listener.")
        # self.bg_task = self.loop.create_task(twitch.fetch())
        print("Listening for commands...")

    async def on_message(self, message):
        now = datetime.datetime.now()
        timestamp = datetime.datetime.time(now)
        print(f"{timestamp}\nGuild: {message.guild} - Channel: {message.channel}\n{message.author}: {message.content}")

        if message.content.startswith("--avatar"):
            msg = message.content.split()
            user = self.get_user(int(msg[1]))
            await message.channel.send(user.avatar_url)

        if message.content.startswith("--poll"):
            url = await strawpoll.poll(message)
            await message.channel.send(url)

        if message.author.id not in [49291953782657024, 421387430017368074]:
            return

        if message.content.startswith("--streams"):
            await twitch.stream(message)

        if message.content.startswith("--kill"):
            """Kills the bot."""
            await self.close()


if __name__ == "__main__":
    TOKEN = os.environ["DiscordToken"]
    start = Bot()
    start.run(TOKEN)
