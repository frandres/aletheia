from gensim import corpora, models, similarities
from gensim.models.lsimodel import LsiModel
from pymongo import MongoClient
import math
from collections import defaultdict
import cPickle as pickle
from bisect import bisect_left
import os.path
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.cm as cm
from elasticsearch import Elasticsearch
import scipy.cluster.hierarchy as hac
from math import sqrt

from sklearn import metrics

def entities2bill_documents(bill_id,db):
    bill_articles = db.bills.find_one({'id':bill_id})['bill_articles_ids']
    article2column = {}
    i=0
    for article in bill_articles:
        article2column[article] = i
        i+=1
    entity2row = {}
    matrix = []         
    i=0
    es = Elasticsearch()
    for eb in db.entities_bills.find({'bill':bill_id}):
        if 'bill_articles_ids' in eb and len(eb['bill_articles_ids'])>0:
            entity_vector = []
            q = {"query": {'match_phrase': {'body': {'analyzer': 'analyzer_shingle','query': eb['name']}}}}
            if es.count(index='catnews_spanish',body=q)['count']<2:
                continue
            for article in eb['bill_articles_ids']:
                entity_vector.append((article2column[article],1.0))
            entity2row[eb['entity']] = i
            i+=1
            matrix.append(entity_vector)
        else:
            pass
    return (matrix,entity2row)

def build_distance(corpus,entities,entity2row,seeds):

    matrix = []

    lsi = LsiModel(corpus=corpus, num_topics=10)

    sim = similarities.MatrixSimilarity(lsi[corpus])

    # Require that the entity have a minimum similarity with the seeds:
    possible_entities = []
    for n1 in entities:
        for n2 in seeds:
            if sim[lsi[corpus[entity2row[n1]]]][entity2row[n2]]>0.2:
                possible_entities.append(n1)
                break

    for n1 in possible_entities:
        vector = []
        comp = lsi[corpus[entity2row[n1]]]
        for n2 in possible_entities:
            if n1 == n2:
                vector.append(0.0)
            else:
                vector.append(min(1.0,1.0-sim[comp][entity2row[n2]]))
        matrix.append(vector)
    return (np.array(matrix),possible_entities)

def find_relevant_entities(db,bill_id,seeds):

    (corpus,entity2row) = entities2bill_documents(bill_id,db)
     
    entities = entity2row.keys()
    print 'Initial size: {}'.format(len(entities))

    seed_ids = []
    for seed in seeds:
        if seed in entities:
            seed_ids.append(seed)

    (distance_matrix,entities)= build_distance(corpus,entities,entity2row,seed_ids)
    print 'Prefiltered size: {}'.format(len(entities))
    
    print 'Distance matrix computed' 
    seeds_indices = [entities.index(x) for x in seed_ids]

    return find_best_cluster(distance_matrix,entities,seeds_indices)

def find_best_cluster(distance_matrix,entities,seeds_indices,minimum_size =100):
    linkage_matrix = hac.linkage(distance_matrix, method='average', metric='euclidean') #single, average

    relevant_thresholds =  np.concatenate(([0],np.array(linkage_matrix[:,2])), axis=0)
    relevant_thresholds = relevant_thresholds.tolist()
    relevant_thresholds.reverse()
    thresholds_silhoutte = []
    prev_cluster_size = len(entities)+1

    for t in relevant_thresholds[1:len(relevant_thresholds)]:
        clusters_list = hac.fcluster(linkage_matrix, t, criterion='distance')
       
        '''
        next_t = False
        for s1 in seeds:
            for s2 in seeds:
                if s1 == s2:
                    continue
                if clusters_list[s1] != clusters_list[s2]:
                    next_t = True
                    break
        if next_t:
            continue
        '''

        mask = clusters_list == clusters_list[seeds_indices[0]]
        new_cluster = np.array(entities)[mask]
        if len(new_cluster)<minimum_size:
            if len(thresholds_silhoutte)==0:
                thresholds_silhoutte.append((1,t))

            break
        if prev_cluster_size != len(new_cluster):
            prev_cluster_size = len(new_cluster)
            #print prev_cluster_size
            silhoutte = np.mean(metrics.silhouette_samples(distance_matrix , clusters_list, metric='precomputed')[mask])
            thresholds_silhoutte.append((silhoutte,t))
            print silhoutte,prev_cluster_size
            '''

            print t-prev_threshold
            prev_threshold = t

            '''
    silhouttes = [x[0] for x in thresholds_silhoutte]
    optimum_i = silhouttes.index(max(silhouttes))
    optimum_threshold = thresholds_silhoutte[optimum_i][1]
    clusters_list = hac.fcluster(linkage_matrix, optimum_threshold, criterion='distance')
    mask = clusters_list == clusters_list[seeds_indices[0]]
    return np.array(entities)[mask].tolist()

