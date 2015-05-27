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
    
def calculate_metrics_ee(db,bill_id,e_e):
    e1 = db.entities.find_one({'_id':e_e['e1_id']})
    if 'google_count' in e1:
        e1_count = float(e1['google_count'][bill_id])
    else:
        raise Exception('Count not computed for {}.'.format(e1['name']))

    e2 = db.entities.find_one({'_id':e_e['e2_id']})
    if 'google_count' in e2:
        e2_count = e2['google_count'][bill_id] 

    metrics = {}
    metrics['google_mutual_information'] = log((e_e['google_count']+1)/(e1_count*e2_count+1))
    metrics['google_dice'] = (2*(e_e['google_count']+1))/(e1_count+e2_count+1)
    metrics['google_jaccard'] = ((e_e['google_count']+1)/(e1_count+e2_count-e_e['google_count']+1))
    # Cosine similarity
    e1ks = e1['keywords'].items() 
    e1ks.sort()
     
    e2ks = e2['keywords'].items() 
    e2ks.sort()

    metrics['cosine_similarity_keywords'] = cosine_similarity_keywords(e1ks,e2ks)   

    return metrics

def calculate_metrics(db,bill_id):

    compute_total_google_count(db,bill_id)
    print 'Computed Google count' 
    entities = [db.entities.find_one({'_id':e_id}) for e_id in db.bills.find_one({'id':bill_id})['relevant_entities']]
    for i in range(0,len(entities)-1): 
        print i
        e1 = entities[i]
        for j in range(i+1,len(entities)):
            e2 = entities[j]
            e_e = db.entity_entity.find_one({'$or':[{'e1_id':e1['_id'],'e2_id':e2['_id']},{'e2_id':e1['_id'],'e1_id':e2['_id']}]})
            if e_e is None:
                print e1['_id'], e2['_id']
                if e1['name'] == e2['name']:
                    print 'Continuing'
                    continue
                e_e = {}

                if e1['name'] > e2['name']:
                    e_e['e1_name'] = e2['name']
                    e_e['e2_name'] = e1['name']
                    e_e['e1_id'] = e2['_id']
                    e_e['e2_id'] = e1['_id']
                else:
                    e_e['e1_name'] = e1['name']
                    e_e['e2_name'] = e2['name']
                    e_e['e1_id'] = e1['_id']
                    e_e['e2_id'] = e2['_id']
                e_e['google_count'] = 0
                e_e['bill_id'] = bill_id

            metrics = calculate_metrics_ee(db,bill_id,e_e)
            for (metric,value) in metrics.items():
                e_e[metric] = value
            db.entity_entity.update({'$or':[{'e1_id':e1['_id'],'e2_id':e2['_id']},{'e2_id':e1['_id'],'e1_id':e2['_id']}]},e_e,upsert=True)

def compute_total_google_count(db,bill_id):
    entities = [db.entities.find_one({'_id':e_id}) for e_id in db.bills.find_one({'id':bill_id})['relevant_entities']]

    for e1 in entities:
        count = 0
        for e2 in entities:
            ee = db.entity_entity.find_one({'$or':[{'e1_id':e1['_id'],'e2_id':e2['_id']},{'e2_id':e1['_id'],'e1_id':e2['_id']}]})
            if ee is not None:
                count += ee['google_count']
            else:
                if e1['_id'] != e2['_id']:
                    pass
                    #print('entity-entity relation is null, e1:{} and e2:{}'.format(e1['name'],e2['name']))

        if 'google_count' in e1:
            google_count = e1['google_count']
        else:
            google_count = {}
 
        google_count[bill_id] = count

        db.entities.update({'_id':e1['_id']},{'$set':{'google_count':google_count}})

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
    cosines = []
    for i in range(window_size/2+1,len(scores)-window_size/2):
        v1 = (-1*window_size/2,scores[i-window_size/2])
        v2 = (window_size/2,scores[i+window_size/2])
        n1 = sqrt(v1[0]**2 +v1[1]**2)
        n2 = sqrt(v2[0]**2 +v2[1]**2)
        cos = (v1[0]*v2[0] + v1[1]*v2[1])/(n1*n2)
        cosines.append((cos,i))
        '''
        slope = abs(float(scores[i-window_size/2]-scores[i+window_size/2])/(window_size))
        if slope<epsilon:
            return i
        '''
    for cos in cosines:
        print cos
    return None

