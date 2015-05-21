from pymongo import MongoClient
from bisect import bisect_left
from entities_functions import merge_entities
from collections import defaultdict
import matplotlib.pyplot as plt
from elasticsearch import Elasticsearch
from string import punctuation
from multiprocessing import Process

stopwords = ["de","la","que","el","en","y","a","los","del","se","las","por","un","par","con","no","una","su","al","lo","com","mas","per","sus","le","ya","o","este","si","porqu","esta","entre","cuand","muy","sin","sobr","tambi","me","hast","hay","dond","qui","desd","tod","nos","durant","tod","uno","les","ni","contr","otros","ese","eso","ante","ellos","e","esto","mi","antes","algun","que","unos","yo","otro","otras","otra","el","tant","esa","estos","much","quien","nad","much","cual","poc","ella","estar","estas","algun","algo","nosotr","mi","mis","tu","te","ti","tu","tus","ellas","nosotr","vosostr","vosostr","os","mio","mia","mios","mias","tuy","tuy","tuy","tuy","suy","suy","suy","suy","nuestr","nuestr","nuestr","nuestr","vuestr","vuestr","vuestr","vuestr","esos","esas","estoy","estas","esta","estam","estais","estan","este","estes","estem","esteis","esten","estar","estar","estar","estar","estareis","estar","estari","estari","estari","estariais","estari","estab","estab","estab","estabais","estab","estuv","estuv","estuv","estuv","estuv","estuv","estuv","estuv","estuvier","estuv","estuv","estuv","estuv","estuvies","estuv","estuv","estand","estad","estad","estad","estad","estad","he","has","ha","hem","habeis","han","hay","hay","hay","hayais","hay","habr","habr","habr","habr","habreis","habr","habri","habri","habri","habriais","habri","habi","habi","habi","habiais","habi","hub","hub","hub","hub","hub","hub","hub","hub","hubier","hub","hub","hub","hub","hubies","hub","hub","hab","hab","hab","hab","hab","soy","eres","es","som","sois","son","sea","seas","seam","seais","sean","ser","ser","ser","ser","sereis","ser","seri","seri","seri","seriais","seri","era","eras","eram","erais","eran","fui","fuist","fue","fuim","fuisteis","fueron","fuer","fuer","fuer","fuerais","fuer","fues","fues","fues","fueseis","fues","sint","sent","sent","sent","sent","sient","sent","teng","tien","tien","ten","teneis","tien","teng","teng","teng","tengais","teng","tendr","tendr","tendr","tendr","tendreis","tendr","tendri","tendri","tendri","tendriais","tendri","teni","teni","teni","teniais","teni","tuv","tuv","tuv","tuv","tuv","tuv","tuv","tuv","tuvier","tuv","tuv","tuv","tuv","tuvies","tuv","tuv","ten","ten","ten","ten","ten","ten"]

from nltk.tokenize import sent_tokenize

from nltk.stem import SnowballStemmer
from math import log,sqrt

'''
Given a sentence, return 1,2,3-grams and do stemming and stopword removal
'''
def sentence2ngrams(sentence, max_size = 2):
    for sign in punctuation:
        sentence = sentence.replace(sign,'')
    stemmer = SnowballStemmer('spanish')
    words = []
    for word in sentence.split():
        try:
            words.append(stemmer.stem(word.decode('utf8')))
        except Exception as e:
            words.append(word)

    words = [word for word in words if word not in stopwords]
    ngrams = [word for word in words]
    for i in range(1,max_size):
        for j in range(0,len(words)-i):
            ngrams.append(' '.join(words[j:j+i+1]))
    return ngrams

def get_key(item):
    return item[0]

