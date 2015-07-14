import sys
from pymongo import MongoClient
import os
from math import log,sqrt
import matplotlib.pyplot as plt
import louvain
from igraph import *


def get_norm(v):
    return sqrt(v[0]**2 + v[1]**2)
def elbow(scores):
    distances = []
    #print scores
    max_y = scores[0]
    b = [len(scores),scores[len(scores)-1]-max_y]
    b_norm = get_norm(b)
    b[0] = b[0]/b_norm
    b[1] = b[1]/b_norm

    for i in range(0,len(scores)):
        p = (i,scores[i]-max_y)
        p_bhat = p[0]*b[0] + p[1]*b[1]
        proj = (b[0]*p_bhat,b[1]*p_bhat)
        d = (p[0]-proj[0],p[1]-proj[1])
        distances.append(get_norm(d))

    return distances.index(max(distances))
        
def find_cutting_point(scores):
    return elbow(scores)

'''
Para cada ley, determinar entidades relevantes para cada entidad y 
añadir una arista en el grafo entre dos entidades e1 y e2 
si e1 esta en la lista de entidades relevantes de e2 
y si e2 esta en la lista de entidades relevantes de e1.

'''
def generate_graph(db,bill_id,metric = 'bill_articles_sentence_cosine_similarity_keywords', threshold = 0.20):
    relevant_entities = {}
    k=0
    rel_entities_bill = db.bills.find_one({'id':bill_id})['relevant_entities']
    
    for e1 in rel_entities_bill :

	# Obtener la informacion de e1.

        e_b = db.entities_bills.find_one({'bill':bill_id,'entity':e1})
        k+=1 
        values = []
        relevant_entities[e_b['name']] = []
        j=0
        for e2 in rel_entities_bill:

	    # Obtener la informacion de e2.
            if e1 == e2:
                continue
            j+=1
            if j%100 == 0:
                print j

            # Obtener el objeto de la interrelación.
            e_e = db.entity_entity.find_one({'$or':[{'e1_id':e2,'e2_id':e1},{'e1_id':e1,'e2_id':e2}],metric:{'$exists': True},'bill_id':bill_id})

            if e_e is None:
                e_b2 = db.entities_bills.find_one({'bill':bill_id,'entity':e2})
                values.append((0,e_b2['name']))
                #print ' '+e_b2['name']
                continue

            # Guardar el valor de la métrica si es mayor que un threshold, ya que esto de mejores resultados empiricamente.
            if e_e['e1_name'] == e_b['name']:
                if e_e[metric] > 0.05:
                    values.append((e_e[metric],e_e['e2_name'])) 
            else:
                if e_e[metric] > 0.05:
                    values.append((e_e[metric],e_e['e1_name'])) 
        # Encontrar el codo.
        if len(values)==0:
            continue
        values.sort(reverse=True)

        cut_point = find_cutting_point([v[0] for v in values])
        for i in range(0,cut_point+1):
	    # Si el valor esta a la izquierda del codo y es mayor que un threshold minimo, considerar la entidad como relevante.
            if values[i][0]>threshold:
                relevant_entities[e_b['name']].append(values[i][1])

    links = {}
    for entity in db.entities_bills.find({'bill':bill_id,'bill_articles_ids':{'$exists':True}},timeout=False): 
        links[entity['name']] = []

    # Evaluar las relaciones recíprocas.
    for e1 in relevant_entities.keys() :
        for e2 in relevant_entities[e1]:
            if e2 in relevant_entities and e1 in relevant_entities[e2] and e1<e2:

                links[e1].append(e2)
                links[e2].append(e1)

    db.graphs.update({'bill':bill_id},{'bill':bill_id,'links':links},upsert=True)
    return links

def main():
    db = MongoClient().catalan_bills
    bill_ids =[bill['id'] for bill in db.bills.find()] 
    for bill_id in bill_ids:
        generate_graph(db,bill_id)

main()
