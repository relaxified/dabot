import datetime
import discord
import logging
import os

from lib import strawpoll, twitch, xivapi

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

# Log file name
logging.basicConfig(filename=f'logs.log')

# Logging level
logLevel = logging.DEBUG

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

msgLogger = logging.getLogger('messages')
msgLogger.setLevel(logLevel)

ch = logging.StreamHandler()
ch.setLevel(logLevel)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch.setFormatter(formatter)

logger.addHandler(ch)
msgLogger.addHandler(ch)

twitchActive = False


class Bot(discord.Client):
    def __init__(self):
        super().__init__()
        self.EMOJI = dict()
        self.activity = discord.Activity(name='pepega', type=5)
        self.bg_task = None
        twitch.required_files()
        webhook_url = f"https://discordapp.com/api/oauth2/authorize?client_id={CLIENT_ID}" \
                      "&state=00100&redirect_uri=http%3A%2F%2Fgg.relaxified.com%2Factivate%2F" \
                      "&response_type=code&scope=webhook.incoming"
        logger.debug(discord.utils.oauth_url(client_id=CLIENT_ID, permissions=discord.Permissions(1580727376)))
        logger.debug(webhook_url)

    async def on_ready(self):
        logger.info(f'Logged in as: {self.user}')
        if twitchActive:
            logger.info('Starting Twitch listener')
            self.bg_task = self.loop.create_task(twitch.fetch())
            logger.info('Twitch listener started')
        logger.info('Listening for commands...')

    async def on_message(self, message):
        msgLogger.info(f'Server: {message.guild} / Channel: {message.channel}\n{message.author}: {message.content}')

        if message.author.id == self.user.id:
            return

        if message.content.startswith("--help"):
            """
            Send a list of commands.
            Usage:
                --help <optional: command>
            Permissions:
                read_message_history
                send_messages
            """
            msg = message.content.split()
            content = discord.Embed(color=16776960)

            if len(msg) < 2:
                content.title = "Commands"
                content.add_field(
                    name="--help <command>",
                    value="Show command usage.",
                    inline=False
                )
                content.add_field(
                    name="--avatar",
                    value="Retrieve a users avatar.",
                    inline=False
                )
                content.add_field(
                    name="--poll",
                    value="Creates a StrawPoll.",
                    inline=False
                )
                content.add_field(
                    name="--itemsearch",
                    value="Retrieve item information from XIVAPI.",
                    inline=False
                )

                return await message.channel.send(embed=content)

            elif msg[1].lower() == "avatar":
                content.title = "--avatar"
                content.description = "Retrieve a users avatar."
                content.add_field(
                    name="Usage:",
                    value="--avatar <user> or <userid>"
                )

                return await message.channel.send(embed=content)

            elif msg[1].lower() == "poll":
                content.title = "--poll"
                content.description = "Creates a StrawPoll."
                content.add_field(
                    name="Usage:",
                    value="--poll <question> <choice1> <choice2>\n"
                          "Question and choices must be within quotations.\n"
                          "Must have at least 2 choices."
                )

                return await message.channel.send(embed=content)

            elif msg[1].lower() == "itemsearch":
                content.title = "--itemsearch"
                content.description = "Retrieve item information from XIVAPI."
                content.add_field(
                    name="Usage:",
                    value="--itemsearch <itemname>"
                )

                return await message.channel.send(embed=content)

            else:
                return await message.channel.send("Something went wrong!")

        if message.content.startswith("--avatar"):
            """
            Retrieve a users avatar from Discord servers.
            Usage:
                --avatar [id]
            Permissions:
                read_message_history
                send_messages
            """
            msg = message.content.split()

            if len(msg) < 2:
                return await message.channel.send("You must provide a user id or @user")

            # Checks if a user is mentioned before checking the message content for a user id
            if message.mentions:
                user = message.mentions[0]
            else:
                # if a user isn't mentioned, tries to retrieve a user from id provided, if valid
                try:
                    user = self.get_user(int(msg[1]))
                except ValueError:
                    return await message.channel.send("You must provide a user id or @user")

            # Checks if user is None, if true, searches Discord for user id provided
            if user is None:
                try:
                    user = await self.fetch_user(int(msg[1]))
                except discord.errors.NotFound:
                    return await message.channel.send("User not found.")

            await message.channel.send(user.avatar_url)

        if message.content.startswith("--poll"):
            """
            Create a StrawPoll.
            Usage:
                --poll <question> <answer1> <answer2> <etc>
            Permissions:
                read_message_history
                send_messages
            """
            url = await strawpoll.poll(message)

            await message.channel.send(url)

        if message.content.startswith("--itemsearch"):
            """
            Retrieve information from XIVAPI.
            Usage:
                --itemsearch <itemname>
            Permissions:
                read_message_history
                send_messages
            """
            msg = message.content.split("--itemsearch ")
            content = discord.Embed(
                color=discord.Colour.random()
            )

            result = await xivapi.fetch_item(msg[1])
            logger.debug(result)

            if result is not False:
                content.title = result['Results'][0]['Name']
                content.set_thumbnail(url=f"https://xivapi.com/{result['Results'][0]['Icon']}")
                content.add_field(
                    name="Item Level",
                    value=result['Results'][0]['LevelItem'],
                    inline=False
                )

                await message.channel.send(embed=content)
            else:
                await message.channel.send(f"Could not find \"{msg[1]}\".")

        if message.author.id not in [49291953782657024, 421387430017368074]:
            return

        if message.content.startswith("--streams"):
            await twitch.stream(message)

        if message.content.startswith("--kill"):
            """Kills the bot."""
            await self.close()


if __name__ == "__main__":
    TOKEN = os.environ["CLIENT_TOKEN"]
    start = Bot()
    start.run(TOKEN)