'''
Given a name, look it up in the index and return a dictionary containing keywords occurring in the sentences, along with their TF-IDF value
'''
def get_entity_keywords(name,aliases,index,min_freq=2):

    
    q = {'query': {'bool': {'disable_coord': True, 'must': [{'match_phrase': {'body': {'analyzer': 'analyzer_shingle', 'query': name}}}]}}}
    es = Elasticsearch(timeout=300)
    N = es.count(index = 'catnews_spanish')['count']

    results = es.search(index=index, body=q, explain = True, size = 3000,search_type = 'dfs_query_then_fetch')['hits']['hits']
    n_grams = {}

    if name not in aliases:
        aliases.append(name)
    aliases = [alias.encode('utf8') for alias in aliases]
    for result in results:
        article = result['_source']['body']
        sentences = sent_tokenize(article)
        for sentence in sentences:
            sentence = sentence.encode('utf8')
            for alias in aliases:
                if alias in sentence:
                    for n_gram in sentence2ngrams(sentence):
                        if n_gram in n_grams:
                            n_grams[n_gram]['freq']+=1
                        else:
                            n_grams[n_gram] = {}

                            n_grams[n_gram]['freq'] = 1
                    break

    filtered_n_grams = {}
    for (n_gram,value) in n_grams.items():
        if value['freq'] >= min_freq:
            q = {'query': {'bool': {'must': [{'match_phrase': {'body': {'analyzer': 'analyzer_keywords2', 'query': n_gram}}}]}}}
            results = es.search(index=index, body=q, explain = True,search_type = 'dfs_query_then_fetch')['hits']['hits']
            document_count = es.search(index=index, body=q, explain = True,search_type = 'dfs_query_then_fetch')['hits']['total']
            if document_count >0:
                value['idf'] = log(N/document_count) 
                filtered_n_grams[n_gram] = value['idf'] *value['freq']

    return filtered_n_grams

def get_entities_keywords(db,bill_id, index,num_threads = 10):

    entity_weight = []
    for eb in db.entities_bills.find({'bill':bill_id}):
        entity = db.entities.find_one({'_id':eb['entity']})
        if entity is not None:
            entity_weight.append(((eb['adjusted_weight'],eb['name']),entity))

    entity_weight.sort(reverse=True,key=get_key)
    num_entities = find_cutting_point([ew[0] for ew in entity_weight],bill_id)

    print num_entities
    entities = [e[1] for e in entity_weight[0:num_entities] if e[1] is not None and 'keywords'not in e[1]]

    print len(entities)
    processes = []
    collection = db.entities
    for i in range(0,num_threads):
#        print 0+i* len(entities)/num_threads,(i+1)* len(entities)/num_threads
        p = Process(target=get_entities_keywords_process, args=(entities[0+i* len(entities)/num_threads:(i+1)* len(entities)/num_threads],index,collection))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

def get_entities_keywords_process(entities, index,collection):
    i = 0
    for entity in entities:
        i+=1
        kws = get_entity_keywords(entity['name'],entity['aliases'],index)
        print entity['name']
        print len(kws.values())
        collection.update({'_id':entity['_id']},{'$set':{'keywords':kws}})
        print 'keywords' in collection.find_one({'_id':entity['_id']})

def compute_total_google_count(db,bill_id):

    ees= [ee for ee in db.entity_entity.find({'bill_id':bill_id})]
    entities = []
    for ee in ees:
        if ee['e1_id'] not in entities:
            entities.append(ee['e1_id'])
        if ee['e2_id'] not in entities:
            entities.append(ee['e2_id'])

    print len(entities)

    for e in entities:
        count = 0
        for ee in db.entity_entity.find({'bill_id':bill_id,'e1_id':e}):
            count += ee['google_count']
            
        for ee in db.entity_entity.find({'bill_id':bill_id,'e2_id':e}):
            count += ee['google_count']

        db.entities.update({'_id':e},{'$unset':{'google_count':1}})
        db.entities.update({'_id':e},{'$set':{'google_count':{bill_id:count}}})
'''
Fetch all entities from the Database, 
compute the most frequent tag,
and set a field called 'tag' with that value.
'''
def set_main_tag(collection):
    
    for entity in collection.find():
        if 'tag'in entity.keys():
            continue
        tags = [(y,x) for (x,y) in entity['tags'].items()]
        tags.sort(reverse=True)
        tag = tags[0][1]
        collection.update({'name':entity['name']},{'$set':{'tag':tag}})

