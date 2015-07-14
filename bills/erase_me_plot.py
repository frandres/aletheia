
from pymongo import MongoClient
import matplotlib.pyplot as plt

db = MongoClient().catalan_bills

entity_weight= []

for eb in db.entities_bills.find({'bill':'00062014'}):
    entity = db.entities.find_one({'_id':eb['entity']})
    if entity is None:
        print eb
    else:    
        if 'google_count' in entity and entity['google_count'] >100:
            entity_weight.append((eb['weight']['value'],eb['name']))
         


entity_weight.sort(reverse=True)
plt.plot(range(len(entity_weight)), [x[0] for x in entity_weight])
plt.savefig('plots/0062014_adjusted_weight.png')
plt.clf()

for val in entity_weight[0:500]:
    print val


        


