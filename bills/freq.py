from elasticsearch import Elasticsearch

from pymongo import MongoClient
db = MongoClient().catalan_bills

es = Elasticsearch()
count = 0
for eb in db.entities_bills.find({'bill':'00062014'}):
    q = {"query": {'match_phrase': {'body': {'analyzer': 'analyzer_shingle','query': eb['name']}}}}
    if es.count(index='catnews_spanish',body=q)['count']!=2:
        count+=1
    else:
        print eb['name'],es.count(index='catnews_spanish',body=q)['count']

print count
