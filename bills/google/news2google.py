from multiprocessing import Process
from time import sleep
from random import random
from bisect import bisect_left

from pymongo import MongoClient
import pymongo
from google import ask_google_individual, ask_google_pairs
import matplotlib.pyplot as plt
from math import log, floor

def find_cutting_point(scores, bill_id,epsilon = 0.001,window_size = 50):
    for i in range(50,len(scores)):
        slope = abs(float(scores[i][0]-scores[i-window_size][0])/(window_size))
        if slope<epsilon:
            return i

def ask_google_process_individual(all_entities,db):

    # First we filter out entities for which we have already used google.

    entities_to_query = [e for e in all_entities if 'google_count'not in e]
    # Hit google
    for (entity,results) in ask_google_individual(entities_to_query):
        db.entities.update({'_id':entity['_id']},{'$set':{'google_count':results}})
                
def ask_google_process_pairs(ent_analyze,all_entities,bill_id,db):

    # First we filter out entities for which we have already used google.

    entities_already_analyzed = []
    cursor = db.entity_entity.find({'e1_id':ent_analyze['_id']})
    for e in cursor:
        if e['e2_id'] not in entities_already_analyzed:
            entities_already_analyzed.append(e['e2_id'])
    
    cursor = db.entity_entity.find({'e2_id':ent_analyze['_id']})
    for e in cursor:
        if e['e1_id'] not in entities_already_analyzed:
            entities_already_analyzed.append(e['e1_id'])

    entities_already_analyzed.sort()

    entities_to_query = []

    for entity in all_entities:
        index = bisect_left(entities_already_analyzed,entity['_id'])
        if index == len(entities_already_analyzed) or entities_already_analyzed[index] != entity['_id']:
            entities_to_query.append(entity)
    '''
    num_threads = floor(len(entities_to_query)/800)+1
    processes = []
    
    for thread in range(0,num_threads):
        p = Process(target=ask_google_pairs, args=(ent_analyze,entities_to_query[floor(thread* len(entities_to_query)/num_threads):floor((thread+1)* len(entities_to_query)/num_threads)]))
        p.start()
        sleep(35)
        processes.append(p)

    for proc in processes:
        proc.join()
    '''
    # Hit google
    results = ask_google_pairs(ent_analyze,entities_to_query)
    for (entity,results) in results:
        if ent_analyze['name'] < entity['name']:
            e1 = ent_analyze
            e2 = entity
        else:
            e1 = entity
            e2 = ent_analyze

        db.entity_entity.insert({'bill_id':bill_id,'e1_id':e1['_id'],'e2_id':e2['_id'],'google_count':results,'e1_name':e1['name'],'e2_name':e2['name']})

def are_linked(ent_ana,entity):
    return random()<0.0005

def run_bfs_iteration(entities_to_analyze,entities_analyzed,all_entities):
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
    
def analyze_bill(db,bill_id,max_depth=3):

    politicians = []
    for politician_bill in db.politicians_bills.find({'bill':bill_id}):
        entity = db.entities.find_one({'_id':politician_bill['entity_id']})
        politicians.append(entity)
        
    all_entities = []
    for entity_bill in db.entities_bills.find({'bill':bill_id}):
        entity = db.entities.find_one({'_id':entity_bill['entity']})
        if entity is not None and entity['tag'] in ['PERSON','ORGANIZATION','MISC']:
            all_entities.append(entity)

    # Get the individual counts
    proc = Process(target=ask_google_process_individual, args=(all_entities,db,))
    proc.start()
    
    entities_analyzed = []
    # And the counts with politicians
    entities_to_analyze = run_bfs_iteration(politicians,entities_analyzed,all_entities)

    proc.join()

    # Now let's generate the rest of the graph based on the results.
    for i in range(0,max_depth):
        print ('Analyzing {}'.format(entities_to_analyze))
        entities_to_analyze = run_bfs_iteration(entities_to_analyze,entities_analyzed,all_entities)
        print ('Found {}'.format(entities_to_analyze))
        print ('')

def get_key(x):
    return x[0]

def all_vs_all(db,bill_id):
    entity_weight = []
    for eb in db.entities_bills.find({'bill':'00062014'}):
        entity = db.entities.find_one({'_id':eb['entity']})
        if entity is not None:
            entity_weight.append((eb['adjusted_weight'],entity))

    entity_weight.sort(reverse=True,key=get_key)
    num_entities = find_cutting_point(entity_weight,bill_id)
    print (num_entities)
    entities = [ew[1] for ew in entity_weight[0:num_entities]]

    processes = []


    for i in range(67,len(entities)-1): # CHANGE THIS to 50
        print('Entity: {},{}'.format(i,entities[i]['name']))
        ask_google_process_pairs(entities[i],entities[i+1:len(entities)],bill_id,db)

