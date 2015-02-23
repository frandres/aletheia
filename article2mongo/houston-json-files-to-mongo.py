from langdetect import detect, detect_langs
import sys, os
import json
import datetime

from pymongo import MongoClient
conn = MongoClient() 
db = conn.newsdb 

houston_path = "/Users/dolano/htdocs/dama-larca/data/"
houston_dirs = ["sh1", "sh2","sh3","sh4","sh5"]
c = 0
es_cnt = 0
en_cnt = 0
for coma in houston_dirs:
    print coma+" - "
    cur = 0
    for root, subFolders, files in os.walk(os.path.join(houston_path,coma)):    
        if subFolders == []:          
            if len(os.listdir(root)) > 0: 
                    c = c + 1;
                    if c > 0:
                        for filename in os.listdir(root):
                            #print "\n***\t"+filename
                            jsdata = open(os.path.join(root,filename),"r")
                            jso = json.load(jsdata)
                            
                            
                            #do language detection
                            if jso["text"] == "" or len(jso["text"]) < 2:
                                print "\tERROR: No text in "+filename  
                                try:
                                    jso["language"] = detect(jso["title"])
                                except:# LangDetectException:
                                    jso["language"] = "en"
                            else:
                                try:
                                    jso["language"] = detect(jso["text"]) 
                                except:# LangDetectException:
                                    try:
                                        jso["language"] = detect(jso["title"])
                                    except:
                                        jso["language"] = "en"
                                
                            #print jso
                            
                            if jso["language"] == "es":
                                db.texnews.spanish.insert(jso)
                                es_cnt = es_cnt + 1
                            else:                                
                                db.texnews.english.insert(jso)
                                en_cnt = en_cnt + 1
                            cur = cur + 1
    print str(cur)


#get rid of duplicates ..
#NOTE: you need to do this for texnews.english and texnews.spanish 
res3 = db.texnews.spanish.aggregate([{ "$group": { "_id": { "article-num": "$article-num" }, 
                                       "count": { "$sum": 1 }, "docs": { "$push": "$_id" }}},
                                    { "$match": { "count": { "$gt" : 1 }}}],allowDiskUse=True)



len(res3["result"])


for resa in res3['result']:
    print resa["_id"]["article-num"] + ": "+ str(resa["count"])
    c = 0
    print resa
    for d in resa["docs"]:
        if c > 0: 
            print "\t mark as duplicate:"+str(d)
            if c == 1:
                print "\t\t !!! remove from mongod"
                db.texnews.spanish.remove({'_id': d})
        c = c + 1


#> db.texnews.english.count();   731273
#> db.texnews.spanish.count();     15514



#PUT MONGO INTO ELASTIC SEARCH ( first create indexes via elasticsearch/ python files)

from elasticsearch import Elasticsearch
es = Elasticsearch()

from pymongo import MongoClient
conn = MongoClient() 
db = conn.newsdb 

i = 0
for c in db.texnews.english.find():
    i+=1
    c.pop(u'_id')
    es.index(index="texnews_english", doc_type='news_article', id=i, body=c)


i = 0
for c in db.texnews.spanish.find():
    i+=1
    c.pop(u'_id')
    es.index(index="texnews_spanish", doc_type='news_article', id=i, body=c)

