from pymongo import MongoClient

conn = MongoClient()
db = conn.catalan_bills

bill = '00152014'

politicians = [{'name':'Alicia Alegret','aliases':['Alegret'],'tag':'PERSON'},
                {'name':'Ferran Falco','aliases':['Falco'],'tag':'PERSON'},
                {'name':'Alicia Romero','aliases':['Romero'],'tag':'PERSON'},
                {'name':'Jose Villegas Perez','aliases':[],'tag':'PERSON'},
                {'name':'Quim Arrufat','aliases':['Arrufat'],'tag':'PERSON'},
                {'name':'Sergi Sabria','aliases':['Sabria'],'tag':'PERSON'},
                {'name':'Dolors Camats','aliases':['Camats'],'tag':'PERSON'}]

for politician in politicians:
    cursor = db.entities.find({'name':politician['name']})
    if cursor.count()==0:
        db.entities.insert(politician)
        cursor = db.entities.find({'name':politician['name']})
    db.politicians_bills.insert({'entity_id':cursor[0]['_id'],'bill':bill})
        


