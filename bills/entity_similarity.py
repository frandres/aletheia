from gensim import corpora, models, similarities
from gensim.models.lsimodel import LsiModel
from pymongo import MongoClient
import math
from collections import defaultdict
import cPickle as pickle
'''
From the entities_documents collection in MongoDB generate 
 + A binary entity/document matrix (corpus) (1 iff the entity occurs in the document) 
   in the gensim corpus notation. [[1:0,2:0]]
 + A col2doc dictionary mapping columns to document id.
 + A row2entity dictionary mapping rows to entity_name. 

These are return as a triplet (corpus,col2doc,row2entity)
'''
def ent_doc2corpus():
    conn = MongoClient()
    ent_col = conn.catalan_bills.entities
    entities = []
    for entity in ent_col.find():
        entities.append(entity)

    corpus = []
    col2doc = {}
    doc2col = {}
    row2entity = {}
    max_id = 0
    row_id = 0

    ent_doc_col = conn.catalan_bills.entities_documents

    for entity in entities:
        row2entity[row_id] = entity['name']
        row_id+=1
        print '{} out of {}'.format(row_id,len(entities))  
        ent_docs = ent_doc_col.find({'entity':entity['_id']})
        ent_vector = []
        docs = []
        for ent_doc in ent_docs:
            article_id = ent_doc['article']
  
            if article_id in doc2col: 
                if article_id not in docs:
                    ent_vector.append((doc2col[article_id],1))
                    docs.append(article_id)
            else:
                docs.append(article_id)
                doc2col[article_id] = max_id
                col2doc[max_id] = article_id
                ent_vector.append((doc2col[article_id],1))
                max_id +=1
        corpus.append(ent_vector)

    return (corpus,col2doc,row2entity)


'''
From the entities_keyword collection in MongoDB generate 
 + An entity/keyword matrix (corpus) with the tf/ikf 
   in the gensim corpus notation. [[1:3,2:2]]
   tf denotes the number of times the keyword and the entity co-occur in a document.
 + A col2keyword dictionary mapping columns to keyword.
 + A row2entity dictionary mapping rows to entity_name. 

These are return as a triplet (corpus,col2keyword,row2entity)
'''
def ent_keyword2corpus():
    conn = MongoClient()
    ent_col = conn.catalan_bills.entities
    entities = []
    for entity in ent_col.find():
        entities.append(entity)

    corpus = []
    col2keyword = {}
    keyword2col = {}
    row2entity = {}
    max_id = 0
    row_id = 0

    ent_kw_col = conn.catalan_bills.entities_keywords

    for entity in entities:
        row2entity[row_id] = entity['name']
        row_id+=1
        print '{}: {} out of {}'.format(entity['name'],row_id,len(entities))  
        ent_kws = ent_kw_col.find({'entity':entity['_id']})
        kws = defaultdict(lambda: 0)

        for ent_kw in ent_kws:
            print ent_kw
            keyword = ent_kw['keyword']
	      
    	    if keyword not in keyword2col: 
                keyword2col[keyword] = max_id
                col2keyword[max_id] = keyword
                max_id +=1

            kws[keyword2col[keyword]]+= 1 * ent_kw['idf']

        corpus.append(kws.items())

    return (corpus,col2keyword,row2entity)

'''
From the entities_bill collection in MongoDB generate 
 + An entity/topic matrix (corpus) with the sum(log(document)*log(freq) measure)
   in the gensim corpus notation. [[1:3,2:2]]
 + A col2bill dictionary mapping columns to bill id.
 + A row2entity dictionary mapping rows to entity_name. 

These are return as a triplet (corpus,col2keyword,row2entity)
'''
def ent_bill2corpus():
    conn = MongoClient()
    ent_col = conn.catalan_bills.entities
    entities = []
    for entity in ent_col.find():
        entities.append(entity)

    corpus = []
    col2bill = {}
    bill2col = {}
    row2entity = {}
    max_id = 0
    row_id = 0

    ent_bills_col = conn.catalan_bills.entities_bills

    for entity in entities:
        row2entity[row_id] = entity['name']
        row_id+=1
        print '{}: {} out of {}'.format(entity['name'],row_id,len(entities))  
        ent_bills = ent_bills_col.find({'entity':entity['_id']})
        ent_topics_vector = defaultdict(lambda: 0)

        for ent_bill in ent_bills:
            bill = ent_bill['bill']
            if bill not in bill2col:
                bill2col[bill] = max_id
                col2bill[max_id] = bill
                max_id+=1

            print ent_bill['weight']['articles']
            for article_occurrence in ent_bill['weight']['articles']:
                ent_topics_vector[bill2col[bill]]+= math.log(1+article_occurrence['article_weight']) * math.log(1+article_occurrence['frequency'])
            
        corpus.append(ent_topics_vector.items())

    return (corpus,col2bill,row2entity)


def get_test_corpus():
    return [[(0, 1.0), (1, 1.0), (2, 1.0)],
            [(2, 1.0), (3, 1.0), (4, 1.0), (5, 1.0), (6, 1.0), (8, 1.0)],
            [(1, 1.0), (3, 1.0), (4, 1.0), (7, 1.0)],
            [(0, 1.0), (4, 2.0), (7, 1.0)],
            [(3, 1.0), (5, 1.0), (6, 1.0)],
            [(9, 1.0)],
            [(9, 1.0), (10, 1.0)],
            [(9, 1.0), (10, 1.0), (11, 1.0)],
            [(8, 1.0), (10, 1.0), (11, 1.0)]]


pickle.dump(ent_bill2corpus(),open('ent_bill_corpus.pkl', 'wb'),-1)
pickle.dump(ent_keyword2corpus(),open('ent_bill_keywords.pkl', 'wb'),-1)
pickle.dump(ent_doc2corpus(),open('ent_bill_documents.pkl', 'wb'),-1)
'''
id2word = {0:'a',1:'b',2:'c',3:'de',4:'a',5:'b',6:'c',7:'a',8:'b',9:'c',10:'a',11:'b'}
lsi = LsiModel(corpus=corpus,id2word=id2word, num_topics=2)
print lsi.print_topics(2)
'''
