import aiohttp
import asyncio
import json
import os
import random

from . import database


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


async def is_live():
    """Retrieves stream info from https://api.twitch.tv/
     and saves the information to file in json format."""
    headers = {'Client-ID': os.environ['twitch']}
    while True:
        api_endpoint = 'https://api.twitch.tv/helix/'
        streamer_url = api_endpoint + "streams?user_login="
        user_url = api_endpoint + "users?login="
        game_url = api_endpoint + "games?id="
        try:
            with open(f'twitch/streams.json', 'r'):
                pass
        except FileNotFoundError:
            with open(f'twitch/streams.json', 'w') as f:
                f.write('{"streams": []}')
        finally:
            with open(f'twitch/streams.json', 'r') as f:
                streams = json.load(f)
        if streams != {"streams"}:
            for stream in streams['streams']:
                if stream == streams['streams'][0]:
                    streamer_url += stream
                    user_url += stream
                else:
                    streamer_url += f"&user_login={stream}"
                    user_url += f"&login={stream}"
            async with aiohttp.ClientSession(headers=headers) as session:
                print("Fetching stream info...")
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
                async with session.get(game_url) as g:
                    game_info = await g.json()
                await session.close()
                with open('twitch/user.json', 'w') as f:
                    json.dump(user_info, f, indent=4)
                with open('twitch/live_status.json', 'w') as f:
                    json.dump(stream_info, f, indent=4)
                with open('twitch/game_info.json', 'w') as f:
                    json.dump(game_info, f, indent=4)
            await live_embed()
        await asyncio.sleep(60)


async def live_embed():
    webhooks = database.get_webhooks()
    headers = {'Content-Type': 'application/json'}
    api_endpoint = "https://discordapp.com/api/webhooks/"
    box_art = "https://static-cdn.jtvnw.net/ttv-static/404_boxart-188x250.jpg"
    game_name = "?"
    icon_url = ""
    with open(f'twitch/live_status.json', 'r') as k:
        live_status = json.load(k)
    with open(f'twitch/user.json', 'r') as u:
        user_info = json.load(u)
    with open(f'twitch/game_info.json', 'r') as g:
        game_info = json.load(g)
    with open(f'twitch/started_at.json', 'r') as s:
        started_at = json.load(s)
    if not live_status['data']:
        return
    for stream in live_status['data']:
        if stream['user_name'] not in started_at or stream['user_name'] is not "" and \
                stream['started_at'] != started_at[stream['user_name']]['started_at']:
            for game in game_info['data']:
                if stream['game_id'] == game['id']:
                    box_art = game['box_art_url'].replace("{width}x{height}", "188x250")
                    game_name = game['name']
            for user in user_info['data']:
                if stream['user_id'] == user['id']:
                    icon_url = user['profile_image_url']
            image = stream['thumbnail_url'].replace('{width}x{height}', '1920x1080')
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
                    "url": f"{image}?t={random.randint(0, 999999999)}"
                }
            }
            embeds['embeds'].append(embed)
            async with aiohttp.ClientSession(headers=headers) as session:
                for hook in webhooks:
                    url = f"{api_endpoint}{hook[0]}/{hook[1]}"
                    async with session.post(url, json=embeds) as resp:
                        response = await resp.text()
                        try:
                            response = json.loads(response)
                            if 'code' in response and response['code'] == 10015:
                                database.delete_webhook(hook[0], hook[1])
                        except json.JSONDecodeError:
                            pass
                await session.close()
                started_at.update({stream['user_name']: {'started_at': stream['started_at']}})
                with open('twitch/started_at.json', 'w') as s:
                    json.dump(started_at, s, indent=4)


async def streams(message):
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
