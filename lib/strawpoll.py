import aiohttp


async def poll(message):
    """Gets information from user and creates a Straw Poll.
    usage:
        Can include more than one option.
        Title and Options must be within quotations.
        --poll "title" "options"
    permissions:
        read_message_history
        send_messages
    """
    url = "https://www.strawpoll.me/api/v2/polls"
    headers = {'Content-Type': 'application/json'}
    data = {
        'title': "",
        'options': []
    }
    info = message.content.split("\"")

    for msg in info:
        if msg == info[0]:
            pass
        elif msg == " " or msg == "":
            pass
        elif msg == info[1]:
            data['title'] = info[1]
        else:
            data['options'].append(msg)

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url=url, json=data) as p:
            json_body = await p.json()
            poll_url = f"https://www.strawpoll.me/{json_body['id']}"
    return poll_url