'''
        processes.append(proc)
        sleep(15)
        running_threads = len(processes)
        if running_threads >= 2:
            print('Waiting for workers to finish')
            alive_running_threads = running_threads
            while alive_running_threads == running_threads:
                sleep(60)
                alive_processes = [p for p in processes if p.is_alive()]
                alive_running_threads = len(alive_processes)

            processes = alive_processes

            
  #          for p in processes:
   #             p.join()
    #        processes = []
     #       running_threads = 0
            
            print('Resuming, {}'.format(len(processes)))
            print('Entity: {}'.format(i))
        
    for p in processes:
        p.join()
'''
def preliminary(db,bill_id):

    politicians = []
    for politician_bill in db.politicians_bills.find({'bill':bill_id}):
        entity = db.entities.find_one({'_id':politician_bill['entity_id']})
        politicians.append(entity)
        
    entities = []
    for entity_bill in db.entities_bills.find({'bill':bill_id}):
        entity = db.entities.find_one({'_id':entity_bill['entity']})
        if entity is not None and entity['tag'] in ['PERSON','ORGANIZATION','MISC']:
            entities.append(entity)
    '''
    proc = Process(target=ask_google_process_individual, args=(entities,db,))
    proc.start()
    processes = [proc]    
    '''
    processes = []
    for politician in politicians:
        proc = Process(target=ask_google_process_pairs, args=(politician,entities,db,))
        proc.start()
        processes.append(proc)
        sleep(30)


    for proc in processes:
        proc.join()

def calculate_metrics(db, e_e):
    e1 = db.entities.find_one({'_id':e_e['e1_id']})
    if 'google_count' in e1:
        e1_count = e1['google_count'] +1
        if e1_count<50:
            return None
    else:
        return None

    e2 = db.entities.find_one({'_id':e_e['e2_id']})
    if 'google_count' in e2:
        e2_count = e2['google_count'] +1
        if e2_count<50:
            return None
    else:
        return None


    e1_bill = db.entities_bills.find_one({'entity':e1['_id']})
    e2_bill = db.entities_bills.find_one({'entity':e2['_id']})
    e1_factor = e1_bill['weight']['value']
    e2_factor = e2_bill['weight']['value']


    #print(e1_count,e2_count,e_e['google_count'],((e_e['google_count']+1)/(e1_count+e2_count-e_e['google_count']+1)))
    d = {'e1_name': e1['name'],'e2_name': e2['name'] , 'mutual_information':log((e_e['google_count']+1)/(e1_count*e2_count)),'dice': (2*(e_e['google_count']+1)/(e1_count+e2_count)), 'jaccard': ((e_e['google_count']+1)/(e1_count+e2_count-e_e['google_count']+1)), 'e1_topic_relationship':e1_factor, 'e2_topic_relationship':e2_factor,'count':e_e['google_count'],'ee_topic':e1_factor*e2_factor,'e1_count': e1_count, 'e2_count': e2_count}

    d['mutual_information_adjusted'] = d['mutual_information'] * d['ee_topic']
    d['count_adjusted'] = d['count'] * d['ee_topic']
    d['jaccard_adjusted'] = d['jaccard'] * d['ee_topic']
    d['dice_adjusted'] = d['dice'] * d['ee_topic']
    return d

def get_key(item):
    return item[0]

def plot_bill(db,bill_id, politicians):
    for politician in politicians:

        entity_entity_metrics = []

        # Compute the metrics

        for e_e in db.entity_entity.find({'e1_name':politician}):
            metric = calculate_metrics(db, e_e)
            if metric is not None:
                entity_entity_metrics.append(metric)

        for e_e in db.entity_entity.find({'e2_name':politician}):
            metric = calculate_metrics(db, e_e)
            if metric is not None:
                entity_entity_metrics.append(metric)

        plot_bill_(db,bill_id, politician, entity_entity_metrics)

def plot_bill_(db,bill_id, politician,entity_entity_metrics):
    politician = politician.replace(' ','_')
    # Normalize the mutual information
    min_mi = 0
    for metric in entity_entity_metrics:
        min_mi = min(min_mi,metric['mutual_information'])

    for metric in entity_entity_metrics:
        metric['mutual_information']-= min_mi
    
    # Plot the metrics

    for metric_name in ['jaccard','jaccard_adjusted','count','count_adjusted','mutual_information','mutual_information_adjusted','dice','dice_adjusted']:


        metrics_values = [(metric[metric_name],metric) for metric in entity_entity_metrics]
        metrics_values.sort(reverse=True,key=get_key)


        if metric_name == 'jaccard':
            for (_,metric) in metrics_values[len(metrics_values)-100:len(metrics_values)]:
                print('Jaccard: {}: together: {}, e1: {}, e2: {}'.format(metric['jaccard'],metric['count'],metric['e1_count'],metric['e2_count']))

        plt.plot(range(len(metrics_values)),[metric[0] for metric in metrics_values])
        plt.savefig('./plots/'+politician+'/'+bill_id+'_'+metric_name+'.png')
        plt.clf()

        f = open('./plots/'+politician+'/'+bill_id+'_'+metric_name+'.txt', 'w')

        i = 0
        for (value,metric) in metrics_values[0:1000]:
            f.write('Index: {}; entities {} and {}. Value: {}\n'.format(i,metric['e1_name'], metric['e2_name'],value))
            i+=1
        f.close()
        '''
        entities_bills = []
        for eb in db.entities_bills.find({'bill':bill_id}):
            entities_bills.append((eb['weight']['value'],eb['name']))
        entities_bills.sort(reverse=True)

        for eb in entities_bills[0:100]:
            print (eb)
        '''
def main():
    conn = MongoClient()
    db = conn.catalan_bills
    bill = '00062014' #['00152014','00202014']
    bill = '00062014'
    #analyze_bill(db,bill)
    all_vs_all(db,bill)
    #plot_bill(db,bill,['Albert Batet','Xavier Sabat', 'Oriol Amoros'])

main()

