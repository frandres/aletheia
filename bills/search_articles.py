
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

from nltk.stem import SnowballStemmer

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

    return log(1+count)


def apply_rocchio(documents,keywords,alpha=1,beta=0.5):
    #eywords = zip(keywords,[1.0/len(keywords) for i in range(len(keywords))])
    # This dict will store the new keywords.
    new_keywords = {}

    # Normalize q

    q_norm = sqrt(sum([y**2 for (x,y) in keywords]))

    for (kw,weight) in keywords:
        new_keywords[kw] = alpha* weight/q_norm

    # Now analyze the documents

    tfidf_v = CountVectorizer(ngram_range=(1,3),stop_words = stopwords, tokenizer = tokenizer_with_stemming)

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
                #print documents[i]
                #print features[j]
                #print freq

                idf = get_idf(features[j])
                tf_idf_w = idf*freq
                doc_norm+= tf_idf_w**2
                if tf_idf_w >0:
                    doc[features[j]] = tf_idf_w
                #print 'done'
                
        doc_norm = sqrt(doc_norm)
        for (keyword,weight) in doc.items():
            if keyword in new_keywords:
                new_keywords[keyword]+= beta*weight/(doc_norm*len(documents))
            else:
                new_keywords[keyword]= beta*weight/(doc_norm*len(documents))

    print len(keywords)
    print len(new_keywords)
    return [(y,x) for (x,y) in new_keywords.items()]

def rank_entities(article_bodies):
    i = 0
    for x in article_bodies:
        print i
        i+=1
        for (_,lista) in get_entities(x,'es').items():
            for entity in lista:
                if entity in all_entities_freq:
                    all_entities_freq[entity]+=1
                else:
                    all_entities_freq[entity]=1

    print all_entities_freq
    print ' ' 
    ranking = sorted(all_entities_freq.items(),key=lambda x: x[1],reverse= True)
    print ranking[0:20]

def distance(x,y):
    return sqrt(x*x+y*y)

def best_point(x,y):
    last_point_x = x[len(x)-1]

    last_point_y = -1+y[len(y)-1]
    norm = distance(last_point_x,last_point_y)

    last_point_x = last_point_x / norm
    last_point_y = last_point_y / norm

    dist = []
    for i in range(len(x)):
        x_i = x[i]
        y_i = -1+y[i]

        dot_product = x_i* last_point_x + y_i* last_point_y


        x_cord = x_i - dot_product*last_point_x
        y_cord = y_i - dot_product*last_point_y

        dist.append(distance(x_cord,y_cord))
    
    return dist.index(max(dist))
    
conn = MongoClient()
db = conn.catalan_bills

for bill in db.bills.find()[0:40]:
    keywords = bill['keywords']
    es = Elasticsearch(timeout=30)
    query = {"query":{"bool":{"disable_coord": True,"should": [{'match_phrase':{'body':{'query':x,'boost':y,'analyzer':'analyzer_keywords'}}} for [x,y] in keywords]}}}


    #query = {"query":{"bool":{"disable_coord": True,"should": {'match':{'body':{'query':bill['text'],'analyzer':'analyzer_shingle'}}}}}}
#        query = {"query":{"match":{"disable_coord": True,{'body':{'match':{'body':bill[body],'analyzer':'analyzer_shingle'}}}}}}

    score = []

    results = es.search(index="catnews_spanish", body=query,size =10,timeout=30)['hits']['hits']
    documents = [x['_source']['body'] for x in results[0:10]]

    rocchio_kws = apply_rocchio(documents,keywords,alpha=1,beta=0.5)


    rocchio_kws.sort(reverse= True)
   
    print bill['title']
    for (x,y) in rocchio_kws[0:100]:
        if y not in [a for [a,b] in keywords]:
            print x,y

    query = {"query":{"bool":{"disable_coord": True,"should": [{'match_phrase':{'body':{'query':kw,'boost':weight,'analyzer':'analyzer_keywords'}}} for (weight,kw) in rocchio_kws[0:3]]}}}
    results = es.search(index="catnews_spanish", body=query,size =3000,timeout=30)['hits']['hits']
    scores = []

    for x in results:
        scores.append(x['_score'])
        

    plt.plot(range(len(results)),scores)
    #i = best_point(range(len(results)),scores)

    #plt.plot(range(len(results))[i], scores[i], 'rD')

    plt.savefig('plots/'+bill['id']+'-score3.png')
    plt.clf()

    '''
    print len(results)
    print results[0]['_score']
    print ''
    print results[0]['_explanation']['description']
    print ''
    print ''
    print ''
    for x in results[0]['_explanation']['details']:
        print x['description']
        print x['value'] 
        for x in x['details'][0]['details']:
            print x
            print ''
        print '-----------'
        print ''

    for x in results[0]['_explanation']['details'][0]['details'][0]['details']:
        print x
        print ''


    with open('plots/'+bill['id']+'_full.txt', 'w') as f:
        f.write(bill['title'].encode('utf-8')+'\n')
        f.write('|'.join(keywords).encode('utf-8')+'\n')
        for x in results[0:100]:
            text = x['_source']['body']
            f.write(text.encode('utf-8')+'\n-------------------------------------------------\n\n')


    for x in results:
        text = x['_source']['body'].lower()
        occurring_keywords = []
        for kw in keywords:
            if kw in text:
                occurring_keywords.append(kw)
        score.append(len(occurring_keywords))
                
    plt.plot(range(len(score)),score,'ro')

    plt.savefig('plots/'+bill['id']+'-nwords.png')
    plt.clf()

    scores = []
    derivatives = []
    for x in results:
        scores.append(x['_score'])
        

    plt.plot(range(len(results)),scores)
    i = best_point(range(len(results)),scores)

    plt.plot(range(len(results))[i], scores[i], 'rD')

    plt.savefig('plots/'+bill['id']+'-score.png')
    plt.clf()
with open('plots/'+bill['id']+'.txt', 'w') as f:
    f.write(bill['title'].encode('utf-8')+'\n')
    f.write('|'.join(keywords)+'\n')
    for x in range(i-10,i+10):
        f.write('\n')
        f.write('------------------------------------------------------------------------------------\n')
        f.write(results[x]['_source']['body'].encode('utf-8'))
'''    
'''

all_entities_freq={}

article_bodies = [x['_source']['body'] for x in results['hits']['hits']]



rank_entities(article_bodies)
'''
