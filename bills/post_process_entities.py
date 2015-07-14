from pymongo import MongoClient
from bisect import bisect_left
from entities_functions import merge_entities
from collections import defaultdict
import matplotlib.pyplot as plt
from elasticsearch import Elasticsearch
from string import punctuation
from multiprocessing import Process
from elasticsearch import helpers
from entity_similarity import find_relevant_entities
import ngram
import sys
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

def get_entities_documents(bill,index,db,overwrite=True):
    bill_articles = db.bills.find_one({'id':bill})['bill_articles_ids']
    i = 0
    for eb in db.entities_bills.find({'bill':bill}):
        entity = db.entities.find_one({'_id':eb['entity']})
        i+=1
        if entity is not None:
            print i
            if 'articles_ids' not in entity:
                docs = get_entity_documents(entity,index)
                #db.entities.update({'_id':entity['_id']},{'$set':{'articles_ids':docs}})
            else:
                docs = entity['articles_ids']
            if 'bill_articles_ids' not in eb or overwrite:
                bill_articles_ids = []
                for ea_id in docs:
                    if ea_id in bill_articles:
                        bill_articles_ids.append(ea_id)
                bill_articles.sort()
                print entity['name'], len(bill_articles_ids)
                db.entities_bills.update({'_id':eb['_id']},{'$set':{'bill_articles_ids':bill_articles_ids}})

def get_entity_documents(entity,index):
    name = entity['name']
    q = {'query':{'bool': {'disable_coord': True, 'must': [{'match_phrase': {'body': {'analyzer': 'analyzer_shingle', 'query': name}}}]}}}
    es = Elasticsearch(timeout=30000)
    docs = []
    for d in helpers.scan(es,index = index,query=q,size=1000):
        docs.append(d['_id'])
    docs.sort()
    return docs



'''
Given a name, look it up in the index and return a dictionary containing keywords occurring in the sentences, along with their TF-IDF value
'''
def get_entity_keywords(entity,index,bill_articles,bill_entity_articles,min_freq=2):
    name = entity['name']

    aliases = entity['aliases']
    print name,aliases

    if name not in aliases:
        aliases.append(name)
 
    contexts = []
    es = Elasticsearch(timeout=30000)
    for alias in aliases:
        q = {"query": {"bool": {"must": [{"filtered" : {"filter" : {"terms": {"article_id": bill_entity_articles}}}},{'match_phrase': {'body': {'analyzer': 'analyzer_shingle','query': alias}}}]}}}
        for context in helpers.scan(es,index = index,query=q):
            contexts.append(context['_source']['body'].encode('utf8'))

    print ' {}'.format(len(contexts))
    if len(contexts)>100000:
        print ' Sorry, too long'
        return None

    n_grams = {}
    print ' Sentences sorted. Now getting ngrams '
    for context in contexts:
        context = context.decode('utf8')
        for sentence in sent_tokenize(context):
            for n_gram in sentence2ngrams(sentence):
                if n_gram in n_grams:
                    n_grams[n_gram]['freq']+=1
                else:
                    n_grams[n_gram] = {}
                    n_grams[n_gram]['freq'] = 1

    print ' {} ngrams found. Generating vector space representation'.format(len(n_grams))
    filtered_n_grams = {}

    q = {"query": {"filtered" : {"filter" : {"terms": {"article_id": bill_articles}}}}}
    N = es.count(index=index,body=q)['count']

    for (n_gram,value) in n_grams.items():
        if value['freq'] >= min_freq:
            q = {"query": {"bool": {"must": [{"filtered" : {"filter" : {"terms": {"article_id": bill_articles}}}},{'match_phrase': {'body': {'analyzer': 'analyzer_keywords2','query': n_gram}}}]}}}
            document_count = es.count(index=index,body=q)['count']
            if document_count >0:
                value['idf'] = log(N/document_count)
                 
                filtered_n_grams[n_gram] = value['idf'] *(1.0+log(value['freq']))

    print ' Done'
    return filtered_n_grams

def reduce_size_vectors(entity,kws):
    e_size = sys.getsizeof(entity)
    max_size = (14*1024*1024-e_size)


    pairs = [(value,key) for (key,value) in kws.items()]
    pairs.sort(reverse=True)
    new_dict = {}
    i = 0
    while i<len(pairs) and sys.getsizeof(new_dict)< max_size:
        pair = pairs[i]
        new_dict[pair[1]]=pair[0]
        i+=1

    return new_dict
