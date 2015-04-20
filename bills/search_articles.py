from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

from nltk.stem import SnowballStemmer
from entities import get_entities
from collections import defaultdict
from entities_functions import merge_entities
from elasticsearch import Elasticsearch
import matplotlib.pyplot as plt
from pymongo import MongoClient
from math import sqrt,log
import re

stopwords = ["de","la","que","el","en","y","a","los","del","se","las","por","un","par","con","no","una","su","al","lo","com","mas","per","sus","le","ya","o","este","si","porqu","esta","entre","cuand","muy","sin","sobr","tambi","me","hast","hay","dond","qui","desd","tod","nos","durant","tod","uno","les","ni","contr","otros","ese","eso","ante","ellos","e","esto","mi","antes","algun","que","unos","yo","otro","otras","otra","el","tant","esa","estos","much","quien","nad","much","cual","poc","ella","estar","estas","algun","algo","nosotr","mi","mis","tu","te","ti","tu","tus","ellas","nosotr","vosostr","vosostr","os","mio","mia","mios","mias","tuy","tuy","tuy","tuy","suy","suy","suy","suy","nuestr","nuestr","nuestr","nuestr","vuestr","vuestr","vuestr","vuestr","esos","esas","estoy","estas","esta","estam","estais","estan","este","estes","estem","esteis","esten","estar","estar","estar","estar","estareis","estar","estari","estari","estari","estariais","estari","estab","estab","estab","estabais","estab","estuv","estuv","estuv","estuv","estuv","estuv","estuv","estuv","estuvier","estuv","estuv","estuv","estuv","estuvies","estuv","estuv","estand","estad","estad","estad","estad","estad","he","has","ha","hem","habeis","han","hay","hay","hay","hayais","hay","habr","habr","habr","habr","habreis","habr","habri","habri","habri","habriais","habri","habi","habi","habi","habiais","habi","hub","hub","hub","hub","hub","hub","hub","hub","hubier","hub","hub","hub","hub","hubies","hub","hub","hab","hab","hab","hab","hab","soy","eres","es","som","sois","son","sea","seas","seam","seais","sean","ser","ser","ser","ser","sereis","ser","seri","seri","seri","seriais","seri","era","eras","eram","erais","eran","fui","fuist","fue","fuim","fuisteis","fueron","fuer","fuer","fuer","fuerais","fuer","fues","fues","fues","fueseis","fues","sint","sent","sent","sent","sent","sient","sent","teng","tien","tien","ten","teneis","tien","teng","teng","teng","tengais","teng","tendr","tendr","tendr","tendr","tendreis","tendr","tendri","tendri","tendri","tendriais","tendri","teni","teni","teni","teniais","teni","tuv","tuv","tuv","tuv","tuv","tuv","tuv","tuv","tuvier","tuv","tuv","tuv","tuv","tuvies","tuv","tuv","ten","ten","ten","ten","ten","ten"]
def tokenizer_with_stemming(string):
    token_pattern=r"(?u)\b\w\w+\b"
    pattern = re.compile(token_pattern)
    tokens = pattern.findall(string)

    stemmer = SnowballStemmer('spanish')
    stemmed_text = [stemmer.stem(i) for i in tokens]
    return stemmed_text

    #return stemmed_text

def get_idf(word):
    es = Elasticsearch()

    q = {'query': {'bool': {'disable_coord': True, 'must': [{'match_phrase': {'body': {'analyzer': 'analyzer_keywords', 'query': word}}}]}}}

    count = es.count(index='catnews_spanish',body =q)['count']
    N = es.count(index='catnews_spanish')['count']

    return log(float(N)/(1+count))


def apply_rocchio(documents,keywords,alpha=1,beta=0.5,min_freq=3.0):
    #eywords = zip(keywords,[1.0/len(keywords) for i in range(len(keywords))])
    # This dict will store the new keywords.
    new_keywords = {}

    # Normalize q

    q_norm = sqrt(sum([y**2 for (x,y) in keywords]))

    for (kw,weight) in keywords:
        new_keywords[kw] = alpha* weight/q_norm

    # Now analyze the documents

    tfidf_v = CountVectorizer(ngram_range=(1,3),stop_words = stopwords, tokenizer = tokenizer_with_stemming,min_df=float(min_freq)/len(documents))

    t = tfidf_v.fit_transform(documents)
    features = tfidf_v.get_feature_names()

    matrix = t.todense()

    for i in range(len(documents)):
        doc_norm = 0
        doc = {}

        # Compute the norm and the weight of each feature.

        for j in range(len(features)):
            freq = matrix[i,j]
            if freq >2:

                idf = get_idf(features[j])
                tf_idf_w = idf*freq
                doc_norm+= tf_idf_w**2
                if tf_idf_w >0:
                    doc[features[j]] = tf_idf_w
                
        doc_norm = sqrt(doc_norm)
        for (keyword,weight) in doc.items():
            if keyword in new_keywords:
                new_keywords[keyword]+= beta*weight/(doc_norm*len(documents))
            else:
                new_keywords[keyword]= beta*weight/(doc_norm*len(documents))

    return [(y,x) for (x,y) in new_keywords.items()]