'''
Compute the IDF and the adjusted score of every entity and every entity-bill relationship.
The IDF is computed counting the number of topics the entity is related to and counting the total number of topics
there are. (log(TOTAL/count_entity)).
The adjusted score is the IDF times the weight of the relationship between the entity and the bills.
'''
def compute_entity_idf_and_adjusted_weight(db):
    total_topics = float(db.bills.count())
    for entity in db.entities.find():
        idf = log(total_topics/len(entity['bills']))
        db.entities.update({'_id':entity['_id']},{'$set':{'topic_idf':idf}})
        entity_bills = [eb for eb in db.entities_bills.find({'entity':entity['_id']})]
        for eb in entity_bills:
            db.entities_bills.update({'_id':eb['_id']},{'$set':{'entity_idf':idf}})
            db.entities_bills.update({'_id':eb['_id']},{'$set':{'adjusted_weight':idf*eb['weight']['value']}})
            
'''
Fetch all locations from the Database,
fetch all entities and check if by camelizing the names we match non-location entities with locations
This solves the problem of locations like CATALUNYA, BARCELONA that are in uppercase and not recognize
by the system as a location.
'''
def normalize_locations(collection):
    locations = [camelize(entity['name']) for entity in collection.find({'tag':'LOCATION'})]
    locations.sort()

    for entity in collection.find():
        name = camelize(entity['name'])
        # If it is already camelized, it doesn't make sense to analyze it again.
        if name == entity['name']:
            continue 
        # Otherwise, check if by camelizing it we recognize one of the locations.
        i = bisect_left(locations,name)
        if i == len(locations) or locations[i] != name:
            continue
      
        # If it matches a location, merge it with the location.

        # Check if there is a camelized version in the database; otherwise update this entity:
        cursor = collection.find({'name':name})
        if cursor.count() >1:
            raise Exception('Non unique entity')

        #print name
        if cursor.count() ==0 :
            
            #print 'Updating'
            #print entity
            #print 'New name: '+ name
            collection.update({'name':entity['name']},{'$set':{'name':name}})
        else:
            print 'Merging'
            print entity
            merge_entities(entity,{'name':name},collection,drop=True)
        print ''

'''
Given an entity, return the number of times it occurs accross all bills in the database. 
'''
def get_entity_freq(db,entity):
    collection = db.entities_bills
    cursor = collection.find({'name':entity['name']})
    freq = 0
    for entity_bill in cursor:
        freq+= entity_bill['freq']
    return freq
'''
This function goes through the list of found entities and removes entities with very low frequency.
This is useful for noise reduction (ie removing mistaken entities)
'''
def remove_entities_with_low_frequency(db,min_freq=3):
    collection = db.entities
    i = 0
    for entity in collection.find():
        freq = get_entity_freq(db,entity)
        if freq<=min_freq:
            i+=1
            print entity['name']
           
            #collection.remove({'name': entity['name']})
    print i


def find_comparable_entities(db):

    eb_col = db.entities_bills
    e_col = db.entities
    entity_bills = defaultdict(lambda: [])

    for eb in eb_col.find():
        try:
            entity = e_col.find({'_id':eb['entity']})[0]
        except Exception:
            continue
        if entity['tag'] != 'LOCATION':
            entity_bills[eb['bill']].append(entity['name'])

    c= 0 
    for (key,value) in entity_bills.items():
        print 'Bill: {} has {} entities, which make {} possible links'.format(key,len(value),len(value)**2)
        c+= len(value)**2
    print c
    '''
    entity_entity = defaultdict(lambda:[])
    
    bill_comparable_entities = db.bill_comparable_entities

    for (key,value) in entity_bills.items():
        print 'Bill: {}'.format(key)
        value.sort()
        print ' GO: {}'.format(len(value))
        #bill_comparable_entities.insert({'bill':key,'entities':value})
        for i in range(0,len(value)-1):
            print i
            for j in range(i+1,len(value)):
                if value[j] not in entity_entity[value[i]]:
                    entity_entity[value[i]].append(value[j])
    '''
        
    comparable_entities = db.comparable_entities
    
    for (key,value) in entity_entity:
        comparable_entities.insert({'entity':key,'comparable_entities':value})    

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
            print 'TRUE'
            product+= e1k[1] * e2k[1]

            if e1_i< len(e1ks):
                norm_e1 += e1k[1] * e1k[1]
                e1_i+=1

            if e2_i< len(e2ks):
                norm_e2 += e2k[1] * e2k[1]
                e2_i+=1

        if e1k[0] < e2k[0] or e2_i == len(e2ks):
            if e1_i< len(e1ks):
                norm_e1 += e1k[1] * e1k[1]
                e1_i+=1
        if e1k[0] > e2k[0] or e1_i == len(e1ks):
            if e2_i< len(e2ks):
                norm_e2 += e2k[1] * e2k[1]
                e2_i+=1


    norm_e1 = sqrt(norm_e1)            
    norm_e2 = sqrt(norm_e2)            

     
    if product >0:
        product = product/(norm_e1*norm_e2)   

    return product
