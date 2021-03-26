import asyncio
import logging

import aiohttp
import pyxivapi
from pyxivapi.models import Filter, Sort

API_KEY = "0242c177a95446a18365e64e84154f4816f5359a0b8b4e24858d8feca43405c5"


async def fetch_item(name):
    client = pyxivapi.XIVAPIClient(api_key=API_KEY)

    getitem = await client.index_search(
        name=name,
        indexes=["Item"],
        columns=["ID", "Name", "Description", "Icon", "LevelItem"]
    )

    await client.session.close()

    if getitem["Pagination"]["Results"] < 1:
        return False
    else:
        return getitem


async def fetch_example_results():
    client = pyxivapi.XIVAPIClient(api_key=API_KEY)

    # Search for an item using specific filters
    filters = [
        Filter("LevelItem", "gte", 100)
    ]

    filtered = [
        Filter("Name", "gte", 0)
    ]

    sort = Sort("LevelItem", True)

    dodo = await client.index_search(
        name="Edenmorn Codex",
        indexes=["Item"],
        columns=["Name", "Description", "Icon", "LevelItem", "Stats"],
        # filters=filtered,
        sort=sort,
    )

    print(dodo)

    item = await client.index_search(
        name="Omega Rod",
        indexes=["Item"],
        columns=["ID", "Name", "Icon", "Description", "LevelItem"],
        # filters=filters,
        sort=sort,
    )

    print(item)

    specific = await client.index_by_id(
        index="Item",
        content_id=23575,
        columns=["ID", "Name", "Icon", "ItemUICategory.Name", "ItemResult.Description"]
    )
    print(specific)

    if dodo['Pagination']['Results'] > 0:
        print(dodo['Results'][0]['Name'] + "\n" + client.base_url + dodo['Results'][0]['Icon'])
    else:
        print("Nothing to see here...")

    await client.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s', datefmt='%H:%M')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_example_results())
