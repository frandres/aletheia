
from pymongo import MongoClient
from elasticsearch import Elasticsearch

es = Elasticsearch()

conn = MongoClient() 
db = conn.newsdb   #db is called "newsdb"
db.catnews.spanish.count()    

i = 0
for c in db.catnews.spanish.find():
    i+=1
    c.pop(u'_id')
    es.index(index="catnews_spanish", doc_type='news_article', id=i, body=c)
