
from pymongo import MongoClient
from elasticsearch import Elasticsearch
from nltk.tokenize import sent_tokenize

es = Elasticsearch()

conn = MongoClient() 
db = conn.newsdb   #db is called "newsdb"
print  db.catnews.spanish.count()

i = 0
inserted = {}
j=0
all_articles = [c for c in db.catnews.spanish.find()]
for c in all_articles:
    i+=1
    c.pop(u'_id')
    
    if c['date'] in inserted:
        if c['title'] in inserted[c['date']]:
            continue
        else:
            inserted[c['date']].append([c['title']])
    else:
        inserted[c['date']] = [c['title']]
    es.index(index="catnews_spanish", doc_type='news_article', id=i, body=c)
    print i