def generate_graph(db,bill_id,method):
    if type(method) is list:
        all_links = {}
        for m in method:
            all_links[m] = generate_graph_method(db,bill_id,m)
    else:
        generate_graph_method(db,bill_id,method)
        return

    key_entities = [u'Ricardo', u'Felip Puig', u'Espana', u'Adsera', u'Turistico', u'Hortensia Grau', u'World', u'Veremonte', u'Arturo', u'Gabriel Escarrer', u'Melia', u'Portaventura', u'Macao', u'Artur Mas', u'Singapur', u'Port Aventura', u'Xavier Sabat', u'Enrique Ba\xf1uelos', u'Eurovegas', u'Roca Village', u'Albert Batet', u'Vegas Sands', u'Reus', u'Pere Granados', u'Sheldon Adelson', u'Las Vegas', u'BCN', u'Cataluna', u'Pere Navarro', u'Oriol Amoros', u'Europa', u'Costa Dorada', u'Josep Felix Ballesteros', u'Josep Poblet', u'Damia Calvet', u'Parlament', u'Vila-seca', u'Catalunya', u'Europa Press', u'Value Retail', u'Tarragona', u'Costa Daurada', u'Xavier Adsera', u'Barcelona', u'Barcelona World', u'Xavier Sabate', u'Hard Rock', u'Francesc Perendreu', u'Melco', u'Economia', u'Salou']

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

def generate_graph_method(db,bill_id,metric):
    entities = [db.entities.find_one({'_id':e_id}) for e_id in db.bills.find_one({'id':bill_id})['relevant_entities']]
    relevant_entities = {}
    for entity in entities:
        relevant_entities[entity['name']] = []
        entity_entities = []
        for e_e in db.entity_entity.find({'$or':[{'e1_id':entity['_id']},{'e2_id':entity['_id']}]}):
            for e in entities:
                if (e_e['e1_id'] == e['_id'] or e_e['e2_id'] == e['_id']) and e['_id'] != entity['_id'] and 'google_mutual_information' in e_e:
                    entity_entities.append(e_e)
        values = []
        for e_e in entity_entities:
            if e_e['e1_name'] == entity['name']:
                values.append((e_e[metric],e_e['e2_name'])) 
            else:
                values.append((e_e[metric],e_e['e1_name'])) 

        values.sort(reverse=True)
        cut_point = find_cutting_point([v[0] for v in values])
        for i in range(0,cut_point+1):
            relevant_entities[entity['name']].append(values[i][1])

    links = {}
    for entity in entities:
        links[entity['name']] = []

    for entity in entities:
        for r_e in relevant_entities[entity['name']]:
            if entity['name'] in relevant_entities[r_e] and entity['name']<r_e:
#                print '"{}","{}"'.format(r_e.encode('utf8'),entity['name'].encode('utf8') )
                links[entity['name']].append(r_e)
                links[r_e].append(entity['name'])
    return links

    for x in ['Jara','Albert Batet','Oriol Amoros','Xavier Sabat','Veremonte','Vegas Sands','Xavier Adsera','Adsera','Melco','Gabriel Escarrer','Melia','Value Retail']:
        print x,links[x]
    coms = get_communities_louvain(links)
    for com in coms:
        print com
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
   
def plot(db, bill_id):

    entities = [db.entities.find_one({'_id':e_id}) for e_id in db.bills.find_one({'id':bill_id})['relevant_entities']]

    metrics = ['google_mutual_information', 'google_dice', 'google_jaccard','cosine_similarity_keywords']

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
def main():
    db = MongoClient().catalan_bills
    bill_id = '00062014'
    #calculate_metrics(db,bill_id)
    #plot(db,bill_id)
    generate_graph(db,bill_id,['cosine_similarity_keywords','google_dice'])
#    generate_graph(db,bill_id,'google_dice')
main()
