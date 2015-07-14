import os
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
import unicodedata
from docx import Document
import numpy
import re

from nltk.corpus import stopwords
stopwords = stopwords.words('spanish')


from nltk.stem import SnowballStemmer


def strip_accents(s):
    if type(s) is not unicode:
        s = s.decode('utf-8')
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def tokenizer_with_stemming(string):
    token_pattern=r"(?u)\b\w\w+\b"
    pattern = re.compile(token_pattern)
    tokens = pattern.findall(string)

    stemmer = SnowballStemmer('spanish')
    
    stemmed_text = [stemmer.stem(i) for i in tokens]
   
    return tokens
     
    #return stemmed_text
 
def proper_keyword(keyword,stopwords):
    words = keyword.split(' ')
    return words[0] not in stopwords and words[len(words)-1] not in stopwords
               
def extract_keywords(folder):
    doc_names = [folder+x for x in os.listdir(folder)]
    docs = []

    for doc_name in doc_names:
        document = Document(doc_name)
        docText = '\n\n'.join([paragraph.text.encode('utf-8') for paragraph in document.paragraphs])
        docText = strip_accents(docText)
        docs.append(docText)


    tfidf = TfidfVectorizer(ngram_range=(1,3),tokenizer=tokenizer_with_stemming,stop_words = [])
    t = tfidf.fit_transform(docs)

    features = tfidf.get_feature_names()

    i = 0
    doc_to_keywords = {}
    for doc_name in doc_names:
        values = t.todense()[i,:].tolist()[0]
        order = numpy.argsort(values).tolist()
        order.reverse()

        keywords = [features[x] for x in order[0:1000] if proper_keyword(features[x],stopwords)]    
        doc_to_keywords[doc_name] = keywords
        i+=1
    return doc_to_keywords
        
