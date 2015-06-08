from pymongo import MongoClient
import os
from math import log,sqrt
import matplotlib.pyplot as plt
import louvain
from igraph import *

def run_bfs_iteration(bill):
    processes = []    
    for ent_ana in entities_to_analyze:
        proc = Process(target=ask_google_process_pairs, args=(ent_ana,all_entities,))
        proc.start()
        processes.append(proc)
        sleep(30)

    for proc in processes:
        proc.join()

    new_entities = []

    for ent_ana in entities_to_analyze:
        for entity in all_entities:
            if are_linked(ent_ana,entity):
                if entity not in entitities_to_analyze and entity not in entities_analyzed and entity not in new_entities:
                    new_entities.append(entity)
    return new_entities

def cosine_similarity_keywords(e1ks,e2ks):    

    e1_i = 0
    e2_i = 0

    product = 0
    norm_e1 = 0
    norm_e2 = 0

    e1k = ('',0)
    e2k = ('',0)
    while e1_i < (len(e1ks)) or (e2_i<len(e2ks)):
#    print e1_i < (len(e1ks) -1) or (e2_i<len(e2ks)-1)
#    print e1_i, len(e1ks) -1, e1_i < (len(e1ks) -1)
#    print e2_i, len(e2ks)-1, (e2_i<len(e2ks)-1)
#    print ''
        
        if e1_i < len(e1ks):
            e1k = e1ks[e1_i]
            
        if e2_i < len(e2ks):
            e2k = e2ks[e2_i]

        if e1k[0] == e2k[0]:
            product+= float(e1k[1]) * e2k[1]

            if e1_i< len(e1ks):
                norm_e1 += float(e1k[1]) * e1k[1]
                e1_i+=1

            if e2_i< len(e2ks):
                norm_e2 += float(e2k[1]) * e2k[1]
                e2_i+=1

        if e1k[0] < e2k[0] or e2_i == len(e2ks):
            if e1_i< len(e1ks):
                norm_e1 += float(e1k[1]) * e1k[1]
                e1_i+=1
        if e1k[0] > e2k[0] or e1_i == len(e1ks):
            if e2_i< len(e2ks):
                norm_e2 += float(e2k[1]) * e2k[1]
                e2_i+=1


    norm_e1 = sqrt(norm_e1)            
    norm_e2 = sqrt(norm_e2)            

    if product >0:
        product = product/(norm_e1*norm_e2)   
    return product
    
def intersection(l1,l2):
    count = 0
    i1 = 0
    i2 = 0
    if len(l1) == 0 or len(l2) == 0:
        return 0
    while i1<len(l1) or i2<len(l2):

            
        if i1 < len(l1):
            w1 = l1[i1]
            
        if i2 < len(l2):
            w2 = l2[i2]

        if w1 == w2:
            count+=1

            if i1<len(l1):
                i1+=1
            if i2<len(l2):
                i2+=1

        if w1 < w2 or i2 == len(l2):
            if i1<len(l1):
                i1+=1

        if w2 < w1 or i1 == len(l1):
            if i2<len(l2):
                i2+=1
    return count

def calculate_metrics_ee_bill(e1,e2,e_e):
    
#    if 'bill_articles_co-occurence_mutual_information' in e_e or 'bill_articles_sentence_cosine_similarity_keywords' in e_e:
#        print e_e
#        print 'None'


    if 'bill_articles_ids' not in e1 or 'bill_articles_ids' not in e2:
        raise Exception('No docs for {} or {}'.format(e1['name'], e2['name']))
    e1_count = len(e1['bill_articles_ids'])
    e2_count = len(e2['bill_articles_ids'])
    intersection_count = float(intersection(e1['bill_articles_ids'],e2['bill_articles_ids']))

    metrics = {}
    metrics['bill_articles_co-occurence_mutual_information'] = log((intersection_count+1)/(e1_count*e2_count+1))
    metrics['bill_articles_co-occurence_dice'] = (2*(intersection_count))/(e1_count+e2_count+1)
    metrics['bill_articles_co-occurence_jaccard'] = ((intersection_count)/(e1_count+e2_count-intersection_count+1))
    # Cosine similarity
    if 'entity_keywords'not in e1 or 'entity_keywords' not in e2:
        #print ('No kws for {} or {}'.format(e1['name'], e2['name']))
        return None

    e1ks = e1['entity_keywords'].items() 
    e1ks.sort()
     
    e2ks = e2['entity_keywords'].items()
    e2ks.sort()

    metrics['bill_articles_sentence_cosine_similarity_keywords'] = cosine_similarity_keywords(e1ks,e2ks)   
    return metrics