def calculate_metrics_ee(db,bill_id,e_e):
    e1 = db.entities.find_one({'_id':e_e['e1_id']})
    if 'google_count' in e1:
        e1_count = e1['google_count'][bill_id] +1
    else:
        return None

    e2 = db.entities.find_one({'_id':e_e['e2_id']})
    if 'google_count' in e2:
        e2_count = e2['google_count'][bill_id] +1
    else:
        return None

    metrics = {}
    metrics['google_mutual_information'] = log((e_e['google_count']+1)/(e1_count*e2_count))
    metrics['google_dice'] = (2*(e_e['google_count']+1)/(e1_count+e2_count))
    metrics['google_jaccard'] = ((e_e['google_count']+1)/(e1_count+e2_count-e_e['google_count']+1))

    # Cosine similarity
    e1ks = e1['keywords'].items() 
    e1ks.sort()
     
    e1ks = e1['keywords'].items() 
    e2ks.sort()

    metrics['cosine_similarity_keywords'] = cosine_similarity_keywords(e1ks,e2ks)   

    return metrics

def find_cutting_point(scores, bill_id,epsilon = 0.001,window_size = 50):
    for i in range(50,len(scores)):
        slope = abs(float(scores[i][0]-scores[i-window_size][0])/(window_size))
        if slope<epsilon:
            plt.plot(range(len(scores)),[score for (score,_) in scores])
            plt.plot(i, scores[i][0], 'ro')
            plt.savefig('./plots_entities_bills/'+bill_id+'.png')
            plt.clf()
            return i

def calculate_metrics(db,bill_id):
    entity_weight = []
    for eb in db.entities_bills.find({'bill':bill_id}):
        entity = db.entities.find_one({'_id':eb['entity']})
        if entity is not None:
            entity_weight.append(((eb['adjusted_weight'],eb['name']),entity))

    entity_weight.sort(reverse=True,key=get_key)
    num_entities = find_cutting_point([ew[0] for ew in entity_weight],bill_id)
    entities = [ew[1] for ew in entity_weight[0:num_entities]]

    for i in range(0,len(entities)-1): 
        e1 = entities[i]
        for j in range(i+1,len(entities)):
            e2 = entities[j]
            e_e = db.entity_entity.find_one({'e1_id':e1['_id'], 'e2_id':e2['_id']})
            if e_e is None:
                raise Exception('entity-entity relation is null, e1:{} and e2:{}'.format(e1['name'],e2['name']))
            metrics = calculate_metrics_ee(db,bill_id,e_e)
            for (metric,value) in metrics.items():
                db.entity_entity.update({'_id':e_e['_id']},{'$set':{metric:value}})
            
def postprocess_entities():
    conn = MongoClient()
    db = conn.catalan_bills
    print 'Setting main tag'
    #set_main_tag(db.entities)
    print 'Normalizing locations'
    #normalize_locations(db.entities)
    print 'Finding comparable entities'
    #find_comparable_entities(db)
    print 'Computing IDF'
    #compute_entity_idf_and_adjusted_weight(db)
    get_entities_keywords(db,'00062014', 'catnews_spanish')
    #remove_entities_with_low_frequency(db)
    #compute_total_google_count(db,'00062014')
    #calculate_metrics(db,'00062014')

def camelize(string):
    to_upper_case = True
    new_string = ''
    for x in string:
        if to_upper_case:
            new_string+=x.upper()
        else:
            new_string+=x.lower()

        to_upper_case = x == ' '
    return new_string

postprocess_entities()
