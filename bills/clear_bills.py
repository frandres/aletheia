from pymongo import MongoClient

conn = MongoClient()
collection = conn.catalan_bills.bills
for bill in collection.find():
    collection.update({'id':bill['id']},{'$unset':{'entities':''}})