def calculate_metrics_ee_general(db,bill_id,e_e):
    
    if 'co-occurence_mutual_information' in e_e and 'co-occurence_dice' in e_e and 'co-occurence_jaccard' in e_e and 'cosine_similarity_keywords' in e_e:
        return None

    e1 = db.entities.find_one({'_id':e_e['e1_id']})
    e2 = db.entities.find_one({'_id':e_e['e2_id']})


    if 'articles_ids'not in e1 or 'articles_ids' not in e2:
        print 'Articles ids not present'
        print e1['name']
        print e2['name']
        return None

    e1_count = len(e1['articles_ids'])
    e2_count = len(e2['articles_ids'])
    intersection_count = float(intersection(e1['articles_ids'],e2['articles_ids']))

    metrics = {}
    metrics['co-occurence_mutual_information'] = log((intersection_count+1)/(e1_count*e2_count+1))
    metrics['co-occurence_dice'] = (2*(intersection_count))/(e1_count+e2_count+1)
    metrics['co-occurence_jaccard'] = ((intersection_count)/(e1_count+e2_count-intersection_count+1))
    # Cosine similarity
    if 'keywords'not in e1 or 'keywords' not in e2:
        print 'Keywords not present',e1['name'], e2['name']
        print e1['name']
        print e2['name']
        return None

    e1ks = e1['keywords'].items() 
    e1ks.sort()
     
    e2ks = e2['keywords'].items() 
    e2ks.sort()

    metrics['cosine_similarity_keywords'] = cosine_similarity_keywords(e1ks,e2ks)   

    return metrics

import sys

def calculate_metrics(db,bill_id):

    #for i in range(0,len(entities)-1): 
    i = 0

    rel_entities_bill = db.bills.find_one({'id':bill_id})['relevant_entities']
    for e1 in rel_entities_bill :
        e1 = db.entities_bills.find_one({'bill':bill_id,'entity':e1})
        if e1 is None or 'bill_articles_ids' not in e1:
            continue
        i+=1
        print i, e1['name']
        j=0
        for e2 in rel_entities_bill :
            if e1 == e2:
                continue
            e2 = db.entities_bills.find_one({'bill':bill_id,'entity':e2})
            if 'bill_articles_ids' not in e2:
                continue
#        for e2 in db.entities_bills.find({'bill':bill_id,'bill_articles_ids':{'$exists':True}},timeout=False).batch_size(5100):
            #e2 = db.entities.find_one({'_id':eb2['entity']})
            j+=1
            if e2 is None or e1['name'] == e2['name']:
                continue
            if j%100 == 0:
                print j

            e_e = db.entity_entity.find_one({'$or':[{'e1_id':e1['entity'],'e2_id':e2['entity']},{'e2_id':e1['entity'],'e1_id':e2['entity']}]})
            if e_e is None:
                e_e = {}

                if e1['name'] > e2['name']:
                    e_e['e1_name'] = e2['name']
                    e_e['e2_name'] = e1['name']
                    e_e['e1_id'] = e2['entity']
                    e_e['e2_id'] = e1['entity']
                else:
                    e_e['e1_name'] = e1['name']
                    e_e['e2_name'] = e2['name']
                    e_e['e1_id'] = e1['entity']
                    e_e['e2_id'] = e2['entity']
                e_e['bill_id'] = bill_id
            '''
            if 'bill_metrics' not in e_e:
                e_e['bill_metrics'] = {}
            if 'bill_id' not in e_e['bill_metrics'] :
                e_e['bill_metrics'][bill_id] = {}
            '''
            metrics = calculate_metrics_ee_bill(e1,e2,e_e)
            if metrics is None:
                print 'continuing'
                continue
            for (metric,value) in metrics.items():
                e_e[metric] = value
            #db.entity_entity.update({'$or':[{'e1_id':e1['entity'],'e2_id':e2['entity']},{'e2_id':e1['entity'],'e1_id':e2['entity']}]},e_e,upsert=True)

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
        
def find_cutting_point(scores, epsilon = 0.0005,window_size = 10):
    return elbow(scores)

