'''
TODO:

1) Insert entities in MongoDB.- DONE
3) Compute IDF. Print that. Analyze. Be happy
'''
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

from nltk.stem import SnowballStemmer
from collections import defaultdict

from elasticsearch import Elasticsearch
import matplotlib.pyplot as plt
from pymongo import MongoClient
from math import sqrt,log
import re

def entity_idf(_id,col, N = 45.0):
    return log(N/len(col.find({'_id':_id})[0]['bills']))

conn = MongoClient()
db = conn.catalan_bills

c = 0
for bill in db.bills.find():
    c+=1
    print c
    original_keywords = bill['keywords']

    plt.plot(range(len(original_keywords)),[x[1] for x in original_keywords])
    plt.savefig('./results/keywords/'+bill['id']+'_original_keywords.png')
    plt.clf()
    original_keywords = [x for (x,y) in original_keywords]
    rocchio_kws = bill['rocchio_keywords']
    
    entities = bill['entities']
    entities_score = {}
    for entity in entities:
        mongo_entity = db.entities.find({'_id': entity['_id']})[0]
        tags = [(y,x) for (x,y) in mongo_entity['tags'].items()]
        tags.sort(reverse= True)
        if tags[0][0] == 'LOCATION':
            continue
             
        entities_score[entity['name']]= (entity['weight']['value'] * entity_idf(entity['_id'],db.entities), entity['weight']['value'],entity_idf(entity['_id'],db.entities),entity['freq'])

    sorted_entities = [(y[0],x,y) for (x,y) in entities_score.items()]
    sorted_entities.sort(reverse=True)
    sorted_entities = [(x,y) for (z,x,y) in sorted_entities]
    
    with open('./results/'+bill['id']+'_summary.txt', 'w') as f:
        f.write(bill['text'][0:500].encode('utf8')+'\n\n')
        f.write('\n----------------- ROCCHIO FOUND -----------------\n\n')

        i = 0
        for (kw,weight) in rocchio_kws[0:1024]:
            if kw not in original_keywords:
                f.write(kw.encode('utf8')+ ' with weight: '+ str(weight) + ' and ranking ' + str(i)+'\n')
            i+=1
        i = 0
        f.write('\n----------------- ENTITIES FOUND -----------------\n\n')
        for (entity,weight) in sorted_entities:
            i+=1
            f.write(entity.encode('utf8'))
            f.write(' with score: {}\n'.format(weight[0]))
            f.write(' with weight: {}\n'.format(weight[1]))
            f.write(' with idf: {}\n'.format(weight[2]))
            f.write(' with freq: {}\n'.format(weight[3]))
            f.write(' with ranking: {}\n\n'.format(i))
