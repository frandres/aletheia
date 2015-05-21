import sys
from nltk.tokenize import sent_tokenize
from elasticsearch import Elasticsearch

#from search_articles import stopwords
from collections import defaultdict
from string import punctuation

stopwords = ["de","la","que","el","en","y","a","los","del","se","las","por","un","par","con","no","una","su","al","lo","com","mas","per","sus","le","ya","o","este","si","porqu","esta","entre","cuand","muy","sin","sobr","tambi","me","hast","hay","dond","qui","desd","tod","nos","durant","tod","uno","les","ni","contr","otros","ese","eso","ante","ellos","e","esto","mi","antes","algun","que","unos","yo","otro","otras","otra","el","tant","esa","estos","much","quien","nad","much","cual","poc","ella","estar","estas","algun","algo","nosotr","mi","mis","tu","te","ti","tu","tus","ellas","nosotr","vosostr","vosostr","os","mio","mia","mios","mias","tuy","tuy","tuy","tuy","suy","suy","suy","suy","nuestr","nuestr","nuestr","nuestr","vuestr","vuestr","vuestr","vuestr","esos","esas","estoy","estas","esta","estam","estais","estan","este","estes","estem","esteis","esten","estar","estar","estar","estar","estareis","estar","estari","estari","estari","estariais","estari","estab","estab","estab","estabais","estab","estuv","estuv","estuv","estuv","estuv","estuv","estuv","estuv","estuvier","estuv","estuv","estuv","estuv","estuvies","estuv","estuv","estand","estad","estad","estad","estad","estad","he","has","ha","hem","habeis","han","hay","hay","hay","hayais","hay","habr","habr","habr","habr","habreis","habr","habri","habri","habri","habriais","habri","habi","habi","habi","habiais","habi","hub","hub","hub","hub","hub","hub","hub","hub","hubier","hub","hub","hub","hub","hubies","hub","hub","hab","hab","hab","hab","hab","soy","eres","es","som","sois","son","sea","seas","seam","seais","sean","ser","ser","ser","ser","sereis","ser","seri","seri","seri","seriais","seri","era","eras","eram","erais","eran","fui","fuist","fue","fuim","fuisteis","fueron","fuer","fuer","fuer","fuerais","fuer","fues","fues","fues","fueseis","fues","sint","sent","sent","sent","sent","sient","sent","teng","tien","tien","ten","teneis","tien","teng","teng","teng","tengais","teng","tendr","tendr","tendr","tendr","tendreis","tendr","tendri","tendri","tendri","tendriais","tendri","teni","teni","teni","teniais","teni","tuv","tuv","tuv","tuv","tuv","tuv","tuv","tuv","tuvier","tuv","tuv","tuv","tuv","tuvies","tuv","tuv","ten","ten","ten","ten","ten","ten"]



sys.setrecursionlimit(2000)

from nltk.stem import SnowballStemmer
from math import log
def sentence2ngrams(sentence, max_size = 3):
    for sign in punctuation:
        sentence = sentence.replace(sign,'')
    stemmer = SnowballStemmer('spanish')
    words = [stemmer.stem(word.decode('utf8')) for word in sentence.split()]
    words = [word for word in words if word not in stopwords]
    ngrams = [word for word in words]
    for i in range(1,max_size):
        for j in range(0,len(words)-i):
            ngrams.append(' '.join(words[j:j+i+1]))
    return ngrams
    
def get_entity_keywords(name,index,min_freq=2):

    
    q = {'query': {'bool': {'disable_coord': True, 'must': [{'match_phrase': {'body': {'analyzer': 'analyzer_shingle', 'query': name}}}]}}}
    es = Elasticsearch()
    N = es.count(index = 'catnews_spanish')['count']

    results = es.search(index=index, body=q, explain = True, size = 3000,search_type = 'dfs_query_then_fetch')['hits']['hits']
    n_grams = {}

    for result in results:
        article = result['_source']['body']
        sentences = sent_tokenize(article)
        for sentence in sentences:
            sentence = sentence.encode('utf8')
            if name in sentence:
                for n_gram in sentence2ngrams(sentence):
                    if n_gram in n_grams:
                        n_grams[n_gram]['freq']+=1
                    else:
                        n_grams[n_gram] = {}

                        n_grams[n_gram]['freq'] = 1

    filtered_n_grams = {}
    for (n_gram,value) in n_grams.items():
        if value['freq'] >= min_freq:
            q = {'query': {'bool': {'must': [{'match_phrase': {'body': {'analyzer': 'analyzer_keywords2', 'query': n_gram}}}]}}}
            results = es.search(index=index, body=q, explain = True,search_type = 'dfs_query_then_fetch')['hits']['hits']
            document_count = es.search(index=index, body=q, explain = True,search_type = 'dfs_query_then_fetch')['hits']['total']
            if document_count >0:
                value['idf'] = log(N/document_count) 
                filtered_n_grams[n_gram] = value

    return filtered_n_grams


for w in get_entity_keywords('Albert Batet','catnews_spanish').items()[0:100]:
    print w
#print get_entity_keywords('Albert Batet','catnews_spanish')