def generate_graph(db,bill_id,method):
    if type(method) is list:
        all_links = {}
        for m in method:
            all_links[m] = generate_graph_method(db,bill_id,m)
    else:
        generate_graph_method(db,bill_id,method)
        return

    key_entities = [u'Ricardo', u'Felip Puig', u'Espana', u'Adsera', u'Turistico', u'Hortensia Grau', u'World', u'Veremonte', u'Gabriel Escarrer', u'Melia', u'Portaventura', u'Macao', u'Artur Mas', u'Singapur', u'Port Aventura', u'Xavier Sabat', u'Enrique Ba\xf1uelos', u'Eurovegas', u'Roca Village', u'Albert Batet', u'Vegas Sands', u'Reus', u'Pere Granados', u'Sheldon Adelson', u'Las Vegas', u'BCN', u'Cataluna', u'Pere Navarro', u'Oriol Amoros', u'Europa', u'Costa Dorada', u'Josep Felix Ballesteros', u'Josep Poblet', u'Damia Calvet', u'Parlament', u'Vila-seca', u'Catalunya', u'Europa Press', u'Value Retail', u'Tarragona', u'Costa Daurada', u'Xavier Adsera',  u'Barcelona World', u'Xavier Sabate', u'Hard Rock', u'Francesc Perendreu', u'Melco', u'Economia', u'Salou']

    for e in key_entities:
        print ''
        print '-----------------------------------------------------'
        print e
        print all_links['google_dice'][e]
        print all_links['cosine_similarity_keywords'][e]
        for e1 in all_links['google_dice'][e]:
            if e1 not in all_links['cosine_similarity_keywords']:
                print ' google_dice adds: {}'.format(e1)
        for e1 in all_links['cosine_similarity_keywords'][e]:
            if e1 not in all_links['google_dice']:
                print ' cosine similarity adds adds: {}'.format(e1)
                
#    generate_graph(db,bill_id,'google_dice')

#for entity in entities:
'''
        relevant_entities[entity['name']] = []
        entity_entities = []
        for e_e in db.entity_entity.find({'$or':[{'e1_id':entity['_id']},{'e2_id':entity['_id']}]}):
            for e in entities:
                if (e_e['e1_id'] == e['_id'] or e_e['e2_id'] == e['_id']) and e['_id'] != entity['_id'] and 'google_mutual_information' in e_e:
                    entity_entities.append(e_e)
        values = []
'''

def generate_graph_method(db,bill_id,metric):
    relevant_entities = {}
    k=0
    rel_entities_bill = db.bills.find_one({'id':bill_id})['relevant_entities']
    for e1 in rel_entities_bill :
        e_b = db.entities_bills.find_one({'bill':bill_id,'entity':e1})
        k+=1 
#        print k,e_b['name']
        values = []
        relevant_entities[e_b['name']] = []
        j=0
        for e2 in rel_entities_bill:
            if e1 == e2:
                continue
	    #print db.entity_entity.find({'$or':[{'e1_id':e1},{'e2_id':e1}],metric:{'$exists': True},'bill_id':bill_id}).count()
            e_e = db.entity_entity.find_one({'$or':[{'e1_id':e2,'e2_id':e1},{'e1_id':e1,'e2_id':e2}],metric:{'$exists': True},'bill_id':bill_id})

            if e_e is None:
                j+=1
                print e1,e2
                e_b2 = db.entities_bills.find_one({'bill':bill_id,'entity':e2})
                values.append((0,e_b2['name']))
                #print ' '+e_b2['name']
                continue
            if e_e['e1_name'] == e_b['name']:
                if e_e[metric] > 0.1:
                    values.append((e_e[metric],e_e['e2_name'])) 
            else:
                if e_e[metric] > 0.1:
                    values.append((e_e[metric],e_e['e1_name'])) 
        if len(values)==0:
            continue
