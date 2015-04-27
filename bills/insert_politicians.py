from pymongo import MongoClient

conn = MongoClient()
db = conn.catalan_bills

bill = '00062014'

politicians = [{'name':'Albert Batet','aliases':['Batet'],'tag':'PERSON'},
                {'name':'Xavier Sabat','aliases':['Sabat'],'tag':'PERSON'},
                {'name':'Oriol Amoros','aliases':['Amoros'],'tag':'PERSON'}]

for politician in politicians:
    cursor = db.entities.find({'name':politician['name']})
    if cursor.count()==0:
        db.entities.insert(politician)
        cursor = db.entities.find({'name':politician['name']})
    db.politicians_bills.insert({'entity_id':cursor[0]['_id'],'bill':bill})
        


