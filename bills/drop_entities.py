from pymongo import MongoClient

conn = MongoClient()
db = conn.catalan_bills

db.entities.drop()
db.entities_bills.drop()
db.entities_documents.drop()
db.entities_keywords.drop()
db.politicians_bills.drop()