#      print j
        values.sort(reverse=True)
        #print len(values)
        print 'P:{}'.format(e_b['name'])
        for (value,name) in values:
            print ' {} with value: {}'.format(name.encode('utf8'),value)
        cut_point = find_cutting_point([v[0] for v in values])
        for i in range(0,cut_point+1):
            relevant_entities[e_b['name']].append(values[i][1])

    links = {}
    for entity in db.entities_bills.find({'bill':bill_id,'bill_articles_ids':{'$exists':True}},timeout=False): 
        links[entity['name']] = []
    key_entities = [u'Felip Puig', u'Espana', u'Adsera', u'Turistico', u'Hortensia Grau', u'World', u'Veremonte',  u'Gabriel Escarrer', u'Melia', u'Portaventura', u'Macao', u'Artur Mas', u'Singapur', u'Port Aventura', u'Xavier Sabat', u'Enrique Banuelos', u'Eurovegas', u'Roca Village', u'Albert Batet', u'Vegas Sands', u'Reus', u'Pere Granados', u'Sheldon Adelson', u'Las Vegas', u'BCN', u'Cataluna', u'Pere Navarro', u'Oriol Amoros', u'Europa', u'Costa Dorada', u'Josep Felix Ballesteros', u'Josep Poblet', u'Damia Calvet', u'Parlament', u'Vila-seca', u'Catalunya', u'Europa Press', u'Value Retail', u'Tarragona', u'Costa Daurada', u'Xavier Adsera', u'Barcelona World', u'Xavier Sabate', u'Hard Rock', u'Francesc Perendreu', u'Melco', u'Economia', u'Salou']

    #for entity in db.entities_bills.find({'bill':bill_id,'bill_articles_ids':{'$exists':True}},timeout=False):
    for e1 in rel_entities_bill :
        entity = db.entities_bills.find_one({'bill':bill_id,'entity':e1})
        for r_e in relevant_entities[entity['name']]:
            if r_e in relevant_entities and entity['name'] in relevant_entities[r_e] and entity['name']<r_e and (entity['name'] in key_entities or r_e in key_entities):
#                print '"{}","{}"'.format(r_e.encode('utf8'),entity['name'].encode('utf8') )
                links[entity['name']].append(r_e)
                links[r_e].append(entity['name'])
    return links

    for x in ['Sheldon Adelson','Albert Batet','Oriol Amoros','Xavier Sabat','Veremonte','Vegas Sands','Xavier Adsera','Adsera','Melco','Gabriel Escarrer','Melia','Value Retail']:
	if x in links:
        	print x,links[x]
    #coms = get_communities_louvain(links)
    #for com in coms:
    #    print com
    '''
    get_communities_wcc(links)
    return
    communities = get_communities_louvain(links)
    final_entities = []
    for community in communities:
        for politician in ['Albert Batet','Oriol Amoros','Xavier Sabat']:
            if politician in community:
                for entity in community:
                    if entity not in final_entities:
                        final_entities.append(entity)

    for e1 in final_entities:
        for e2 in links[e1]:
            print '"{}","{}"'.format(e1.encode('utf8'),e2.encode('utf8') )
    '''
def get_communities_louvain(graph):
    g = Graph()
    id_to_entity = {}
    entity_to_id = {}
    i = 0
    for entity in graph.keys():
        id_to_entity[i] = entity
        entity_to_id[entity] = i
        i+=1
    g.add_vertices(len(graph.keys()))
    edges = []    
    for (e,related_entities) in graph.items():
        for re in related_entities:
            if e<re:
                edges.append((entity_to_id[e],entity_to_id[re]))
    g.add_edges(edges)

    #print g
    part = louvain.find_partition(g, method='RBConfiguration')
    i= 0
    communities = {}
    for ms in part.membership:
        if ms not in communities:
            communities[ms] = [id_to_entity[i]]
        else:
            communities[ms].append(id_to_entity[i])
        i+=1
    return [val for val in communities.values()]
def get_communities_wcc(graph):
    id_to_entity = {}
    entity_to_id = {}
    i = 0
    for entity in graph.keys():
        i+=1
        id_to_entity[i] = entity
        entity_to_id[entity] = i

    f = open('./community_detection/SCD/build/network_file.dat', 'w')
    for (e,related_entities) in graph.items():
        for re in related_entities:
            if e<re:

                #print '{},{}'.format(entity_to_id[e],entity_to_id[re])
                f.write('{} {}\n'.format(entity_to_id[e],entity_to_id[re]))

    f.close()
    os.system('./community_detection/SCD/build/scd -f ./community_detection/SCD/build/network_file.dat -o ./community_detection/SCD/build/network_communities.dat')

    f = open('./community_detection/SCD/build/network_communities.dat', 'r')
    communities = []
    for line in f:
        print line
        communities.append([id_to_entity[int(i)] for i in line.split(' ')])
    f.close()
    for community in communities:
        print community
