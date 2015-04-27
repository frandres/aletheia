
from pymongo import MongoClient
from google import ask_google

def google_bill(db,bill_id):

    politicians = []
    for politician_bill in db.politicians_bills.find({'bill':bill_id}):
        entity = db.entities.find_one({'_id':politician_bill['entity_id']})
        politicians.append(entity)
        
    entities = []
    for entity_bill in db.entities_bills.find({'bill':bill_id}):
        entity = db.entities.find_one({'_id':entity_bill['entity']})
        if entity is not None and entity['tag'] in ['PERSON','ORGANIZATION','MISC']:
            entities.append(entity)
    
    for politician in politicians:
        for (entity,results) in ask_google(politician,entities).items():

            if politician['name'] < entity['name']:
                e1 = politician
                e2 = entity
            else:
                e1 = entity
                e2 = politician

            db.entity_entity.insert({'e1_id':e1['_id'],'e2_id':e2['_id'],'google_count':results,'e1_name':e1['name'],'e2_name':e2['name']})

                    
def main():
    conn = MongoClient()
    db = conn.catalan_bills
    bill = '00062014'
    google_bill(db,bill)

    entity_entity = []

    for e_e in db.entity_entity.find():
        entity_entity.append(e_e['google_count'],e_e['e1_name'],e_e['e2_name'])

    plt.plot(range(len(entity_entity)),[score for (score,_,__) in entity_entity])
    plt.savefig('./plots/'+bill+'.png')
    plt.clf()

main()

