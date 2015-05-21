import os
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
import unicodedata
import numpy
import re
import matplotlib.pyplot as plt

from bs4 import BeautifulSoup

from pymongo import MongoClient

from math import sqrt

stopwords = ["de","la","que","el","en","y","a","los","del","se","las","por","un","par","con","no","una","su","al","lo","com","mas","per","sus","le","ya","o","este","si","porqu","esta","entre","cuand","muy","sin","sobr","tambi","me","hast","hay","dond","qui","desd","tod","nos","durant","tod","uno","les","ni","contr","otros","ese","eso","ante","ellos","e","esto","mi","antes","algun","que","unos","yo","otro","otras","otra","el","tant","esa","estos","much","quien","nad","much","cual","poc","ella","estar","estas","algun","algo","nosotr","mi","mis","tu","te","ti","tu","tus","ellas","nosotr","vosostr","vosostr","os","mio","mia","mios","mias","tuy","tuy","tuy","tuy","suy","suy","suy","suy","nuestr","nuestr","nuestr","nuestr","vuestr","vuestr","vuestr","vuestr","esos","esas","estoy","estas","esta","estam","estais","estan","este","estes","estem","esteis","esten","estar","estar","estar","estar","estareis","estar","estari","estari","estari","estariais","estari","estab","estab","estab","estabais","estab","estuv","estuv","estuv","estuv","estuv","estuv","estuv","estuv","estuvier","estuv","estuv","estuv","estuv","estuvies","estuv","estuv","estand","estad","estad","estad","estad","estad","he","has","ha","hem","habeis","han","hay","hay","hay","hayais","hay","habr","habr","habr","habr","habreis","habr","habri","habri","habri","habriais","habri","habi","habi","habi","habiais","habi","hub","hub","hub","hub","hub","hub","hub","hub","hubier","hub","hub","hub","hub","hubies","hub","hub","hab","hab","hab","hab","hab","soy","eres","es","som","sois","son","sea","seas","seam","seais","sean","ser","ser","ser","ser","sereis","ser","seri","seri","seri","seriais","seri","era","eras","eram","erais","eran","fui","fuist","fue","fuim","fuisteis","fueron","fuer","fuer","fuer","fuerais","fuer","fues","fues","fues","fueseis","fues","sint","sent","sent","sent","sent","sient","sent","teng","tien","tien","ten","teneis","tien","teng","teng","teng","tengais","teng","tendr","tendr","tendr","tendr","tendreis","tendr","tendri","tendri","tendri","tendriais","tendri","teni","teni","teni","teniais","teni","tuv","tuv","tuv","tuv","tuv","tuv","tuv","tuv","tuvier","tuv","tuv","tuv","tuv","tuvies","tuv","tuv","ten","ten","ten","ten","ten","ten"]

from nltk.stem import SnowballStemmer
import chardet

def strip_accents(s):
#    encoding = chardet.detect(s)['encoding']
    s = s.decode('utf-8','ignore')

    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def tokenizer_with_stemming(string):
    token_pattern=r"(?u)\b\w\w+\b"
    pattern = re.compile(token_pattern)
    tokens = pattern.findall(string)

    stemmer = SnowballStemmer('spanish')
    
    stemmed_text = [stemmer.stem(i) for i in tokens]
    return stemmed_text
     
    #return stemmed_text
 
digits = map(str,range(10))
def proper_keyword(keyword):
    words = keyword.split(' ')

    # There is at least one word
    if len([x for x in words if x[0] not in digits]) ==0:
        return False
    return True

def get_title(doc):
    regexp = re.compile(r"(^\s*(?:<<)*.{0,1}(?:Ley|LEY).*?$)",re.MULTILINE)
    if len(regexp.findall(doc))==0:
        return ''
    line = regexp.findall(doc)[0].strip()
    return line

def get_year(doc):
    title = get_title(doc)
    if title == '':
        return ''
    regexp = re.compile(r".*?\d*/\s*(\d{4}).*")
    year = regexp.findall(doc)[0]
    return year


def get_date(doc):
    regexp = re.compile(r"(^(?:Sessio|Sesi).*?$)", re.MULTILINE)
    if len(regexp.findall(doc))==0:
        #print '---------------'
        #print doc[0:1000]
        return ''

    line = regexp.findall(doc)[0]
    regexp = re.compile(r".*?(\d*\.\d*\.\d*).*", re.MULTILINE)
    return regexp.findall(line)[0]

def process_docs(folder,db):
    doc_names = os.listdir(folder)
    docs = {}

    all_docs = []

    for doc_name in doc_names:
        with open(folder+doc_name, 'r') as f:
            docText = f.read()
        docs[doc_name] = {}

        #document = Document(doc_name)
        #docText = '\n\n'.join([paragraph.text.encode('utf-8') for paragraph in document.paragraphs])
        docText = strip_accents(docText)
        t = doc_name.split('.')
        docs[doc_name]['id'] = t[0]
        docs[doc_name]['title'] = get_title(docText[0:1000])
        docs[doc_name]['year'] = get_year(docText[0:1000])
        docs[doc_name]['text'] = docText
        all_docs.append(docText)

    print 'Building model'
    tfidf = TfidfVectorizer(ngram_range=(1,3),stop_words = stopwords, tokenizer = tokenizer_with_stemming, norm = False)
    print 'Transforming'
    t = tfidf.fit_transform(all_docs)
    print 'Getting features'
    features = tfidf.get_feature_names()

    i = 0
    doc_to_keywords = {}
    for doc_name in doc_names:
        print i
        if db.bills.find({'id':docs[doc_name]['id']}).count() >0:
            print 'Done'
            i+=1
            continue

        if docs[doc_name]['year'] == '' or int(docs[doc_name]['year'])<2004:
            print 'Skipping because of the year'
            i+=1
            continue

        print 'Analyzing: {}'.format(docs[doc_name]['year'])


        values = t.todense()[i,:].tolist()[0]
        all_tokens = zip(values,range(len(values)))
        l = [(x,y) for (x,y) in all_tokens if x>0]
        print len(l)

        selected = [(x,y) for (x,y) in l if x/tfidf.idf_[y]>2 and proper_keyword(features[y])]
        print 'done'

        norm = sqrt(sum([x**2 for (x,y) in selected]))
        selected = [(x/norm,y) for (x,y) in selected]
        print sqrt(sum([x**2 for (x,y) in selected]))

        selected.sort(reverse=True)

        print len(selected)
        keywords = [(features[y],x) for (x,y) in selected]
        print keywords[0:100]
        tfidfs = [x for(x,y) in selected]
        plt.plot(range(len(tfidfs)),tfidfs)
        plt.savefig('tfidf/'+doc_name+'.png')
        plt.clf()
         
        docs[doc_name]['keywords'] = keywords

        db.bills.insert(docs[doc_name])

        i+=1

def main():

    conn = MongoClient()
    db = conn.catalan_bills
    docs = process_docs('./spanish/txt/',db)
    '''
    for (key, value) in docs.items():
        db.bill.insert(value)
    '''
main()
