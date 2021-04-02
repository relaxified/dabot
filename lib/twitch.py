import aiohttp
import asyncio
import json
import logging
import os
import random

from lib import database

TWITCH_ID = os.environ['TWITCH_ID']
TWITCH_BEARER = os.environ['TWITCH_BEARER']

logger = logging.getLogger('__main__')


def required_files():
    try:
        f = open("twitch/streams.json", "r")
        f.close()
    except FileNotFoundError:
        f = open("twitch/streams.json", "w")
        f.write('{"streams": []}')
    try:
        f = open("twitch/started_at.json", "r")
        f.close()
    except FileNotFoundError:
        f = open("twitch/started_at.json", "w")
        f.write('{}')


async def fetch():
    """Retrieves stream info from https://api.twitch.tv/
     and saves the information to file in json format."""
    headers = {'Authorization': f'Bearer {TWITCH_BEARER}', 'Client-ID': TWITCH_ID}
    while True:
        api_endpoint = 'https://api.twitch.tv/helix/'
        streamer_url = f'{api_endpoint}streams?user_login='
        user_url = f'{api_endpoint}users?login='
        game_url = f'{api_endpoint}games?id='

        # open streams file and saves info to variable
        with open(f'twitch/streams.json', 'r') as f:
            streams = json.load(f)

        # creates url for fetching data with
        if streams != {'streams'}:
            for streamer in streams['streams']:
                if streamer == streams['streams'][0]:
                    streamer_url += streamer
                    user_url += streamer
                else:
                    streamer_url += f"&user_login={streamer}"
                    user_url += f"&login={streamer}"

            # fetches stream data from Twitch
            async with aiohttp.ClientSession(headers=headers) as session:
                logger.info('Fetching stream info')
                async with session.get(streamer_url) as r:
                    stream_info = await r.json()
                async with session.get(user_url) as u:
                    user_info = await u.json()
                if stream_info['data']:
                    for game_id in stream_info['data']:
                        if game_id['game_id'] in game_url:
                            pass
                        elif game_id == stream_info['data'][0]:
                            game_url += game_id['game_id']
                        else:
                            game_url += f"&id={game_id['game_id']}"

                # fetches game data from Twitch
                async with session.get(game_url) as g:
                    game_info = await g.json()
                await session.close()

                # saves all data retrieved
                with open('twitch/user.json', 'w') as user, open('twitch/live_status.json', 'w') as live,\
                        open('twitch/game_info.json', 'w') as game:
                    json.dump(user_info, user, indent=4)
                    json.dump(stream_info, live, indent=4)
                    json.dump(game_info, game, indent=4)
            await live_message()
        await asyncio.sleep(60)


async def live_message():
    webhooks = database.get_webhooks()
    headers = {'Content-Type': 'application/json'}
    api_endpoint = "https://discord.com/api/v8"
    box_art = "https://static-cdn.jtvnw.net/ttv-static/404_boxart-188x250.jpg"
    game_name = "?"
    icon_url = ""
    with open(f'twitch/live_status.json', 'r') as k, open(f'twitch/user.json', 'r') as u,\
            open(f'twitch/game_info.json', 'r') as g, open(f'twitch/started_at.json', 'r') as s:
        live_status = json.load(k)
        user_info = json.load(u)
        game_info = json.load(g)
        started_at = json.load(s)

    # if no streamer is live delete all saved stream information
    if not live_status['data']:
        for old_stream in started_at['data']:
            started_at['data'].remove(old_stream)
        with open(f'twitch/started_at.json', 'w') as s:
            json.dump(started_at, s, indent=4)
        return

    for streamer in live_status['data']:
        # TODO: Fix Twitch embedding to prevent frequent posting
        if not any(d.get('user_id', None) == streamer['user_id'] for d in started_at['data']):
            started_at['data'].append(streamer)
            with open(f'twitch/started_at.json', 'w') as s:
                json.dump(started_at, s, indent=4)
            for game in game_info['data']:
                if streamer['game_id'] == game['id']:
                    box_art = game['box_art_url'].replace("{width}x{height}", "188x250")
                    game_name = game['name']
            for user in user_info['data']:
                if streamer['user_id'] == user['id']:
                    icon_url = user['profile_image_url']
            image_url = streamer['thumbnail_url'].replace('{width}x{height}', '1920x1080')
            embeds = {'embeds': []}
            embed = {
                "color": 6570405,
                "author": {
                    "name": f"{streamer['user_name']} went live!",
                    "url": f"https://www.twitch.tv/{streamer['user_name']}",
                    "icon_url": icon_url
                },
                "title": streamer['title'],
                "description": f"[Watch live on Twitch!](https://www.twitch.tv/{streamer['user_name']})",
                "fields": [
                    {
                        "name": "Playing",
                        "value": game_name,
                        "inline": True
                    },
                    {
                        "name": "Viewers",
                        "value": streamer['viewer_count'],
                        "inline": True
                    }
                ],
                "thumbnail": {
                    "url": box_art
                },
                "image": {
                    "url": f"{image_url}?t={random.randint(0, 999999999)}"
                }
            }
            embeds['embeds'].append(embed)
            async with aiohttp.ClientSession(headers=headers) as session:
                for hook in webhooks:
                    url = f"{api_endpoint}/webhooks/{hook[0]}/{hook[1]}"
                    async with session.post(url, json=embeds) as resp:
                        response = await resp.text()
                        try:
                            response = json.loads(response)
                            if 'code' in response and response['code'] == 10015:
                                database.delete_webhook(hook[0], hook[1])
                        except json.JSONDecodeError:
                            pass
                await session.close()


async def stream(message):
    msg = message.content.split()
    with open('twitch/streams.json', 'r') as f:
        stream_list = json.load(f)
    print(len(msg))
    if len(msg) == 1:
        return await message.channel.send("Usage: --streams [add/remove/list] (add/remove args)")
    if msg[1] == "add":
        stream_list['streams'].append(msg[2].lower())
    elif msg[1] == "remove" and msg[2] in stream_list['streams']:
        stream_list['streams'].remove(msg[2])
    elif msg[1] == "list":
        await message.channel.send(stream_list['streams'])
    with open('twitch/streams.json', 'w') as f:
        json.dump(stream_list, f, indent=4)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch())
