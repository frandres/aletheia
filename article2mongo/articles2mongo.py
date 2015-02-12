rootdir_comarcas = "/Users/dolano/htdocs/dama-larca/catalan2/vanguardia/articulos_por_secciones/comarcas/"
rootdir_global = "/Users/dolano/htdocs/dama-larca/catalan2/vanguardia/articulos_por_secciones/global/"
rootdir_regiones = "/Users/dolano/htdocs/dama-larca/catalan2/vanguardia/articulos_por_secciones/regiones/"

import sys, os
import pprint
import json
import datetime

from pymongo import MongoClient
conn = MongoClient() 
db = conn.newsdb   #db is called "newsdb"

import unicodedata
from nltk.corpus import stopwords
spanish = stopwords.words('spanish')

catalan = [u'a', u'abans', u'aci', u'ah', u'aixi', u'aixo', u'al', u'als', u'aleshores', u'algun', u'alguna', u'algunes', u'alguns', u'alhora', u'alla', u'alli', u'allo', u'altra', u'altre', u'altres', u'amb', u'ambdos', u'ambdues', u'apa', u'aquell', u'aquella', u'aquelles', u'aquells', u'aquest', u'aquesta', u'aquestes', u'aquests', u'aqui', u'baix', u'cada', u'cadascu', u'cadascuna', u'cadascunes', u'cadascuns', u'com', u'contra', u"d'un", u"d'una", u"d'unes", u"d'uns", u'dalt', u'de', u'del', u'dels', u'des', u'despres', u'dins', u'dintre', u'donat', u'doncs', u'durant', u'e', u'eh', u'el', u'els', u'em', u'en', u'encara', u'ens', u'entre', u'erem', u'eren', u'ereu', u'es', u'es', u'esta', u'esta', u'estavem', u'estaven', u'estaveu', u'esteu', u'et', u'etc', u'ets', u'fins', u'fora', u'gairebe', u'ha', u'han', u'has', u'havia', u'he', u'hem', u'heu', u'hi', u'ho', u'i', u'igual', u'iguals', u'ja', u"l'hi", u'la', u'les', u'li', u"li'n", u'llavors', u"m'he", u'ma', u'mal', u'malgrat', u'mateix', u'mateixa', u'mateixes', u'mateixos', u'me', u'mentre', u'mes', u'meu', u'meus', u'meva', u'meves', u'molt', u'molta', u'moltes', u'molts', u'mon', u'mons', u"n'he", u"n'hi", u'ne', u'ni', u'no', u'nogensmenys', u'nomes', u'nosaltres', u'nostra', u'nostre', u'nostres', u'o', u'oh', u'oi', u'on', u'pas', u'pel', u'pels', u'per', u'pero', u'perque', u'poc', u'poca', u'pocs', u'poques', u'potser', u'propi', u'qual', u'quals', u'quan', u'quant', u'que', u'que', u'quelcom', u'qui', u'quin', u'quina', u'quines', u'quins', u"s'ha", u"s'han", u'sa', u'semblant', u'semblants', u'ses', u'seu', u'seus', u'seva', u'seva', u'seves', u'si', u'sobre', u'sobretot', u'soc', u'solament', u'sols', u'son', u'son', u'sons', u'sota', u'sou', u"t'ha", u"t'han", u"t'he", u'ta', u'tal', u'tambe', u'tampoc', u'tan', u'tant', u'tanta', u'tantes', u'teu', u'teus', u'teva', u'teves', u'ton', u'tons', u'tot', u'tota', u'totes', u'tots', u'un', u'una', u'unes', u'uns', u'us', u'va', u'vaig', u'vam', u'van', u'vas', u'veu', u'vosaltres', u'vostra', u'vostre', u'vostres']

def det_language(text):
    spanish_counter = 0
    catalan_counter = 0
    for word in text.split(' '):
        if word in spanish:
            spanish_counter+=1
        if word in catalan:
            catalan_counter+=1

    return 'spanish' if spanish_counter>catalan_counter else 'catalan'


