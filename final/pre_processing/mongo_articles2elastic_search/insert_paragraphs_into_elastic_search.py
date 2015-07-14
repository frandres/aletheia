
from pymongo import MongoClient
from elasticsearch import Elasticsearch
from nltk.tokenize import sent_tokenize
from elasticsearch import helpers
es = Elasticsearch(timeout=50000)

i = 0
d_count = 0
for d in helpers.scan(es,index ='catnews_spanish'):
    print d_count
    d_count+=1
    for paragraph in d['_source']['body'].split('\n'):
        i+=1
        doc = {}
        doc['body']=paragraph
        doc['article_id']=d['_id']
        es.index(index="catnews_spanish_paragraphs", doc_type='news_article_paragraph', id=i, body=doc)
