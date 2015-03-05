from elasticsearch import Elasticsearch
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer


def get_idf(word):
    es = Elasticsearch()

    q = {'query': {'bool': {'disable_coord': True, 'must': [{'match_phrase': {'body': {'analyzer': 'analyzer_keywords', 'query': word}}}]}}}

    count = es.count(index='texnews_english',body =q)['count']

    return log(1+count)

def get_keywords(documents, min_freq=3.0, min_ngrams = 1, max_ngrams = 3):

    tfidf_v = CountVectorizer(ngram_range=(min_ngrams,max_ngrams),stop_words = english, tokenizer = tokenizer_with_stemming, min_df = min_freq/len(documents))

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

            if features[j] in keywords:
                keywords[features[j]]+=1
            else:
                keywords[features[j]]=1
                 
    sorted_keywords = [(y,x) for (x,y) in keywords.items()]
    sorted_keywords.sort(reverse= True)

    return sorted_keywords

example = ['Diego is in favor of drug legalization', 'Diego said: "Medical Marihuana is a right', 'We believe that drug legalization could lead to the use of medical marihuana']

print get_keywords(example)[0:10]
