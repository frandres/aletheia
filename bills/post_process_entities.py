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

def get_entity_documents(entity,index):
    name = entity['name']
    q = {'query': {'bool': {'disable_coord': True, 'must': [{'match_phrase': {'body': {'analyzer': 'analyzer_shingle', 'query': name}}}]}}}
    es = Elasticsearch(timeout=30000)
    results = es.search(index=index, body=q, explain = True, size = 3000)['hits']['hits']
    for result in results:
        print result


'''
Given a name, look it up in the index and return a dictionary containing keywords occurring in the sentences, along with their TF-IDF value
'''
def get_entity_keywords(name,aliases,index,min_freq=2):
  
    q = {'query': {'bool': {'disable_coord': True, 'must': [{'match_phrase': {'body': {'analyzer': 'analyzer_shingle', 'query': name}}}]}}}
    es = Elasticsearch(timeout=30000)
    N = es.count(index = 'catnews_spanish')['count']

    results = es.search(index=index, body=q, explain = True, size = 3000)['hits']['hits']
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

    entities = [db.entities.find_one({'_id':e_id}) for e_id in db.bills.find_one({'id':bill_id})['relevant_entities']]

    entities = [e for e in entities if 'keywords' not in e]

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

def find_cutting_point(scores, bill_id, plot = True, epsilon = 0.2,window_size = 60):
    for i in range(50,len(scores)):
        slope = abs(float(scores[i][0]-scores[i-window_size][0])/(window_size))
        if slope<epsilon:
            if plot:
                plt.plot(range(len(scores)),[score for (score,_) in scores])
                plt.plot(i, scores[i][0], 'ro')
                plt.savefig('./results/article_weight/'+bill_id+'.png')
                plt.clf()
            return i
def compute_relevant_entities_for_bill(db,bill_id):
    print len([eb['entity'] for eb in db.entities_bills.find({'bill':bill_id})])
    db.bills.update({'id':bill_id},{'$set':{'relevant_entities':[eb['entity'] for eb in db.entities_bills.find({'bill':bill_id})]}})
'''
def compute_relevant_entities_for_bill(db,bill_id):
    entity_weight = []
    for eb in db.entities_bills.find({'bill':bill_id}):
        entity = db.entities.find_one({'_id':eb['entity']})
        if entity is not None:
            entity_weight.append(((eb['adjusted_weight'],eb['name']),entity))

    entity_weight.sort(reverse=True,key=get_key)
    num_entities = find_cutting_point([ew[0] for ew in entity_weight],bill_id)
    entities = [ew[1] for ew in entity_weight[0:num_entities]]

    bill = db.bills.find_one({'id':bill_id})

    if 'relevant_entities' in bill:
        existing_entities =bill['relevant_entities']
    else:
        existing_entities = []

    existing_entities = []
    for entity in entities:
        if entity['_id'] not in existing_entities:
            existing_entities.append(entity['_id'])

    for politician in db.politicians_bills.find({'bill':bill_id}):
        if politician['entity_id'] not in existing_entities:
            existing_entities.append(politician['entity_id'])
    print len(existing_entities)
    db.bills.update({'id':bill_id},{'$set':{'relevant_entities':existing_entities}})
'''           
def postprocess_entities():
    conn = MongoClient()
    db = conn.catalan_bills
    index = 'catnews_spanish'
    print 'Setting main tag'
    #set_main_tag(db.entities)
    print 'Normalizing locations'
    #normalize_locations(db.entities)
    print 'Computing IDF'
    bill_id = '00152014'
    bill_id = '00062014'
    #compute_entity_idf_and_adjusted_weight(db)
    #compute_relevant_entities_for_bill(db,bill_id)
    print 'Getting keywords'
    #get_entities_keywords(db,bill_id, 'catnews_spanish')
    #remove_entities_with_low_frequency(db)
    get_entity_documents(db.entities.find_one(),index)

    
postprocess_entities()
