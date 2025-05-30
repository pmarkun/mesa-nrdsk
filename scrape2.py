import asyncio, datetime as dt
from dateutil.relativedelta import relativedelta
from twscrape import API, gather
import networkx as nx, json

async def main():
    HASHTAG="ozempic"
    today   = dt.date.today()
    weekago = today - relativedelta(days=7)
    api = API()
    await api.pool.add_accounts_from_file("cookies.json")

    tweets = await gather(api.search(
        f"#{HASHTAG} lang:pt", limit=1500,
        since=weekago.isoformat(), until=today.isoformat()))

    G = nx.DiGraph()
    for t in tweets:
        author = t.user.username.lower()
        G.add_node(author)
        for m in t.mentionedUsers or []:
            mentioned = m.username.lower()
            G.add_edge(author, mentioned,
                       weight=G.get_edge_data(author, mentioned, {})
                                  .get('weight', 0) + 1)

    nx.write_graphml(G, f'{HASHTAG}_pt_mentions.graphml')
    print("Graph salvo")

asyncio.run(main())
