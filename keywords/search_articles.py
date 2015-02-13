
from keywords import extract_keywords
from get_entities import get_entities
from elasticsearch import Elasticsearch



doc2keywords = extract_keywords('./spanish/')
es = Elasticsearch()

keyword_test = '|'.join(doc2keywords.values()[0][0:10])

print keyword_test

results = es.search(index='catnews_spanish',q=keyword_test,size =1,explain=True)

all_entities_freq={}

print len(results['hits']['hits'])

def get_entities(article_bodies):
    for x in article_bodies:
        for (_,lista) in get_entities(x['_source']['body'],'es').items():
            for entity in lista:
                if entity in all_entities_freq:
                    all_entities_freq[entity]+=1
                else:
                    all_entities_freq[entity]=1

    print all_entities_freq
    print ' ' 
    ranking = sorted(all_entities_freq.items(),key=lambda x: x[1],reverse= True)
    print ranking[0:20]
        
