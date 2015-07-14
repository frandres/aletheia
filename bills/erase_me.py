from pymongo import MongoClient

db = MongoClient().catalan_bills

print db.entities.find({'keywords':{'$exists':True}}).count()
for entity in db.entities_bills.find({'entity_keywords':{'$exists':True}}):
    db.entities_bills.update({'_id':entity['_id']},{'$unset':{'entity_keywords':''}})
