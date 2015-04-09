
from pymongo import MongoClient
from elasticsearch import Elasticsearch

es = Elasticsearch()

conn = MongoClient() 
db = conn.newsdb   #db is called "newsdb"
print  db.catnews.spanish.count()

i = 0
inserted = {}

for c in db.catnews.spanish.find():
    i+=1
    c.pop(u'_id')
    
    if c['date'] in inserted:
        if c['title'] in inserted[c['date']]:
            print 'Duplicate detected'
            continue
        else:
            inserted[c['date']][c['title']] = True
    else:
        inserted[c['date']] = {}
    print 'Inserting'
    i+=1
    es.index(index="catnews_spanish", doc_type='news_article', id=i, body=c)
print i