'''
Given a list of articles, 
perform Named Entity Recognition and
return a list of dictionaries containing information about the entities found
'''
def article2entities(articles,index):
    i = 0
    entities = {}
    for (body,weight,article_id) in articles[0:10000]:
        i+=1
        print ' Article {} out of {}'.format(i,len(articles))
        for (entity_name,entity_dict) in get_entities(body,index).items():

            # Update the aggregated dict. 

            freq = entity_dict['freq']
            aliases = entity_dict['aliases']

            # If the entity has already been found for this bill, update the existing instance.
            # Otherwise create a new instance.
                        
            if entity_name in entities:
                entities[entity_name]['articles'].append(article_id)
                entities[entity_name]['freq']+=freq
                entities[entity_name]['weight']['articles'].append({'article_weight':weight,'article_ranking':i,'article_id':article_id,'frequency':freq})
                entities[entity_name]['weight']['value']+=weight*1
                
                # Merge tag counts.

                for (tag,count) in entity_dict['tags'].items():
                    if tag in entities[entity_name]['tags']:
                        entities[entity_name]['tags'][tag]+=count
                    else:
                        entities[entity_name]['tags'][tag]=count

                # Merge aliases list.

                for alias in aliases:
                    if alias not in entities[entity_name]['aliases']:
                        entities[entity_name]['aliases'].append(alias)
            else:
                entities[entity_name] = {}
                entities[entity_name]['articles'] = [article_id]
                entities[entity_name]['freq']=freq
                entities[entity_name]['name']=entity_name
                entities[entity_name]['weight']={}
                entities[entity_name]['tags'] = entity_dict['tags']
                entities[entity_name]['weight']['value']=weight*1
                entities[entity_name]['weight']['articles']=[{'article_weight':weight,'article_ranking':i,'article_id':article_id,'frequency':freq}]
                entities[entity_name]['aliases'] = aliases
    return entities.values()

'''
Given a list of dictionaries of entities and a collection, insert/update them in MongoDB and
set a 'mongoid' attribute in the dictionary with the corresponding MongoDB id.
'''
def insert_entities(entities,collection,bill_id):
    i = 0
    for entity in entities:
        i+=1
        
        # Create a Mongo Entity instance based on the entity.

        mongo_entity = {}
        mongo_entity['name'] = entity['name']
        mongo_entity['aliases'] = entity['aliases']
        mongo_entity['bills'] = [bill_id]
        mongo_entity['tags'] = entity['tags']

        res = collection.find({'name':entity['name']})
        # Insert or update.
        if res.count()>0:
            if res.count()>1:
                raise Exception('Non unique entity')

            merge_entities(mongo_entity,{'name':mongo_entity['name']},collection)

        else:
            # Create a new mongo document containing the name and aliases and fetch the id.
            collection.insert(mongo_entity)

        # We need to store the mongo_id in the dictionary for linking the bill to the entity.
        res = collection.find({'name':entity['name']})
        entity['mongoid'] = res[0]['_id']

    return entities

def find_cutting_point(scores, epsilon = 0.001,window_size = 50):
    for i in range(50,len(scores)):
        slope = abs(float(scores[i][0]-scores[i-window_size][0])/(window_size))
        if slope<epsilon:
            plt.plot(range(len(scores)),[score for (score,_) in scores])
            plt.plot(i, scores[i][0], 'ro')
            plt.savefig('./results/article_weight/'+scores[i][1]+'.png')
            plt.clf()
            return i

def relate_entities_bills(entities,collection,bill_id):
    bill_entities = []
    for entity in entities:
        bill_entity = {}
        bill_entity['entity'] = entity['mongoid']
        bill_entity['weight'] = entity['weight']
        bill_entity['freq'] = entity['freq']
        bill_entity['name'] = entity['name']
        bill_entity['bill'] = bill_id
        collection.insert(bill_entity)

def relate_entities_documents(entities,collection,bill_id):
    for entity in entities:
        for article in entity['articles']:
            collection.insert({'entity': entity['mongoid'], 'article': article,'bill_id':bill_id})

def relate_entities_keywords(entities,collection,keywords_documents,bill_id):
    for entity in entities:
        for article in entity['articles']:
            for keyword in keywords_documents[article]:
                entity_keyword = {}
                entity_keyword['entity'] = entity['mongoid']
                entity_keyword['keyword'] = keyword['word']
                entity_keyword['frequency'] = keyword['frequency']
                entity_keyword['idf'] = keyword['idf']
                entity_keyword['bill_id'] = bill_id
                collection.insert(entity_keyword)


