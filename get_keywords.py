from elasticsearch import Elasticsearch
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from math import log
from data import data

def get_idf(word):
    es = Elasticsearch()
    q = {'query': {'bool': {'disable_coord': True, 'must': [{'match_phrase': {'body': {'analyzer': 'analyzer_keywords', 'query': word}}}]}}}
    count = es.count(index='texnews_english',body =q)['count']
    N = es.count(index='texnews_english')['count']
    #print "count: "+str(N)
    #print word,count
    return log(float(N)/(1+count))

def get_keywords(documents, min_freq=3.0, min_ngrams = 1, max_ngrams = 3):   
    
    minf = float(min_freq)/len(documents)
    tfidf_v = CountVectorizer(ngram_range=(min_ngrams,max_ngrams),stop_words = "english", min_df = minf)
    t = tfidf_v.fit_transform(documents)
    
    features = tfidf_v.get_feature_names()
    matrix = t.todense()
    keywords = {}
    
    for i in range(len(documents)):
        # Compute the norm and the weight of each feature.
        for j in range(len(features)):
            freq = matrix[i,j]

            idf = get_idf(features[j])
            tf_idf_w = idf*freq
            
            #print features[j], idf
            if features[j] in keywords:
                keywords[features[j]]+=tf_idf_w
            else:
                keywords[features[j]]=tf_idf_w
                 
    sorted_keywords = [(y,x) for (x,y) in keywords.items()]
    sorted_keywords.sort(reverse= True)

    return sorted_keywords

print get_keywords(data.values())