def validate(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


###################HANDLE COMARCAS#################

comarcas = ['anoia', 'bagues', 'baix-llobregat', 'barcelones-nord', 'bergueda', 'maresme', 'osona', 'pirineos', 'reus', 'sabadell', 'solsones', 'terrassa', 'terres-de-l-ebre', 'valle-oriental', 'vilafranca', 'vilanova']

#article result counts
res = {'anoia':1430,'bagues':2697,'baix-llobregat':4412,'barcelones-nord':8907,'bergueda':477, 'maresme':3238, 'osona':1378, 
 'pirineos':2020,'reus':1324,'sabadell':3275,'solsones':347,'terrassa':1947,'terres-de-l-ebre':2821,'valle-oriental':2279, 
 'vilafranca':733,'vilanova':625}
#es_cnt = 14938   , and db.catnews.spanish.count() = 14938
#cat_cnt = 22972  , and db.catnews.catalan.count() = 22972
#Diegos-MacBook-Pro:comarcas dolano$ ls -R | grep txt | wc -l   37910

c = 0
es_cnt = 0
cat_cnt = 0
for coma in comarcas:
    print coma+" - "
    cur = 0
    for root, subFolders, files in os.walk(os.path.join(rootdir_comarcas,coma)):    
        if subFolders == []:          
            if len(os.listdir(root)) > 0: 
                    c = c + 1;
                    if c > 0:
                        #print root 
                        for filename in os.listdir(root):
                            #print "\n***\t"+filename
                            f = open(os.path.join(root,filename),"r")
                            text = f.read()
                            
                            jso = {}      
                            jso["source"] = "la vanguardia"
                            textp = text.split("\n")
                            jso["title"] = textp[0]
                            jso["body"] = textp[1:][0].replace("’","'").replace("“",'"').replace("”",'"')                            
                            
                            datepieces = root.split("/")[-3:]
                            jso["date"] = "-".join(datepieces)
                            sectionpieces = root.split("/")[-5:-3]
                            jso["section"] = " - ".join(sectionpieces)
                            try:
                                validate(jso["date"])
                            except e:
                                datepieces = root.split("/")[-4:-1]
                                jso["date"] = "-".join(datepieces)
                                sectionpieces = root.split("/")[-6:-4]
                                jso["section"] = " - ".join(sectionpieces)
                    
                            #do language detection
                            jso["language"] = det_language(jso["body"])
                            #print(jso)
                          
                            if jso["language"] == "spanish":
                                #print "add to spanish db\n"
                                db.catnews.spanish.insert(jso)
                                es_cnt = es_cnt + 1
                            else:
                                #print "add to catalan db\n"
                                db.catnews.catalan.insert(jso)
                                cat_cnt = cat_cnt + 1
                            cur = cur + 1
    print str(cur)




###VERIFY RESULTS
print(es_cnt)
#for c in db.catnews.spanish.find():
#    print c
print db.catnews.spanish.count() 
#db.catnews.spanish.drop()


print(cat_cnt)
#for c in db.catnews.catalan.find():
#    print c
print db.catnews.catalan.count() 




######HANLDE GLOBALS#########
globs = ["articulos-opinion","cultura","deportes","economia","editoriales","gente","internacionales","ocio","opinion-director","politica","sucesos","tecnologia","vida"]

#cultura dolano$ ls -R | grep txt | wc -l   61247
#deportes dolano$ ls -R | grep txt | wc -l  125216
#economia dolano$ ls -R | grep txt | wc -l  124921
#editoriales dolano$ ls -R | grep txt | wc -l    9067
#gente dolano$ ls -R | grep txt | wc -l   24469
#internacionales dolano$ ls -R | grep txt | wc -l   87260
#ocio dolano$ ls -R | grep txt | wc -l   37159
#opinion-director dolano$ ls -R | grep txt | wc -l    7083
#politica dolano$ ls -R | grep txt | wc -l  148855
#sucesos dolano$ ls -R | grep txt | wc -l  142925
#tecnologia dolano$ ls -R | grep txt | wc -l   23882
#vida dolano$ ls -R | grep txt | wc -l  134253
#global dolano$ ls -R | grep txt | wc -l  926337

res = {"articulos-opinion":0, "cultura":61247, "deportes":125216, "economia":124921, "editoriales":9067, 
       "gente":24469, "internacionales":87260, "ocio":37159, "opinion-director":7083, "politica":148855, 
       "sucesos":142925, "tecnologia":23882, "vida":134253}

#catalan- 157950, spanish- 768387
#spanish db. 768387 out of 850585 total ( 82,198 which is comarcas/regionales)
#catalan db. 157950 out of 208145 total ( 50,195 which is comarcas/regionales)
#total :  1,058,730 records

c = 1
es_cnt = 0
cat_cnt = 0
for gs in globs:
    print gs+" - "
    cur = 0
    for root, subFolders, files in os.walk(os.path.join(rootdir_global,gs)):    
        if subFolders == []:          
            if len(os.listdir(root)) > 0:                     
                    if c > 0:
                        #print root 
                        for filename in os.listdir(root):
                            c = c + 1
                            #print "\n***\t"+filename
                            f = open(os.path.join(root,filename),"r")
                            text = f.read()
                            
                            jso = {}      
                            jso["source"] = "la vanguardia"
                            textp = text.split("\n")
                            jso["title"] = textp[0]
                            jso["body"] = textp[1:][0].replace("’","'").replace("“",'"').replace("”",'"')                            
                            
                            datepieces = root.split("/")[-3:]
                            jso["date"] = "-".join(datepieces)
                            sectionpieces = root.split("/")[-5:-3]
                            jso["section"] = " - ".join(sectionpieces)
                            try:
                                validate(jso["date"])
                            except e:
                                datepieces = root.split("/")[-4:-1]
                                jso["date"] = "-".join(datepieces)
                                sectionpieces = root.split("/")[-6:-4]
                                jso["section"] = " - ".join(sectionpieces)
                    
                            #do language detection
                            jso["language"] = det_language(jso["body"])
                            #print(jso)
                            #pp.pprint(json)                          
                            #print(json.loads(json.JSONEncoder(ensure_ascii=False).encode(jso)))
                            #print(json.dumps(json.JSONEncoder(ensure_ascii=False).encode(jso),ensure_ascii=False))
                            #print(json.loads(json.JSONEncoder(ensure_ascii=False).encode(jso),))
                          
                            if jso["language"] == "spanish":
                                #print "add to spanish db\n"
                                db.catnews.spanish.insert(jso)
                                es_cnt = es_cnt + 1
                            else:
                                #print "add to catalan db\n"
                                db.catnews.catalan.insert(jso)
                                cat_cnt = cat_cnt + 1
                            cur = cur + 1
    print str(cur)+"\n"
    
print "catalan- "+str(cat_cnt)+", spanish- "+str(es_cnt)

###VERIFY RESULTS
print(es_cnt)
#for c in db.catnews.spanish.find():
#    print c
print db.catnews.spanish.count()
#db.catnews.spanish.drop()


print(cat_cnt)
#for c in db.catnews.catalan.find():
#    print c
print db.catnews.catalan.count()




######HANDLE REGIONES##########
#REGIONES
#regiones dolano$ ls -R | grep txt | wc -l   94483
#barcelona dolano$ ls -R | grep txt | wc -l   57195
#girona dolano$ ls -R | grep txt | wc -l   15767
#lleida dolano$ ls -R | grep txt | wc -l   12537
#tarragona dolano$ ls -R | grep txt | wc -l    8984

#barcelona -  57195, girona - 15767, lleida - 12537, tarragona - 8984
#catalan- 27223, spanish- 67260
#spanish db.  67260  out of total size 82198 (14,938 which is comarcas)
#catalan db.  27223  out of total size 50195 (22,972 which is comarcas)


regiones = ["barcelona","girona","lleida","tarragona"]
c = 1
es_cnt = 0
cat_cnt = 0
for rs in regiones:
    print rs+" - "
    cur = 0
    for root, subFolders, files in os.walk(os.path.join(rootdir_regiones,rs)):    
        if subFolders == []:          
            if len(os.listdir(root)) > 0:                     
                    if c > 0:
                        #print root 
                        for filename in os.listdir(root):
                            c = c + 1
                            #print "\n***\t"+filename
                            f = open(os.path.join(root,filename),"r")
                            text = f.read()
                            
                            jso = {}      
                            jso["source"] = "la vanguardia"
                            textp = text.split("\n")
                            jso["title"] = textp[0]
                            jso["body"] = textp[1:][0].replace("’","'").replace("“",'"').replace("”",'"')                            
                            
                            datepieces = root.split("/")[-3:]
                            jso["date"] = "-".join(datepieces)
                            sectionpieces = root.split("/")[-5:-3]
                            jso["section"] = " - ".join(sectionpieces)
                            try:
                                validate(jso["date"])
                            except e:
                                datepieces = root.split("/")[-4:-1]
                                jso["date"] = "-".join(datepieces)
                                sectionpieces = root.split("/")[-6:-4]
                                jso["section"] = " - ".join(sectionpieces)
                    
                            #do language detection
                            jso["language"] = det_language(jso["body"])
                            #print(jso)
                            #pp.pprint(json)                          
                            #print(json.loads(json.JSONEncoder(ensure_ascii=False).encode(jso)))
                            #print(json.dumps(json.JSONEncoder(ensure_ascii=False).encode(jso),ensure_ascii=False))
                            #print(json.loads(json.JSONEncoder(ensure_ascii=False).encode(jso),))
                          
                            if jso["language"] == "spanish":
                                #print "add to spanish db\n"
                                db.catnews.spanish.insert(jso)
                                es_cnt = es_cnt + 1
                            else:
                                #print "add to catalan db\n"
                                db.catnews.catalan.insert(jso)
                                cat_cnt = cat_cnt + 1
                            cur = cur + 1
    print str(cur)+"\n"
    
print "catalan- "+str(cat_cnt)+", spanish- "+str(es_cnt)


###VERIFY RESULTS
print(es_cnt)
#for c in db.catnews.spanish.find():
#    print c
print db.catnews.spanish.count()
#db.catnews.spanish.drop()


print(cat_cnt)
#for c in db.catnews.catalan.find():
#    print c
print db.catnews.catalan.count()
