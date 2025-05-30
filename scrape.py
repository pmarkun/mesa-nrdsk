import itertools, datetime as dt, time, random
from dateutil.relativedelta import relativedelta
import snscrape.modules.twitter as sntwitter
import networkx as nx

HASHTAG = "ozempic"
LIMIT   = 1500
today   = dt.date.today()
weekago = today - relativedelta(days=7)
query   = f'#{HASHTAG} lang:pt since:{weekago} until:{today}'

def safe_scrape(q, max_try=5):
    for attempt in range(max_try):
        try:
            return itertools.islice(
                sntwitter.TwitterSearchScraper(q).get_items(), LIMIT)
        except Exception as e:
            wait = 2 + random.random()*4
            print(f'Erro {e} — tentando de novo em {wait:.1f}s...')
            time.sleep(wait)
    raise RuntimeError('Falha depois de várias tentativas.')

tweets = list(safe_scrape(query))
print(f'{len(tweets)} tweets PT-BR coletados')

G = nx.DiGraph()
for t in tweets:
    author = t.user.username.lower()
    G.add_node(author)
    for w in t.content.split():
        if w.startswith('@') and len(w) > 1:
            mentioned = w[1:].strip('.,:;!?').lower()
            if mentioned != author:
                G.add_edge(author, mentioned,
                           weight=G.get_edge_data(author, mentioned, {})
                                      .get('weight', 0) + 1)

nx.write_graphml(G, f'{HASHTAG}_pt_mentions.graphml')
print('Exportado para Gephi:', f'{HASHTAG}_pt_mentions.graphml')