def get_entities_keywords(db,bill_id, s_index,f_index,filter_by_bill=True,overwrite=True):

    i=0
    rel_entities_bill = db.bills.find_one({'id':bill_id})['relevant_entities']    
    print len(rel_entities_bill)
    bill_articles = []
    for e in rel_entities_bill:
        eb  = db.entities_bills.find_one({'bill':bill_id,'entity':e})
        for article_id in eb['bill_articles_ids']:
            if article_id not in bill_articles:
                bill_articles.append(article_id)

    for e in rel_entities_bill:
        i+=1
        
        eb  = db.entities_bills.find_one({'bill':bill_id,'entity':e})
        if 'entity_keywords' in eb and not overwrite:
            continue
        print i

        if eb is not None and 'bill_articles_ids' in eb:
            valid_articles = eb['bill_articles_ids']
        else:
            print 'No articles defined for {}'.format(entity['name'])
            continue

        if len(valid_articles) ==0:
            print 'No articles for {}'.format(entity['name'].encode('utf8'))
            continue

        entity = db.entities.find_one({'_id':e})
        kws = get_entity_keywords(entity,s_index,bill_articles,valid_articles)

        if kws is not None:
            db.entities_bills.update({'bill':bill_id,'entity':entity['_id']},{'$set':{'entity_keywords':kws}})
        else:
            print 'None kws',e
                    

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
'''
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
'''
'''
def compute_relevant_entities_for_bill(db,bill_id):

    print len([eb['entity'] for eb in db.entities_bills.find({'bill':bill_id})])
    db.bills.update({'id':bill_id},{'$set':{'relevant_entities':[eb['entity'] for eb in db.entities_bills.find({'bill':bill_id})]}})

'''
def fix_tags(db,bill_id):
    for e_id in db.bills.find_one({'id':bill_id})['relevant_entities']:
        entity = db.entities.find_one({'_id':e_id})
        print entity['name'],entity['tag']
        x = raw_input('Fix tag?')
        if x in ['PERSON','LOCATION','ORGANIZATION','MISC']:
            print x
            db.entities.update({'_id':e_id},{'$set':{'tag':x}})

def eliminate_duplicated_entities(db,bill_id):

    new_relevant_entities = []
    entities = []
    for e_id in db.bills.find_one({'id':bill_id})['relevant_entities']:
        e_b = db.entities_bills.find_one({'bill':bill_id,'entity':e_id})
        if db.entities.find_one({'_id':e_id})['tag'] in ['PERSON','ORGANIZATION']:
            entities.append((len(e_b['name']),e_b['name'],e_id))
    all_names = [x[1] for x in entities]

    entities.sort()
    print len(entities)
    for (_,n1,_id) in entities:
        ranking = []
        for n2 in all_names:
            if n1 != n2:
                ranking.append((ngram.NGram.compare(n1,n2,N=4),n2))
        ranking.sort(reverse=True)
        if ranking[0][0]>0.2:
            print n1, ranking[0:10]
            x = raw_input('Remove?')
            if x != 'y':
                print 'Keeping'
                new_relevant_entities.append(_id)
            else:
                all_names.remove(n1)
            if x == 'break':
                break
        else:
            new_relevant_entities.append(_id)


    db.bills.update({'id':bill_id},{'$set':{'relevant_entities':new_relevant_entities}}) 

    
def compute_relevant_entities_for_bill(db,bill_id):
    seed_ids = [p['entity_id'] for p in db.politicians_bills.find({'bill':bill_id})]
    relevant_entities = find_relevant_entities(db,bill_id,seed_ids)
    for re in relevant_entities:
        if re is None:
            print 'AHA'

    for seed in seed_ids:
        if db.entities.find_one({'entity':seed}) is None:
            continue
        if seed not in relevant_entities:
            print 'WARNING, POLITICIAN NOT RELEVANT'
            relevant_entities.append(seed)
    #print [db.entities.find_one({'_id':e_id})['name'] for e_id in find_relevant_entities(db,bill_id,seed_ids)]
    db.bills.update({'id':bill_id},{'$set':{'relevant_entities':relevant_entities}})
    '''
    entity_weight = []
    for eb in db.entities_bills.find({'bill':bill_id}):
        entity = db.entities.find_one({'_id':eb['entity']})
        if entity is not None:
            entity_weight.append((eb['adjusted_weight'],eb['entity']))

    entity_weight.sort(reverse=True,key=get_key)
    num_entities = 200# find_cutting_point([ew[0] for ew in entity_weight],bill_id)
    entities = [ew[1] for ew in entity_weight[0:num_entities]]

    bill = db.bills.find_one({'id':bill_id})
    existing_entities = []
    if 'relevant_entities' in bill:
        existing_entities =bill['relevant_entities']
    else:
        existing_entities = []

    existing_entities = []
    for entity in entities:
        if entity not in existing_entities:
            existing_entities.append(entity)

    for politician in db.politicians_bills.find({'bill':bill_id}):
        if politician not in existing_entities:
            pass
            #existing_entities.append(politician)
    #print len(existing_entities)

    db.bills.update({'id':bill_id},{'$set':{'relevant_entities':existing_entities}})
    '''
def postprocess_entities():
    print 'Start'
    conn = MongoClient()
    db = conn.catalan_bills
    index = 'catnews_spanish'
    print 'Setting main tag'
    #set_main_tag(db.entities)
    print 'Normalizing locations'
    #normalize_locations(db.entities)
    print 'Computing IDF'
    bill_ids =[bill['id'] for bill in db.bills.find()]
    #bill_id = '00062014'
    #compute_entity_idf_and_adjusted_weight(db)
    #get_entities_documents(bill_id,index,db)
    #compute_relevant_entities_for_bill(db,bill_id)
    print 'Getting keywords'

    #get_entities_keywords(db,bill_id, 'catnews_spanish_paragraphs','catnews_spanish',filter_by_bill=True)
    #fix_tags(db,bill_id)

    eliminate_duplicated_entities(db,bill_id)

    #remove_entities_with_low_frequency(db)
    #get_entity_documents(db.entities.find_one(),index)

    
postprocess_entities()
