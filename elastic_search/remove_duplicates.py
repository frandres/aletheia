
from pymongo import MongoClient
from elasticsearch import Elasticsearch

es = Elasticsearch()

conn = MongoClient() 
db = conn.newsdb   #db is called "newsdb"
collection = db.catnews.spanish

if True:
    i = 0
    count = 0
    for c in db.catnews.spanish.find():
        i+=1
        if 'duplicate'in c:
            count+=1
            collection.update({'_id':c['_id']},{'$unset':{'duplicate':''}})
        if 'parent'in c:
            collection.update({'_id':c['_id']},{'$unset':{'parent':''}})

            #print i
        #if not c['duplicate']:
            #es.index(index="catnews_spanish", doc_type='news_article', id=i, body=c)
    print count

if False:
    for outer in collection.find():

        if 'duplicate' in outer:
            print 'Continuing'
            continue
        print ''
        collection.update({'_id':outer['_id']},{'$set':{'duplicate':False}})
        print outer['_id']
        for inner in collection.find({'date':outer['date'],'title':outer['title']}):
            print inner['_id']
            if 'duplicate' not in inner:
                collection.update({'_id':outer['_id']},{'$set':{'duplicate':True}})
                collection.update({'_id':outer['_id']},{'$set':{'duplicate':outer['_id']}})
            else:
                print ' TRUE'
            