'''
def generate_graph_method(db,bill_id,metric):
    relevant_entities = {}
    i=0
    rel_entities_bill = db.bills.find_one({'id':bill_id})['relevant_entities']
    for e_b in db.entities_bills.find({'bill':bill_id,'bill_articles_ids':{'$exists':True}},timeout=False):
        if e_b['entity'] not in rel_entities_bill:
            continue
        i+=1 
        #print i
        values = []
        relevant_entities[e_b['name']] = []
        for e_e in db.entity_entity.find({'$or':[{'e1_id':e_b['_id']},{'e2_id':e_b['_id']}],metric:{'$exists': True},'bill_id':bill_id}):
            if e_e['e1_name'] == e_b['name']:
                if e_e['e2_id'] not in rel_entities_bill:
                    continue
                values.append((e_e[metric],e_e['e2_name'])) 
            else:
                if e_e['e1_id'] not in rel_entities_bill:
                    continue
                values.append((e_e[metric],e_e['e1_name'])) 
        if len(values)==0:
            continue
        values.sort(reverse=True)
        #print len(values)
        cut_point = find_cutting_point([v[0] for v in values])
        for i in range(0,cut_point+1):
            relevant_entities[e_b['name']].append(values[i][1])

    links = {}
    for entity in db.entities_bills.find({'bill':bill_id,'bill_articles_ids':{'$exists':True}},timeout=False): 
        links[entity['name']] = []

    for entity in db.entities_bills.find({'bill':bill_id,'bill_articles_ids':{'$exists':True}},timeout=False):
        for r_e in relevant_entities[entity['name']]:
            if entity['name'] in relevant_entities[r_e] and entity['name']<r_e:
#                print '"{}","{}"'.format(r_e.encode('utf8'),entity['name'].encode('utf8') )
                links[entity['name']].append(r_e)
                links[r_e].append(entity['name'])
                print entity['name'].encode('utf8'),r_e.encode('utf8')
    return links
'''   
def plot(db, bill_id,metric):

    rel_entities_bill = db.bills.find_one({'id':bill_id})['relevant_entities']
    for e1 in rel_entities_bill :
        e_b = db.entities_bills.find_one({'bill':bill_id,'entity':e1})
        #print i
        values = []
        for e2 in rel_entities_bill :
            if e1 == e2:
                continue
#	for e_e in db.entity_entity.find({'$or':[{'e1_id':e_b['_id']},{'e2_id':e_b['_id']}],metric:{'$exists': True},'bill_id':bill_id}):
            e_e = db.entity_entity.find_one({'$or':[{'e1_id':e2,'e2_id':e1},{'e1_id':e1,'e2_id':e2}],metric:{'$exists': True},'bill_id':bill_id})
            if e_e is None:
                print e_e
                continue
            if e_e[metric]>0.1:
                values.append(e_e[metric]) 

        values.sort(reverse=True)
        plt.plot(range(len(values)),values)
        i = find_cutting_point(values)
        if i is not None:
            plt.plot(i, values[i], 'ro')
        directory = './results/metrics/'+bill_id+'/'+metric+'/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        plt.savefig(directory+ e_b['name']+'.png')
        plt.clf()

'''
    entities = [db.entities.find_one({'_id':e_id}) for e_id in db.bills.find_one({'id':bill_id})['relevant_entities']]

    metrics = ['co-occurence_mutual_information', 'co-occurence_dice', 'co-occurence_jaccard','cosine_similarity_keywords']

    for entity in entities:
        entity_entities = []
        for e_e in db.entity_entity.find({'$or':[{'e1_id':entity['_id']},{'e2_id':entity['_id']}]}):
            for e in entities:
                if (e_e['e1_id'] == e['_id'] or e_e['e2_id'] == e['_id']) and e['_id'] != entity['_id'] and 'google_mutual_information' in e_e:
                    entity_entities.append(e_e)
        print len(entity_entities)
        for metric in metrics:
            for e_e in entity_entities:
                if 'google_mutual_information' not in e_e:
                    print e_e

            values = [e_e[metric] for e_e in entity_entities]
            values.sort(reverse=True)
            plt.plot(range(len(values)),values)
            i = find_cutting_point(values)
            if i is not None:
                plt.plot(i, values[i], 'ro')
            directory = './results/metrics/'+bill_id+'/'+metric+'/'
            if not os.path.exists(directory):
                os.makedirs(directory)
            plt.savefig(directory+ entity['name']+'.png')
            plt.clf()
'''
def main():
    db = MongoClient().catalan_bills
    bill_id = '00062014'
    #calculate_metrics(db,bill_id)
    #plot(db,bill_id,'bill_articles_sentence_cosine_similarity_keywords')
#    generate_graph(db,bill_id,['cosine_similarity_keywords','google_dice']) #['bill_articles_co-occurence_mutual_information','bill_articles_sentence_cosine_similarity_keywords']
    #print('GENERATING')
    generate_graph(db,bill_id,'bill_articles_sentence_cosine_similarity_keywords')
#    generate_graph(db,bill_id,'google_dice')
main()