def get_rocchio_keywords(original_keywords, num_articles = 10,max_rocchio_num_articles =100):

    query = {"query":{"bool":{"disable_coord": True,"should": [{'match_phrase':{'body':{'query':x,'boost':y,'analyzer':'analyzer_keywords'}}} for [x,y] in original_keywords[0:1024]]}}}
    
    es = Elasticsearch(timeout=30)
    results = es.search(index="catnews_spanish", body=query,size =100,search_type = 'dfs_query_then_fetch',sort='_score:desc,_id:desc')['hits']['hits']

    score = results[num_articles-1]['_score']
    while results[num_articles-1]['_score'] == score and num_articles<max_rocchio_num_articles:
        num_articles+=1

    documents = [x['_source']['body'] for x in results[0:num_articles]]

    rocchio_kws = apply_rocchio(documents,original_keywords,alpha=1,beta=0.5)
    rocchio_kws.sort(reverse=True)
   
    kws = [[x,y] for (y,x) in rocchio_kws]

    return kws

def document2keywords(elasticsearch_results):
    document_keywords = {}
    for hit in elasticsearch_results['hits']['hits']:
        kws = []
        for kw in hit['_explanation']['details']:
            match = re.search('.*body:(.+)\^.*', kw['description'])
            word = match.group(1)
            frequency = kw['details'][0]['details'][1]['details'][0]['details'][0]['value']
            idf = kw['details'][0]['details'][1]['details'][1]['value'] 
            kws.append({'word':word,'frequency':frequency,'idf':idf})
        document_keywords[hit['_id']] = kws

    return document_keywords

     
conn = MongoClient()
db = conn.catalan_bills

bills = []
for bill in db.bills.find():
    bills.append(bill)

for bill in bills:

    original_keywords = bill['keywords']
    #print bill['text'][0:1000].encode('utf8')
    #print bill['keywords']

   
    # Get rocchio's keywords.

    rocchio_kws = get_rocchio_keywords(original_keywords)

    # Store them in Mongo.
    
    db.bills.update({'id':bill['id']},{'$set':{'rocchio_keywords':rocchio_kws}})


    # Execute the new query.

    query = {"query":{"bool":{"disable_coord": True,"should": [{'match_phrase':{'body':{'query':kw,'boost':weight,'analyzer':'analyzer_keywords'}}} for [kw,weight] in rocchio_kws[0:10]]}}}

    print 'Searching'
    es = Elasticsearch(timeout=100)

    results = es.search(index="catnews_spanish", explain = True, body=query,search_type = 'dfs_query_then_fetch',size =3000,sort='_score:desc,_id:desc')

    document_keywords = document2keywords(results)

    articles = [(x['_source']['body'],x['_score'],x['_id']) for x in results['hits']['hits']]

    num_articles = find_cutting_point([(y,_id) for (_,y,_id) in articles])

    print('Bill: {}'.format(bill['id']))

    print(' Found {} relevant articles'.format(num_articles))

    print(' Finding entities')
    entities = article2entities(articles[0:num_articles],'catnews_spanish')
    print(' Found {} entities'.format(len(entities)))
        
    print(' Inserting entities')
    entities = insert_entities(entities,db.entities,bill['id'])

    print(' Relating entities with bills')
    relate_entities_bills(entities,db.entities_bills,bill['id'])

    print(' Relating entities with documents')
    relate_entities_documents(entities,db.entities_documents,bill['id'])

    print(' Relating entities with keywords')
    relate_entities_keywords(entities,db.entities_keywords,document_keywords,bill['id'])
    '''

    print len(ranking)
    plt.plot(range(len(ranking)),[x[1] for x in ranking])
    plt.savefig('./results/'+bill['id']+'_entities_weights.png')
    plt.clf()
    original_keywords = [x for (x,y) in original_keywords]



    with open('./results/'+bill['id']+'_summary.txt', 'w') as f:
        f.write(bill['text'][0:500].encode('utf8')+'\n\n')
        f.write('\n----------------- ROCCHIO FOUND -----------------\n\n')


        i = 0
        for (weight, kw) in rocchio_kws[0:1024]:
            (weight,kw) = rocchio_kws[i]
            if kw not in original_keywords:
                f.write(kw.encode('utf8')+ ' with weight: '+ str(weight) + ' and ranking ' + str(i)+'\n')
            i+=1

        i = 0
        f.write('\n----------------- ENTITIES FOUND -----------------\n\n')
        for (entity,weight) in ranking:
            f.write(entity+ ' with weight: '+ str(weight) + ' and ranking ' + str(i)+'\n')
            i+=1
    '''
