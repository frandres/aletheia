
# coding: utf-8

# In[1]:

#cd /Users/dolano/htdocs/dama-larca/github/aletheia/keywords


# In[612]:

import json
txf = open("/Users/dolano/htdocs/dama-larca/data/sunlight-texas/texas-legislature.json")
data = json.load(txf)

districts = open("/Users/dolano/htdocs/dama-larca/data/sunlight-texas/txdistricts.json")
districtsdata = json.load(districts)


# In[614]:

#districtsdata[0]


# In[12]:

from pymongo import MongoClient
from elasticsearch import Elasticsearch

#GLOBAL VARS
es = Elasticsearch()
conn = MongoClient()
db = conn.newsdb   #db is called "newsdb"


# In[11]:

#put all texas politicians in DB, first time
#for pol in data:
#    pol["entity_type"] = "politician"
#    db.texnews.entities.insert(pol)


# In[13]:

print db.texnews.entities.find_one()
#TODO GET DISTRICT NUMBER FROM OPENSTATES if possible


# In[624]:

def get_entities(query,db):
    return db.texnews.entities.find(query)

def generate_pol_query(pobj):    
    name = pobj["full_name"]
    party = pobj["party"]
    pos = "Senator"
    if pobj["chamber"] == "lower":
        pos = "Rep"
    #TODO maybe add district name (name of town or district)
    return [party + " " +pos, name] 

def run_pol_elastic_query(q):
    query = q[0]
    name = q[1]
    origq = {"query":{"bool":{"disable_coord": True,"must": [{'match_phrase': {'body': {'query':name, 'analyzer':'analyzer_keywords' }}}],
                          "should":[{'match':{'body':{'query':query}}}]}}}
    results = es.search(index='texnews_english',size=10000, body=origq)
    if len(results['hits']['hits']) == 0:        
        print "none found so new query: " + name
        newq = {"query":{"bool":{"disable_coord": True,"must": [{'match_phrase':{'body':{'query':name,'analyzer':'analyzer_keywords'}}}]}}}
        results = es.search(index='texnews_english',size=10000, body=newq)
    return results

#initialize sentence-izer
from __future__ import unicode_literals
from ftfy import fix_text
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
punkt_param = PunktParameters()

#abbreviations to take into account TODO
#punkt_param.abbrev_types = set(['lt', 'gov', 'rep', 'mrs', 'mr', 'inc', 'sen', 'reps']) 

#TODO should I add months here:  'jan', 'feb', etc.. messes up some sentences.. just need to make sure it doesn't get removed this way
#or need to do a search/replace for abbrev month for full month

#make do this instead http://stackoverflow.com/questions/21160310/training-data-format-for-nltk-punkt
#for now just do it manually
sentence_splitter = PunktSentenceTokenizer(punkt_param)
    
    
    
def get_article_sentences(article):
    #approach 5 ( hopefully improved on approach4)
    #TODO: put this in db or config file
    subs = {'Sen.':'Senator','Lt. Gov.':'Lieutenant Governor','Rep.':'Representative', 
            'Reps.':'Representatives,', 'Gov.':'Governor'}
    if '_source' in article:
        r = article['_source']        
        if 'body' in r:
            text = fix_text(r['body']).replace('?"', '? "').replace('!"', '! "').replace('."', '. "')
            for a in subs:
                text = text.replace(a,subs[a])
            sentences = sentence_splitter.tokenize(text)
            return sentences
    return []

def entity_in_article(article,q,debug=False):
    #TODO HANDLE FALSE POSITIVE ON NAME!  for instance searching for "Scott Sanford" gets Jeffrey Scott Sanford
    #if prior character is punctuation or not a name ()
    #print article
    #print q
    query = q[0]
    name = q[1] 
    if '_source' in article:
        r = article['_source']        
        if 'body' in r:
            query_in_art = r['body'].find(query)
            if query_in_art > -1:
                if debug:
                    print "***Found query: "+query+" in article!"
                return True
            else:
                name_in_art = r['body'].find(name)
                if name_in_art > -1:
                    if debug:
                        print "***Found name: "+name+" in article!"
                    #TODO instead of return true immediately, look for Rep or Republican or anything from orginal query
                    #within some distance of the match to verify, we have something!
                    #or use nltk to check if prior or following word is a name
                    return True
    return False
    
#GLOBAL VAR
number_sentences_for_context = 3;

def search_article_for_entity(sentences,q):
    #TODO refactor this to make it more generalizable if need be
    query = q[0]
    name = q[1]
    
    sentences_length = len(sentences)
    for s in sentences:
        loc = s.find(query)
        if loc > -1:
            print "*** Full found: " + r['date'] + ", " + r['section'] + " ," + r['title'] + " ," + r['article-num']
            print "\t"+r['body'][loc-10:loc+len(query)]
        else:
            loc = r['body'].find(name,start)
            if loc > -1:
                    print "*** Name found at spot( "+str(loc)+" of "+str(len(r['body']))+" ): " + r['date'] + ", " + r['section'] + " ," + r['title'] + " ," + r['article-num']
                    temp = r['body']            


# In[485]:

#x = "Rehabilitation"
#x.isupper()


# In[889]:

#initialize Named Entity Recognition engine
import sys, os, string
#GLOBAL VAR
mitiepath = "/Users/dolano/htdocs/dama-larca/mitie/MITIE-master/"
sys.path.append(mitiepath+"mitielib")

from mitie import *
from collections import defaultdict

ner = named_entity_extractor(mitiepath+'MITIE-models/english/ner_model.dat')

def get_named_entities(sentences):
    #deprecated in favor of per sentence version
    #tokens = tokenize("With his Republican primary victory safely behind him, Texas Gov. Rick Perry is still working hard to court conservative voters.  Perry made a guest appearance Saturday night at an event in Tyler hosted by conservative radio and television talk-show host Glenn Beck.  Speculation is swirling that Perry may consider a run for president in 2012 and experts say appearing with Beck keeps the governor in the minds of conservative voters. Perry has denied he's considering a run.  Perry calls Beck a national leader with a powerful message about Washington and its out of control spending. Perry is running for a third term as governor. He faces former Houston Mayor Bill White, a Democrat, in November.")
    text = " ".join(sentences)
    try:
        tokens = tokenize(text)
        entities = ner.extract_entities(tokens) 
        return get_entities_details(tokens,entities,debug)        
        #return [tokens,entities]        
    except:
        print "ERROR: can not tokenize: "+text
        return [[],[]]

def get_entities_details(tokens,entities,debug=False):    
    reso = []
    for e in entities:
        range = e[0]
        tag = e[1]
        score = e[2]
        score_text = "{:0.3f}".format(score)
        entity_text = " ".join(tokens[i] for i in range)
        if debug == True:
            print "\t\tScore: " + score_text + ": " + tag + ": " + entity_text    
        reso.append({'score': score_text, 'tag': tag, 'text': entity_text})
    
    return reso    
    
def get_named_entities_per_sentence(sentences,debug=False):
    #TODO make this return entities in the order in which they appear in the sentence
    res = []
    if debug:
        print "\nIn Get named entities per sentence!"
    for s in sentences:
        try:
            tokens = tokenize(s)            
            entities = ner.extract_entities(tokens)      
            if debug == True:
                print "\nSentence: " + s
                
            ret = get_entities_details(tokens,entities,debug)
            res.append(ret)   
        except:
            if debug == True:
                print "ERROR: can not tokenize as is so removing ascii characters"
            news = filter(lambda x: x in string.printable, s)
            try:
                tokens = tokenize(news)            
                entities = ner.extract_entities(tokens)      
                if debug == True:
                    print "\nSentence: " + news
                
                ret = get_entities_details(tokens,entities,debug)
                res.append(ret)   
            except:
                print "SUPER ERROR - couldn't tokenize as is or without ascii characters" + s
                return []    

    return res

def verify_entity_found(entities,name):
    #[[{u'text': u'AUSTIN', u'score': 0.8039498955658273, u'tag': 'LOCATION'}, 
      #{u'text': u'Texas House', u'score': 1.0538336421043815, u'tag': 'LOCATION'}], 
     #[{u'text': u'House', u'score': 0.6314707951634598, u'tag': 'ORGANIZATION'}, 
      #{u'text': u'Texas Lottery Commission', u'score': 1.254348992018721, u'tag': 'ORGANIZATION'}], [....]]
    ret = False
    #es = [a['text'] for a in e for e in entities]
    es = []
    for e in entities:
        for a in e:
            if a['text'] not in es:
                es.append(a['text'])
                
    if name in es:
        ret =True
    return ret

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
def entity_in_list(ent,li):
    entl = ent.lower()
    ret = [False,""]
    for l in li:
        if entl == l.lower():
            ret = [True,l]
            break
    return ret

def disambiguate_entities(entities,sentences,db,debug=False):
    #TODO pull out big sections into seperate functions
    if debug:
        print "In Disambiguate Entities"
        print "Sentences: "
        print " ".join(sentences)
        print "Entities"
        print entities  
    
    #TODO        
    res = {'ORGANIZATION':{},'PERSON':{},'LOCATION':{},'MISC':{},'BILL':{}}
    titles = ["Governor","Gov","Representative","Rep","Senator","Sen","Commissioner","Speaker","Chairman","Chairwoman",
              "Judge", "Member","member","Trustee","trustee","President","president","Lawyer","lawyer","Candidate",
              "incumbent","Incumbent","challenger","businessman"]
    
    naive_coref = []
    local_id = 0
    prior = {"text":"","tag":"MISC"}
    cur_sen = 0
    skip = 0
    for sent in entities:
        for ind,e in enumerate(sent):
            if skip == 1:
                #skip when the post word has been accounted for MAYBYE
                skip = 0
                if debug:
                    print "Skipping " + e['text'] + " as its already been added in prior step!"
                continue
                
            t = e['text']
            tlower = t.lower()
            already_in, tswap = entity_in_list(t,res[e['tag']])
            if already_in:
                t = tswap
                #print "TODO " + t + ' already in so give it same token'                
                res[e['tag']][t]['id'].append(local_id)
                res[e['tag']][t]['sentence'].append(cur_sen)
            else:
                #TODO INCORPORATE FUZZY AND 
                #ALSO LOOK FOR PRIOR ENTITY IN FRONT OF PEOPLE, so we can find roles better
                if t.find('D-') == 0 or t.find('R-') == 0:
                    #found a clear sign that the prior (mostly likely) or next (unlikely) entity is a politician
                    #print "Found possible politician "+t+" so look at prior"
                    #print prior
                    
                    ps = t.split('-')
                    party = "Republican" if ps[0] == 'R' else "Democrat"
                    loc = ps[1]   
                    pt = prior['text']
                    if pt in res[prior['tag']]:
                        if debug:
                            print "Found D- or R- with "+t+" , now adding party: "+party+" and location: "+loc
                            
                        res[prior['tag']][pt]["party"] = party 
                        res[prior['tag']][pt]["location"] = loc
                    else:
                        if debug:
                            print "ERROR! Did not find "+pt+" with tag "+prior['tag']+", in results list"
                            print res
                            print sentences[cur_sen]
                            print "TODO SEE IF PRIOR WORDS are Uppercased and just weren't considered as an Entity and use them"
                        break
                    
                elif tlower == 'senate bill' or tlower == 'house bill':
                    #possible bill so find location in sentence and include number of bill                    
                    ps = sentences[cur_sen].split()
                    if debug:
                        print "Found Senate or House Bill"
                        print ps
                        
                    for i, j in enumerate(ps):        
                        if j == 'Bill' or j == 'bill':
                            if debug:
                                print "*Found "+j+" "+str(ps[i+1])
                            
                            bb = ps[i+1].replace(":","")
                            
                            if is_number(bb) == True:
                                if debug:
                                    print "numeric"
                                bill = ps[i-1]+" " +ps[i]+" "+bb
                                if debug:
                                    print "Found bill: " + bill
                                res['BILL'][bill] = {'id':[local_id], 'sentence':[cur_sen]}

                                
                elif t == 'SB' or t =='HR':
                    #possible bill so find location in sentence and include number of bill                    
                    ps = sentences[cur_sen].split()
                    if debug:
                        print "FOUND SB/HR!"
                        print ps
                        
                    for i, j in enumerate(ps):        
                        if j == 'SB' or j == 'HR':
                            bb = ps[i+1].replace(":","")
                            if is_number(bb):
                                bill = ps[i]+" "+bb
                                if bill in res['BILL']:
                                    if debug:                                    
                                        print "Found bill already"
                                        print bill
                                    res['BILL'][bill]['id'].append(local_id)
                                    res['BILL'][bill]['sentence'].append(cur_sen)
                                    
                                elif "House Bill "+bb in res['BILL'] or "Senate Bill "+bb in res['BILL']:
                                    if debug:
                                        print "TODO found bill already so add to alias of it"
                                    if "House Bill "+bb in res['BILL']:
                                        res['BILL']["House Bill "+bb]['id'].append(local_id)
                                        res['BILL']["House Bill "+bb]['sentence'].append(cur_sen)
                                    else:
                                        res['BILL']["Senate Bill "+bb]['id'].append(local_id)
                                        res['BILL']["Senate Bill "+bb]['sentence'].append(cur_sen)                                        
                                else:   
                                    res['BILL'][bill] = {'id':[local_id], 'sentence':[cur_sen]}
                                    
                elif e['tag'] == "PERSON":
                    #check that this person is definitely not already in res 
                    #TODO: ( this only works if full name appears before single) 
                    #     thus, at end we'll have to fuzzy combine of PERSON list , and for ORGANIZATION list
                    # TODO EVENTUALLY USE DBPEDIA to verify
                    found = 0
                    if len(t.split()) == 1:
                        #check if this last name                        
                        for i, j in enumerate(res['PERSON']):        
                            if t in j:
                                if debug: 
                                    print "Found name in PERSON ALREADY"+t+" in "+j
                                res['PERSON'][j]['id'].append(local_id)
                                res['PERSON'][j]['sentence'].append(cur_sen)
                                found = 1
                        
                        if found == 0:
                            #TODO Check to see if there is another name after or before
                            res['PERSON'][t] = {'id':[local_id], 'sentence': [cur_sen]}

                                
                    elif len(sent) > ind + 1:                                                   
                        #check if next entity in sentence is a location and if the are combined by "of" or "from"
                        next_ent = sent[ind + 1]
                        ff = 0
                        if next_ent['tag'] == 'LOCATION':
                            start = sentences[cur_sen].find(e['text'])
                            end = sentences[cur_sen].find(next_ent['text'])
                            if end > start:
                                ps = sentences[cur_sen][start+len(e['text']):end].split()
                                if len(ps) == 1:
                                    if ps[0] == "of" or ps[0] == "from":
                                        res[e['tag']][t]= {'id':[local_id],'location':next_ent['text'], 'sentence':[cur_sen]}
                                        ff = 1
                        if ff == 0:
                            res[e['tag']][t]= {'id':[local_id],'sentence':[cur_sen] }
                                                                   
                    else:
                        res[e['tag']][t]= {'id':[local_id], 'sentence':[cur_sen]}                    

                    #LOOK FOR Governor, Represenative, Rep, Senator, Commisioner, etc in word before and 
                    #if so add, and check that is not already and an entity, etc                    
                    ps = sentences[cur_sen].split()
                    if debug:
                        print "\nAAAAAA: Looking if word prior to PERSON "+t+ " is a title"
                        print ps
                       
                    check = t    
                    if len(t.split()) > 1:
                        check = t.split()[0]
                        
                    #does this handle case 47? with Jessica Farrer and then Farrer after
                    found_once = 0 
                    for i,c in enumerate(ps):
                        #if (c == check or (check in c and "'s" in c)) and found_once == 0:
                        if (c == check or (c.replace("'s","").replace(":",""))) and found_once == 0:
                            if len(t.split()) > 1:
                                #verify actually have correct person when Joe Wilson and Joe Matts in same sentence
                                if len(ps) > i +1:
                                    if ps[i+1].replace(":","").replace(",","").replace(".","").replace("?","").replace("'s","") != t.split()[1]:
                                        if debug:
                                            print "Found false match: "+ps[i]+" "+ps[i+1]+" vs "+t+" so continue to see if you find it"
                                        continue
                                    
                            found_once = 1        
                            if ps[i-1] in titles:
                                if debug:
                                    print "FOUND TITLE "+ ps[i-1]
                                    print "look in prior: "+prior['text']
                                #TODO: MAKE THIS GO FARTHER BACK THAN JUST ONE WORD 
                                #  if the one before is CAPS or part of the prior entity which is an ORG    
                                #  in which case add org + ps[-1] as position, and remove org from res entities
                                
                                #TODO: make this also check next word, ex.  Jim Moon, president of Conoco
                                if 'text' in prior:
                                    if ps[i-1] in prior['text']:
                                        #look if title is part of prior entity
                                        res[e['tag']][t]['position'] = [prior['text']]
                                        
                                        #and then remove prior entity
                                        if prior['text'] in res[prior['tag']]:
                                            if debug:
                                                print "prior[text]: "+prior['text']
                                                print "prior[tag]:"
                                                print res[prior['tag']]
                                                
                                            #res[prior['tag']].remove(prior['text'])
                                            del res[prior['tag']][prior['text']]
                                        else:
                                            if debug:
                                                print "ERROR didn't find prior text: "+prior['text']+" with tag: "+prior['tag']+" in res"
                                                print "This means it didn't get inserted properly before, so look into it"
                                    else:
                                        res[e['tag']][t]['position'] = [ps[i-1]]                                                
                                else:
                                    #otherwise just use prior word as title
                                    res[e['tag']][t]['position'] = [ps[i-1]]
                            else:
                                #if prior word is in prior entity which is a one named PERSON, 
                                if ps[i-1] in prior['text'] and prior['tag'] == 'PERSON' and len(prior['text']) == 1:                                                                        
                                    if debug:
                                        print "????FOUND possible names that should be combined: "+prior['text']+" and "+t
                                     
                                    #TODO    
                                    #which was not found in res already (ie, it was added to prior object)                                                                        
                                    print res
                                    #combine the prior PERSON and this person into ONE, if this person is of size one
                                elif ps[i-1] == "Democrat" or ps[i-1] == "Republican":
                                    if debug:
                                        print "Not title, but yes Democrat/Republican so add"
                                    res[e['tag']][t]['party'] = [ps[i-1]]
                                    
                elif e['tag'] == 'ORGANIZATION' and t.split()[-1].lower() == "district":
                    #look to see if this like Texas House District 133, 
                    if debug:
                        print "Check if ORG: "+t+ ", is followed by a number"
                    loc = sentences[cur_sen].find(t)
                    if loc > -1:
                        loc = loc + len(t)
                        possible_num = sentences[cur_sen][loc:].split()[0]
                        possible_num = possible_num.replace(":","").replace(",","")
                        if is_number(possible_num):
                            if debug:
                                print "Found District "+possible_num
                            t = t + " " + possible_num
                    
                    res[e['tag']][t]= {'id':[local_id], 'sentence':[cur_sen]}                        
                
                elif e['tag'] == 'LOCATION':
                    #look to see if next word is in upper case,
                    ps = sentences[cur_sen].split()
                    
                    if t.split()[-1].lower() == "district":
                        if debug:
                            print "Check if LOCATION: "+t+ ", is followed by a number"
                        loc = sentences[cur_sen].find(t)
                        if loc > -1:
                            loc = loc + len(t)
                            possible_num = sentences[cur_sen][loc:].split()[0]
                            possible_num = possible_num.replace(":","").replace(",","")
                            if debug:
                                print "Found "+t+" at position "+str(loc)
                                print "Check if "+possible_num+" is a number"
                                
                            if is_number(possible_num):
                                if debug:
                                    print "Found District "+possible_num
                                t = t + " " + possible_num
                                #treat Districts as Organizations (maybe incorrect, but consistent)
                                res["ORGANIZATION"][t]= {'id':[local_id], 'sentence':[cur_sen]} 
                                continue
                        
                    if debug:
                        print "\nAAAAAA: Looking if word after LOCATION "+t+ " is in CAPS and part of an ORGANIZATION NAME"
                        print ps
                       
                    check = t    
                    if len(t.split()) > 1:
                        check = t.split()[-1]
                    
                    if debug:
                        print "check is "+check
                        
                    added = 0
                    found_once = 0
                    for i,c in enumerate(ps):
                        if c == check and found_once == 0:
                            if len(t.split()) > 1:
                                #verify actually have correct location when two have same starting word in sentence
                                if i+1 >= len(ps):
                                    #to fix error with a=189 (where last word in sentenc is Location)
                                    continue
                                    
                                if ps[i+1].replace(":","").replace(",","") != t.split()[1]:
                                    continue
                                    
                            found_once = 1
                            if debug:
                                print "FOUND C = CHECK"
                            if len(ps)-1 > i:
                                start = 1
                                if debug:
                                    print "NOW CHECK IF "+ps[i+start]+ " is upper or stopword(TODO)"  #of, at, and, &   
                                if ps[i+start][0].isupper():
                                    possible_add = ps[i] + " " + ps[i+start]
                                    if debug:
                                        print "Found "+ps[i+start]+ " which is uppercase"
                                    if len(sent) - 1 > ind:
                                        next_ent = sent[ind + 1]
                                        next_front = next_ent['text']
                                        if len(next_ent['text'].split()) > 1:
                                            next_front = next_ent['text'].split()[0]
                                            
                                        if next_front != ps[i+1]:
                                            if debug:
                                                print 'Next front: '+next_front+' not equal to '+ps[i+1]
                                            start = start + 1
                                            exit = 0
                                            while i + start < len(ps) and start < 5 and exit ==0:
                                                if ps[i+start][0].isupper() and ps[i+start] != next_front and start < 5:
                                                    possible_add = possible_add + " " + ps[i+start]
                                                
                                                if ps[i+start] == next_front:
                                                    exit = 1
                                                    
                                                start = start + 1
                                                
                                                
                                            if debug:
                                                print "EEEEE Possible ROLE/ORGANIZATION FOUND: " + possible_add
                                                print "Next entity is a "+next_ent['tag'] + " and last = " + possible_add.split()[-1]
                                                
                                            if next_ent['tag'] == 'PERSON' and possible_add.split()[-1] in titles:
                                                if debug:
                                                    print "PLACE THE PRIOR AS ROLE FOR "+next_ent['text']
                                                    #check if PERSON entity already in res
                                                    f = 0
                                                    
                                                    for i, j in enumerate(res['PERSON']): 
                                                        if j == next_ent['text']:                                                            
                                                            #add role to that user
                                                            if 'position' in res['PERSON'][j]:
                                                                res['PERSON'][j]['position'].append(possible_add)
                                                            else:
                                                                res['PERSON'][j]['position'] = [possible_add]
                                                            f = 1
                                                            added = 1
                                                        else:
                                                            if len(next_ent['text'].split()) == 1:
                                                                if next_ent['text'] in j:
                                                                    #add role to user
                                                                    if 'position' in res['PERSON'][j]:
                                                                        res['PERSON'][j]['position'].append(possible_add)
                                                                    else:
                                                                        res['PERSON'][j]['position'] = [possible_add]
                                                                    f = 1  
                                                                    added = 1
                                                    if f == 0:
                                                        skip = 1
                                                        if debug:
                                                            print "PERSON NOT FOUND IN RES so add along with position and then skip when it comes up!"
                                                        res['PERSON'][next_ent['text']]= {'id':[local_id], 'sentence':[cur_sen], 'position': [possible_add]}
                                                        added = 1
                                            else:
                                                if debug:
                                                    print "TODO next is not a person so add " + possible_add + " as ORG"                            
                                                    res['ORGANIZATION'][possible_add]= {'id':[local_id], 'sentence':[cur_sen]}
                            
                    if added == 0:
                            res[e['tag']][t]= {'id':[local_id], 'sentence':[cur_sen]}
                    #if so take all next words which are in uppercase and aren't part of the next entity for the line
                else:
                    res[e['tag']][t]= {'id':[local_id], 'sentence':[cur_sen]}
                    
            local_id = local_id + 1
            prior = e
        cur_sen = cur_sen + 1
    
    if debug:
        print "\n"
        print res

    return res


# In[915]:

def get_sentence_with_entity_id(id,entities,sentences,debug):
    if debug == True:
        print "looking for id: "+str(id)
    cur_sen = 0
    cur_ent = 0
    for sent in entities:
        for ind,e in enumerate(sent):
            if cur_ent == id:
                return [cur_sen, sentences[cur_sen]]
            else:
                cur_ent = cur_ent + 1
        cur_sen = cur_sen + 1
    return [-1,""]
    
def get_entities_for_sentence(sent_num,dis_entities,debug=False):
    if debug:
        print "In Get Entities for Sentence"
        print "Sent num: "+str(sent_num)
        print "DisEntities:"
        print dis_entities
        
    res = []
    for k in dis_entities:
        if debug:
            print "CATEGORY: " + k  #"ORGANIZATION", "MISC", etc
        for ent in dis_entities[k]:
            ent_obj = dis_entities[k][ent]
            if debug:
                print "Ent: "+ ent #  "senate", "etc"
                print "Ent Obj"
                print ent_obj

            if sent_num in ent_obj['sentence']:
                indk = ent_obj['sentence'].index(sent_num)
                if debug:
                    print "Find "+str(sent_num)+" which is index: "+str(indk)+" in ent_obj above"
                res.append({"type":k,"name":ent,"ent_id":ent_obj['id'][indk]})
    
    if res != []:
        #sort by ent_id
        res = sorted(res)
             
    return res

def get_entities_for_surrounding_sentences(sent_num,dis_entities,upperbound,debug):
    #uses global var number_sentences_for_context
    
    #go backwards
    prior_sentences = []
    if sent_num > 0:
        start = sent_num - number_sentences_for_context 
        if start < 0:
            #get from 0 to sent
            start = 0
            
        while start < sent_num:
            prior_sentences.append(get_entities_for_sentence(start,dis_entities))
            start = start + 1

    #go forwards
    next_sentences = []
    if sent_num < upperbound:
        start = sent_num + 1 
        end = sent_num + number_sentences_for_context 
        if end > upperbound:
            if debug:
                print "End "+str(end)+" greater than upperbound "+ str(upperbound) + " so setting it to it"
            end = upperbound
        while start <= end:
            next_sentences.append(get_entities_for_sentence(start,dis_entities))
            start = start + 1        

    return [prior_sentences,next_sentences]

def get_entities_further_away_in_article(sent_num,dis_entities,upperbound,debug):
    #uses global var number_sentences_for_context
    
    #go backwards
    prior_farther_sentences = []
    if sent_num > 0:
        start = 0
        end = sent_num - number_sentences_for_context 
        if end >= 0:            
            while start <= end:
                prior_farther_sentences.append(get_entities_for_sentence(start,dis_entities))
                start = start + 1

    #go forwards
    next_farther_sentences = []
    if sent_num < upperbound:
        start = sent_num + number_sentences_for_context + 1 
        end = upperbound 
        if start < upperbound:          
            while start <= end:
                next_farther_sentences.append(get_entities_for_sentence(start,dis_entities))
                start = start + 1        

    return [prior_farther_sentences,next_farther_sentences]
    

def get_relations(starting_politician, entities,dis_entities,sentences,db,debug):
    #TODO maybe add rules for how to consider what to include here 
    # for instance if first word is HIGHLIGHTS we know there are various news items in this article 
    
    
    # so we should only include those from same section.
    rules = {"all_caps_as_new_paragraph"}    
    ent = dis_entities['PERSON'][starting_politician]
    
    res = []
    num_inst = len(ent['sentence'])
    
    if debug:
        print "In Get Relations"
        print "Politician: "+starting_politician
        print "Entities"
        print entities
        print "Disambiguated"
        print dis_entities
        print "Sentences"
        print sentences
        print "Ent"
        print ent
    
    i = 0
    sent_matches = []
    
    #TODO make sure you aren't double counting anything!
    while i < num_inst:        
        #sent_num = ent['id'][i]
        sent_num = ent['sentence'][i]
        sent = sentences[sent_num]
        if debug:
            print "@@@@@@Working on match from sentence "+str(sent_num)
            print sent
            
        #get entities in same sentence and add to res
        same_sent = get_entities_for_sentence(sent_num,dis_entities,False)  #instead of debug
        if debug:
            print "ENTITIES IN SAME SENTENCE"
            for s in same_sent:
                print s
            
        #get entities in surrounding three sentences
        prior_sents, next_sents = get_entities_for_surrounding_sentences(sent_num,dis_entities,len(sentences)-1,debug)
        if debug:
            print "\nPRIOR "+ str(number_sentences_for_context)+" sentences"
            for p in prior_sents:
                print p
            print "\nNEXT "+ str(number_sentences_for_context)+" sentences"
            for ns in next_sents:
                print ns
            
        #get entities in same article 
        prior_far, next_far = get_entities_further_away_in_article(sent_num,dis_entities,len(sentences)-1,debug)
        if debug:
            print "\n\nPRIOR FARTHER THAN "+ str(number_sentences_for_context)+" sentences" 
            for pf in prior_far:
                print pf
            print "\nNEXT FARTHER THAN " + str(number_sentences_for_context)+" sentences"
            for nf in next_far:
                print nf
        
        if num_inst == 1:
            res = [same_sent, prior_sents, next_sents, prior_far, next_far]
        else:
            res.append([same_sent, prior_sents, next_sents, prior_far, next_far])
        i = i + 1
                
    return [ent['sentence'], res]


# In[992]:

def get_ent_to_global(dis_entities,debug):
    ent = {}
    ent_to_global = {}    
    
    for r in dis_entities:
        for e in dis_entities[r]:
            cur = dis_entities[r][e]
            cur["entity_type"] = r
            ent[e] = cur
            
            #see if current entity exists in global list
            if debug:
                print "\nChecking if "+e+" is in global index"
                
            if e in global_index:
                ent_to_global[e] = global_index[e]                
                if debug:
                    print "\tFound in global index"
                    print "\tTODO VERIFY CORRECT:"
                    print "Global:"
                    print global_entities[ent_to_global[e]]                                                
                    print "\nvs Local:"
                    print cur
            else:
                if debug:
                    print "\tNot found directly in global index so check for something similar"
                
                handled = 0
                for ge in global_index:                    
                    if e.lower() == ge.lower():
                        if debug:
                            print "\tFound "+ge+" which is equal lowercase wise and using it as entity"
                        ent_to_global[e] = global_index[ge]
                        handled = 1
                        break
                    else:
                        if e in ge:                         
                            if debug:
                                print "\tNow: Found for something which subsumes it: "+ge
                                print "\tTODO:  check if they have same type, and are same. Don't do for locations.  this must be failsafe.. "                             
                                print "Global:"
                                print global_entities[global_index[ge]]
                                print "\nvs Local:"
                                print cur
                            
                            if (global_entities[global_index[ge]]['entity_type'] == cur['entity_type'] 
                                or global_entities[global_index[ge]]['entity_type'] == "politician" )and cur['entity_type'] == "PERSON":
                                if debug:
                                    print "\tFound these two to be the same entity!"
                                handled = 1
                                ent_to_global[e] = global_index[ge]
                                break
                    
                if handled == 0:
                    if debug:
                        print "\tDid not find "+e+" in global index so add it"
                    cur["full_name"] = e
                    global_entities.append(cur)
                    global_index[e] = len(global_entities) - 1
                    ent_to_global[e] = global_index[e]
                        
    if debug:
        print "ENT:"
        print ent
        print "\nENT_TO_GLOBAL:"
        print ent_to_global
        
    return [ent_to_global,ent]


def handle_single_match_same_sentence(sentn, relations, ent_to_global,same_sent,global_index_val, loc_index,debug):
    if debug:
            print "Sent num: "+str(sentn)        
    
    #TODO WHAT TO DO IF THERE ARE MULTIPLE EXACT HITS IN THE DOCUMENT
    #TODO MAKE THIS WORK FOR OTHER ENTITIES (right now its the politician you are searching for centeric) 
    for i, s in enumerate(same_sent):
        if debug:                
            print "Same sentence item:"
            print s              

        if s['name'] == loc_index:                
            if debug:
                print "found itself so don't add relation"
            continue                    
        else:                                
            t2id = ent_to_global[s['name']]

            #MAKE SURE THE TWO TERMS ARE NOT THE SAME (use ids and maybe substring)
            if global_index_val == t2id:
                    if debug:
                        print "DO NOT ADD AS THEY ARE THE SAME ENTITY GLOBABLY"
            else:                    
                #MAKE SURE RELATION NOT ALREADY IN
                exists = 0
                for rela in relations:
                    if rela['term1_id'] == global_index_val and rela['term2_id'] == t2id and rela['type'] == "same sentence" and rela['sentence_num'] == sentn:
                        exists = 1

                if exists == 0:   
                    if debug:
                        print "\tadd SAME SENTENCE relationship between "+loc_index +" (id: "+str(global_index_val)+") and "+s['name']+" (id: "+str(t2id)+") at sentence: "+str(sentn)                    
                    relations.append({'term1':loc_index, 'term1_id':global_index_val, 
                                      'term2':s['name'], 'term2_id':t2id, 'type':'same sentence', 
                                      'text_snippet':sentences[sentn], 'sentence_num':sentn})
                else:
                    if debug:
                        print "\tRELATION ARLEADY EXISTS LOCALLY SO DON'T ADD IT"

        #TODO CHECK IF these relations are in global_relations, though if you base things with url as key, you should be ok
        #AT END YOU'LL JUST HAVE TO POST PROCESS the global_relations list to get a list that is based on (t1id,t2id) keys  
        
        #TODO MAKE this ADD interlink relations as well! (ie, ones not based on Garnet Coleman)
    return relations

def handle_single_match_near_sentences(sentn,subtype,ent_to_global, near_sents, global_index_val, loc_index, relations, debug):
    for i,se in enumerate(near_sents):
        if debug:
            print se
        for s in se:
            if s['name'] != loc_index:
                
                if subtype =='prior':
                    thissent = sentn - number_sentences_for_context + i
                    dist = number_sentences_for_context - i
                    if thissent < 0:
                        thissent = 0 + i
                        dist = sentn - thissent
                else:
                    thissent = sentn + i + 1
                    dist = i + 1

                t2id = ent_to_global[s['name']]
                if global_index_val == t2id:
                    if debug:
                        print "DO NOT ADD AS THEY ARE THE SAME ENTITY GLOBABLY"
                else:

                    #MAKE SURE RELATION NOT ALREADY IN
                    exists = 0
                    for rela in relations:
                        if rela['term1_id'] == global_index_val and rela['term2_id'] == t2id and rela['type'] == "near":
                            if rela['subtype'] == subtype:
                                exists = 1                                

                    if exists == 0: 
                        if subtype == 'prior':
                            if debug:
                                print "\nadd PRIOR relationship between "+loc_index +" and "+s['name']

                            relations.append({'term1':loc_index, 'term1_id':global_index_val, 
                                              'term2':s['name'], 'term2_id':t2id, 'type':'near', 'subtype':subtype, 'distance': str(dist), 
                                              'text_snippet':" ".join(sentences[thissent:sentn+1]), 'sentence_num':[thissent,sentn]})
                        else:
                            if debug:
                                print "\nadd NEXT relationship between "+loc_index +" and "+s['name']
                                
                            relations.append({'term1':loc_index, 'term1_id':global_index_val, 
                                              'term2':s['name'], 'term2_id':t2id, 'type':'near', 'subtype':subtype, 'distance': str(dist), 
                                              'text_snippet':" ".join(sentences[sentn:thissent+1]), 'sentence_num':[sentn,thissent]})
                            
                    else:
                        if debug:
                            print "\tRELATION ARLEADY EXISTS LOCALLY SO DON'T ADD IT"

                #TODO CHECK IF these relations are in global_relations, though if you base things with url as key, you should be ok
                #AT END YOU'LL JUST HAVE TO POST PROCESS the global_relations list to get a list that is based on 
                #(t1id,t2id) keys  
                
    return relations

def handle_single_match_far_sentences(ent_to_global, rest, global_index_val, loc_index, relations, debug):
    for i,se in enumerate(rest):
        if debug:
            print se

        for s in se:
            if s['name'] != loc_index:                
                t2id = ent_to_global[s['name']]
                
                if global_index_val == t2id:
                    if debug:
                        print "DO NOT ADD AS THEY ARE THE SAME ENTITY GLOBABLY"
                else:
                    #MAKE SURE RELATION NOT ALREADY IN
                    exists = 0
                    for rela in relations:
                        if rela['term1_id'] == global_index_val and rela['term2_id'] == t2id and rela['type'] == "same article":                            
                            exists = 1    

                    if exists == 0:                              
                        if debug:
                            print "\nadd FAR relationship between "+loc_index +" and "+s['name']

                        relations.append({'term1':loc_index, 'term1_id':global_index_val, 
                                          'term2':s['name'], 'term2_id':t2id, 'type':'same article'})
                    else:
                        if debug:
                            print "\tRELATION ARLEADY EXISTS LOCALLY SO DON'T ADD IT" 
    return relations


# In[993]:

def get_global_entity_by_name(name):
    for i,p in enumerate(global_entities):
        if p["full_name"] == name:
            return [i,p]
    return [-1,[]]

#def check_if_article_relation_exists(t1id, t2id, url, sentnum):
    

def verify_and_save_relations(queryobj,entrelations,dis_entities,sentences,art,db,debug):
    sentnums, bgrelations = entrelations
    global_entity_index, global_entity_obj = get_global_entity_by_name(queryobj[1])
    url = art['_source']['url']
    
    if len(sentnums) > 1:
        #TODO FIX THIS SO IT WORKS FOR MULTIPLE HITS, AND FOR MULTIPLE ENTITIES
        print "MULTIPLE DIRECT HITS: "
        #use these two lines to only use first hit
        #sentnums = [sentnums[0]]
        #relations = relations[0]
        print "\nSent nums"
        print sentnums
        print "\nbgrelations"
        for bg in bgrelations:
            print "\n"
            print bg
    else:    
        same_sent, prior_sents, next_sents, prior_far_sents, next_far_sents = bgrelations
        if debug:
            print "POLITICIAN: "+ queryobj[1]+"\nALL SENTENCES"
            print sentences
            print "\nSAME SENTENCE: "
            print same_sent
            print "\nNEAR SENTENCES:"
            print prior_sents
            print next_sents
            print "\nFAR SENTENCES:"
            print prior_far_sents
            print next_far_sents
            print "\nDISAMBIGUATED ENTITIES:"
            print dis_entities                
            #print "POLITICIAN INFO (at index "+str(global_entity_index)+" ):"
            #print global_entity_obj
            
    #to avoid output of get_ent_to_glo
    pred = debug
    if len(sentnums) > 1:
        debug = False
        
    ent_to_global,ent = get_ent_to_global(dis_entities,debug) 
    debug = pred
    
    #get local index of politician along with global index and global object
    if queryobj[1] in ent:
        loc_index = queryobj[1]
    else:
        print "ERROR: didn't find "+queryobj[1]+" in entity list above so find closest approximation"
        for e in ent:
            if queryobj[1].lower() in e.lower():
                loc_index = e
                break
                
    global_index_val = global_index[loc_index]   #loc_index is the word which is the key in the global index
    global_obj = global_entities[global_index_val]
    
    if debug:
        print "index of politician in local entity list: "+loc_index
        print "index of politician in global entity list: "+str(global_index_val)
        #print global_obj
    
    
    #Now Create Relations with ent_to_global, etc
    if debug:
        print "\nNow add relationships from Same Sentence:"

    relations = []
    if len(sentnums) == 1:
        sentn = sentnums[0]
        relations = handle_single_match_same_sentence(sentn, relations, ent_to_global,same_sent,global_index_val, loc_index, debug)                    
    else:
        if debug:
            print "handle more than one direct sentence match"  #TODO HANDLE MULTIPLE SIMILARLY
        for i,sentn in enumerate(sentnums):
            same_sent, prior_sents, next_sents, prior_far_sents, next_far_sents = bgrelations[i]  
            if debug:
                print "\t sentnum: "+str(sentn)
                print "\t with same sent!"
                print same_sent
            relations = handle_single_match_same_sentence(sentn, relations, ent_to_global,same_sent,global_index_val, loc_index, debug)                    
            
            
            
    if debug:
        print "After Same Sentence, Relations:"
        print relations
        print "\nNow add relationships from Prior Sentences:"  
        
    if len(sentnums) == 1:
        subtype = "prior"
        relations = handle_single_match_near_sentences(sentn,subtype,ent_to_global, prior_sents, global_index_val, loc_index, relations, debug)             
    else:
        if debug:
            print "BIG OLE FAIL, more than one direct sentence match"  #TODO HANDLE MULTIPLE SIMILARLY
        subtype = "prior"
        for i,sentn in enumerate(sentnums):
            same_sent, prior_sents, next_sents, prior_far_sents, next_far_sents = bgrelations[i]  
            if debug:
                print "\t sentnum: "+str(sentn)
                print "\t with prior sents!"
                print prior_sents 
            #NOW HERE, TO HANDLE CONFLICTS, 
            #TODO make sure all prior sents are closest to current sentn and not others in sentnums!
            relations = handle_single_match_near_sentences(sentn,subtype,ent_to_global, prior_sents, global_index_val, loc_index, relations, debug)                                 
            
        
                        
            
    if debug:
        print "\nNow add relationships from Next Sentences:"  
        
    if len(sentnums) == 1:
        subtype = "post"
        relations = handle_single_match_near_sentences(sentn,subtype,ent_to_global, next_sents, global_index_val, loc_index, relations, debug)
    else:
        print "BIG OLE FAIL, more than one direct sentence match"   #TODO HANDLE MULTIPLE SIMILARLY
       
        
        
    if debug:
        print "\nNow add relationships from Rest of Sentences:"    
           
    if len(sentnums) == 1:
        rest = prior_far_sents + next_far_sents
        relations = handle_single_match_far_sentences(ent_to_global, rest, global_index_val, loc_index, relations, debug)                                                   
    else:
        print "BIG OLE FAIL, more than one direct sentence match"  #TODO HANDLE MULTIPLE SIMILARLY
        
        
    if debug:    
        print "MADE THE FOLLOWING RELATIONS:"
        for rel in relations:
            print "\n"
            print rel
            
    res = {'url':url, 'entities': ent, 'relations': relations, 'date': art['_source']['date']}
    global_relations[url] = res
    return res


# In[994]:

import time
#GLOBAL VARS
global_entities = []
global_relations = {}
article_relations = {}
global_index = {}


#get list of legislators (from mongodb)
q = {'entity_type':'politician'}
pols = get_entities(q,db)
#print pols.count()

#populate global entities locally
if len(global_entities) == 0:
    for p in pols:
        global_entities.append(p)
    #print len(global_entities)

#make starting global index
for i, j in enumerate(global_entities):
    global_index[j['full_name']] = i
    
    
i = 0
#have to re-get info
pols = get_entities(q,db)

#for each legislator
start = time.clock()
for cur_leg in pols:
    if i < 3 or i > 3:
        i = i + 1
        continue
    i = i + 1
    #print cur_leg
    
    #get party info, position, full name and make query from those
    #q = generate_pol_query(cur_leg)  #q[0] is query, and q[1] is fullname    
    q = ["Democrat Rep","Garnet Coleman"]
    print "***Currently on "+q[0]+" " + q[1]+"\n"
    
    #run query on elastic search, and if no results try simplified query ( just full name)
    results = run_pol_elastic_query(q)
    if len(results['hits']['hits']) == 0:
        print "No results found for "+fullname+" so proceed to next legislator\n"
        continue
    
    print("found "+str(len(results['hits']['hits']))+" results.  Now inspecting article results: ")
    
    a = 0
    poli_found = 0
    #for each article result
    for art in results['hits']['hits']:
        #if a > len(results['hits']['hits']):
        if a > 5:   #to start at another result, change 0 to result -1 
            a = a + 1
            #break
            continue
        a = a + 1
        debug = True
        if debug:
            print "****"+str(a)+"*****************************************************************************************************"
            print "\nLooking at-- id: "+art['_id']+", score: "+str(art['_score']) +", "+art['_source']['date']+"\n"+art['_source']['url']
        #else:
        #    print str(a)
        debug = False
        
        #search if full name is in article
        if art['_id'] == '492537':
            if debug:
                print "!!*!*!*!**!!*!*!*"
            art["_source"]["body"] = "Texas Rehabilitation Commissioner Vernon Arrell told a state House committee today that his agency is working with the federal government to improve the way it processes applications from sick or injured people seeking Social Security disability insurance payments.\n" + art['_source']['body']

        if entity_in_article(art,q,debug) == False:
            #TODO: if not, check for last name and party/position… if that is not present, skip this article ( false positive )              
            ent_found = 0            
            #IF NONE FOUND, make sure article text is same as that from url
            if "_source" in art:
                if "body" in art["_source"]:                    
                    name = q[1]
                    if art["_source"]["body"].find(q[1].upper()) > -1:
                        ent_found = 1
                        art["_source"]["body"] = art["_source"]["body"].replace(q[1].upper(),name)
                    else:
                        if art["_source"]["body"].find(q[1].lower()) > -1:
                            ent_found = 1
                            art["_source"]["body"] = art["_source"]["body"].replace(q[1].lower(),name)    
                       
            if ent_found == 0:
                if debug:
                    print("\tZZZZZZZZZZ No hit found in article\n")
                    print art["_source"]["body"]
                continue
            else:
                if debug:
                    print "Exact hit not found for "+q[1]+", but allcaps or all lower version was found so we changed it"
                    print art["_source"]["body"]
        
        #TODO look into coreference resolution (CRR) via nltk or see how Padro’s does 
        #( that will take way way way too long though unless we have the code, and its not open source )
        
        #regardless of CRR, get sentences of articles ( via approach 5 in texas-elasticsearch-and-entity-detection.ipynb ) 
        if debug:
            print "ARTICLE TEXT: "
            print art
        sentences = get_article_sentences(art)
        
        if debug:
            print "\t--Found "+str(len(sentences))+" sentences"
        
        
        #get list of entities found in article via MITIE
        #tokens, entities = get_named_entities(sentences)  #treating text as one piece
        entities = get_named_entities_per_sentence(sentences,debug) #instead try by sentence

        #before continuing make sure that full name of politician is a found entity (to avoid Jeffry Scott Sanford case)
        if verify_entity_found(entities,q[1]) == False:
            if debug:
                print "\t\t"+q[1]+" not found in entities list for article so skip!"
            continue
        
        poli_found = poli_found + 1
        
        #disambiguate entity list ( i.e., Rick Perry = Gov Perry = Perry (depending on context) )         
        #as much as possible and create dictionary of who goes to who..
        #check to see who if any (and which aren’t locations) exists in entity db
        #return json with keys for each entity, along with aliases for each and db info if any
        
        
        #if a == 189:
        #    debug = True
            
        if debug:
            print "\t\tNow Disambiguate"            
        dis_entities = disambiguate_entities(entities,sentences,db,debug) #debug
            
            
        if debug:
            print "!!HERE IS THE LIST OF DISAMBIGUATED ENTITIES"
            print sentences
            for d in dis_entities:
                print d 
                for de in dis_entities[d]:
                    print "\t"+de+" : "+ str(dis_entities[d][de])
        

        #for each time we find match of full name or a variant of it as determined by disambiguation step 
            #( THIS STEP IS HARD AND IMPORTANT)
            #1) do entity recognition (via MITIE) of the sentence on which the match was found 
                    #( for entities found, this fullname-entity relation gets three points, 
                    #  which gets set in a  local variable dictionary ( politician-entity-location in page )
                    
                    #before we give points to the relation, we need to make sure that this particular entity 
                    #in the sentence hasn’t already been given points for its own)
                    #i.e., no double counting of the same entity-relation in a sentence 

            #2) do entity recognition for sentences in paragraph above and below 
            # ( or some variant here .. this will be determined by how well we can disambiguate and coreference things)

        #PART 2  
           #then once done with the original politician for article, 
           #for all entities which aren’t locations, check to see if they exist in entity db, and if so do above process                    
        if debug:# or a==4:
            debug = True
            print "YYYYYY NOW NOW get relations!"
            #print sentences
        
              
        relations = get_relations(q[1], entities,dis_entities,sentences,db,debug)

        if a == -1:
            debug = True
            print "Sentences:"
            for szi,sz in enumerate(sentences):
                print str(szi) +": " + sz
            print "\nRelations:"
            print relations
            print "\nEntities"
            print entities
            print "\nDis_entities"
            print dis_entities
            
        if debug or a==4:
            debug = True
            print "----------------------------------------------------------------------------------------"
            print "XXXXXX VERIFY/CHECK IF ENTITIES EXIST IN DB and save.. for now just to local BIG list maybe?"
            #print "\nRelations"
            #print relations

        res = verify_and_save_relations(q,relations,dis_entities,sentences,art,db,debug)
        
        #TODO DO THIS FOR OTHER PERSONS/ORGANIZATIONS IN LIST

        debug = False
        if debug or a <= 4:
            print "RESULTS FOR URL:"   
            print " ".join(sentences)
            print "\nMADE THE FOLLOWING RELATIONS:"
            for rel in res['relations']:                
                print "\t"+rel['term1'] + '('+str(rel['term1_id'])+') -- ' +                       rel['term2'] + '('+str(rel['term2_id'])+') of type: '+rel['type']
            print "\nDis Entities"
            print dis_entities

            
        #FUTURE TODO

end = time.clock()
elapsed = end - start
print "**************************************"
print "Elapsed Time: "+str(elapsed)+" seconds"
print "**************************************"

#TODO NOW TAKE THESE RESULTS AND CONVERT TO (term1id,term2id) pair key based thing for viz


# In[564]:

#1. TODO add interarticle links that aren't the primary politican centric (eventually do full)
#2. TODO: ADD ABILITY TO HANDLE MULTIPLE DIRECT HITS ( MOST IMPORTANT)  see a = 4
#  ( SEE GET_RELATIONS, JUST NEED TO BE CLEVER ABOUT MERGING EITHER IN THAT FUNCTION
#    OR IN VERIFY WHEN ADDING RELATIONS, NEED TO INCLUDE ENT_ID TO DIFFERENTIATE or for second only worry about direct hits maybe? )
#3. Get One or two more sources (texas tribune, dallas morning news)
#4. TODO ADD KEYWORDS/FREQUENCY STUFF (IMPORTANT)
#5. TODO ADD MANNER IN WHICH TO GET FEDERAL TEXAS REPS INFO SENATORS/REPS, ALONG WITH OTHER IMPORTANT OFFICES! (VERY IMPORTANT)


#TODO: MAYBE LOOK INTO TITLES AFTER WORD (where as now we only do prior)
#TODO USING WIKIPEDIA TO FIND ALIASES/VERIFY ENTITIES
#TODO AFTER INITIAL SEARCH, LOOK FOR ANY UPPERCASE WORDS NOT INCLUDED IN THE MIX AND DECIDE WHAT THEY ARE. (IMPORTANT-ish)
#TODO DON'T ALLOW PERSONS WITH ONE NAME TO GET ADDED TO GLOBAL LIST ( see, janet.)
#TODO WEIGH IMPORTANCE OF REFERENCES IN A GIVEN ARTICLE BY TOTAL NUMBER OF REFERENCES OVERALL (see a=27, candidate list!!)
#TODO: MAKE SIMPLE TOOL TO JOIN ENTITIES FROM GLOBAL RELATIONS DB WHICH ARE ACTUALLY THE SAME ( that propogates)

#TODO: pre-assess if any pairs of words are in all caps, and then make them just normal capitalized 
#     ( case a = 128, SEN. JUAN "CHUY" HINOJOSA, D-McALLEN ... finds D-McALLEN as person).. maybe just change this thing
#TODO: check if an article doesn't have same info as its webpage!!
#TODO: add district name/city to politicians at beginning for help in verifying things, and county
#TODO: add committees, http://sunlightlabs.github.io/openstates-api/committees.html#committee-fields
#TODO: add finance contributions stuff
#TODO cases:
    #Houston Democrat Representative Garnet Coleman ( gets rep, but not democrat or houston) <--
    #ORG NOT FOUND:   Pro-Choice Texas Foundation-NARAL
    #Representative Inocente "Chente" Quintanilla , treated as MISC: Inocente , MISC: Chente, PERSON: Quintanilla
    #Harris County Attorney 's Office <-- watch for extra space
    #for a=16, Lieutenant Governor Bill Ratliff and House Speaker Pete Laney ( make sure this works)
    #fixed error at 189, AAAAAA: Looking if word after to LOCATION AUSTIN U.S. is in CAPS and part of an ORGANIZATION NAME
        #[u'AUSTIN', u'\u2014', u'U.S.']
        #check is U.S.
        #if ps[i+1].replace(":","").replace(",","") != t.split()[1]:
        #list index out of range
    # error at ****155***id: 645659, 2012-10-14
        #http://www.chron.com/news/houston-texas/article/Cancer-agency-faces-challenges-in-months-ahead-3945706.php
        #ZZZZZZZZZZ No hit found in article    
        #State Rep. Garnet  Coleman   (DOUBLE SPACE SCREWED US so remove from doc and try again)
    # error at ****480***id: 6568312013-02-22
        #http://www.chron.com/opinion/editorials/article/Is-there-really-a-Houston-delegation-in-the-Texas-4301557.php
        #ZZZZZZZZZZ No hit found in article
        #6. Garnet  Coleman, D .. same exact DOUBLE SPACE ISSUE!
    

#XXX: get districts json
   #http://openstates.org/api/v1/districts/tx/?apikey=744e7bf0a08748e69f06d690d8aa197c
#XXX: get counties json
   #http://jasonweaver.name/lab/texascounties/



#FOR HOUSTON CHRONICLE, if link says Legislature-highlights, don't include "same article" catches

#for Garnet Coleman
#for 771 results, we process it in 32.717454 seconds
#GLOBAL INDEX with 7172 entities
#GLOBAL RELATIONS with 767 articles and Total Relations of 22913


# In[901]:

#print "GLOBAL ENTITIES"
#for ge in global_entities:
#    print ge['full_name']
print "\nGLOBAL INDEX"
print str(len(global_index)) + " entities"
print "\nGLOBAL RELATIONS" 
print str(len(global_relations)) + " articles"
total = 0
for gr in global_relations:
    total = total + len(global_relations[gr]['relations'])
    if total < 100:
        print global_relations[gr]['relations']
    
#    print "\n"+gr
#    for rr in global_relations[gr]['relations']:
#        print rr
print "\nTotal Relations"
print str(total)


# In[939]:

from elasticsearch import Elasticsearch
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from math import log


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

example = ['Diego is in favor of drug legalization', 'Diego said: "Medical Marijuana is a right', 'We believe that drug legalization could lead to the use of medical marijuana',
           'Diego is in favor of drug legalization', 'Diego said: "Medical Marijuana is a right', 'We believe that drug legalization could lead to the use of medical marijuana']

print get_keywords(example)


# In[302]:

#tokenizer problem sentences
#s1 = "AUSTIN — The Texas House on Tuesday stuck a fork in the state lottery commission then resuscitated the agency hours later, realizing that dissolving it would create an unwieldy budget gap for schools and charities that depend on their piece of the pie."
#a = tokenize(s1)

#a = tokenize(fix_text(s1))  #still doesn't work

#import string
#news1 = filter(lambda x: x in string.printable, s1)
#a = tokenize(news1)
#a
for c in cur_leg:
    print c + ": "+ str(cur_leg[c])


# In[352]:

for d in db.texnews.entities.find():
    if d["party"] == "Democratic":
        print d["full_name"] + " - " + d["party"]  + ", " + d['district']


# In[3]:

i = 1
name = data[i]["full_name"]
party = data[i]["party"]
pos = "Senator"
if data[i]["chamber"] == "lower":
    pos = "Representative Rep"


# In[152]:

#from get_entities import get_entities
from elasticsearch import Elasticsearch
es = Elasticsearch()

#results = es.search(index='texnews_english',q=query,size =1,explain=True)
#results = es.search(index='texnews_english',size=10000,q=query)

#http://bitquabit.com/post/having-fun-python-and-elasticsearch-part-3/
#results = es.search(index='texnews_english',size=10000, body={'query': {'bool': {'must': [ {'match': { 'text': query }}]}}})

#results = es.search(index='texnews_english',size=10000, body={'query': {'filtered': {'filter': {'term': { 'text': query }}}}})
#this returns 0.. might need to re-index things according to 
#http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/_finding_exact_values.html

#http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/match-multi-word.html
query = party + " " +pos + " " + name


query = "Republican Rep Scott Sanford"
name = "Scott Sanford"

print query
#results = es.search(index='texnews_english',size=10000, body={'query': {'match': {'text': {'query': query, 'operator':'and' }}}})
#origq = {'query':{"bool":{"disable_coord": True,"must": [ {'match_phrase': {'body': {'query': query, "minimum_should_match": "75%" }}}]}}}

origq = {"query":{"bool":{"disable_coord": True,"must": [{'match_phrase': {'body': {'query':name, 'analyzer':'analyzer_keywords' }}}],
                          "should":[{'match':{'body':{'query':'Republican Rep'}}}]}}}
results = es.search(index='texnews_english',size=10000, body=origq)
if len(results['hits']['hits']) == 0:    
    print "none found so new query: " + name
    #results = es.search(index='texnews_english',size=10000, body={'query': {'match': {'text': {'query': query, 'operator':'and' }}}})
    newq = {"query":{"bool":{"disable_coord": True,"must": [{'match_phrase':{'body':{'query':name,'analyzer':'analyzer_keywords'}}}]}}}
    results = es.search(index='texnews_english',size=10000, body=newq)

    
#"minimum_should_match": "75%"    
    
print len(results['hits']['hits'])


# In[154]:

#query = "Scott Sanford"
#query = "Penny Todd"
#results = es.search(index='texnews_spanish',size=10000, body={'query': {'bool': {'must': {'match': { 'body': query }}}}})
#results = es.search(index='texnews_spanish',size=10000, body={"query":{"bool":{"disable_coord": True,"must": [{'match_phrase':{'body':{'query':query,'analyzer':'analyzer_keywords'}}}]}}})

print len(results['hits']['hits'])
print results['hits']['hits'][0]


# In[158]:

ress = results['hits']['hits']
for x in ress:
    #print x
    if '_source' in x:
        r = x['_source']        
        start = 0
        if 'body' in r:
            loc = r['body'].find(query,start)
            if loc > -1:
                print "*** Full found: " + r['date'] + ", " + r['section'] + " ," + r['title'] + " ," + r['article-num']
                print "\t"+r['body'][loc-10:loc+len(query)]
            else:
                loc = r['body'].find(name,start)
                if loc > -1:
                    print "*** Name found at spot( "+str(loc)+" of "+str(len(r['body']))+" ): " + r['date'] + ", " + r['section'] + " ," + r['title'] + " ," + r['article-num']
                    #print "\t"+r['text'][loc-10:loc+len(query)]
                    #print r['text'][start:loc].split(" ")
                    temp = r['body']


# In[93]:

#https://github.com/LuminosoInsight/python-ftfy
#!easy_install ftfy


# In[7]:

ress = results['hits']['hits'][0:1]
r = ress[0]['_source']
start = 0
loc = r['text'].find(name,start)
#print "*** Name found at spot( "+str(loc)+" of "+str(len(r['text']))+" ): " + r['date'] + ", " + r['section'] + " ," + r['title'] + " ," + r['article-num']
print "*** Name found at spot( "+str(loc)+" of "+str(len(r['text']))+" ): " + r['url'] + " ," + r['article-num']

#approach1
#sentences = ress[0]['_source']['text'].split(".\n")   #gives 15 sentences while there are more

#approach2
#http://stackoverflow.com/questions/25735644/python-regex-for-splitting-text-into-sentences-sentence-tokenizing
#import re
#sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', ress[0]['_source']['text'])  
#this approach is better than first and gives 37 sentences

#approach3
#http://stackoverflow.com/questions/9474395/how-to-break-up-a-paragraph-by-sentences-in-python
#from nltk import tokenize
#sentences = tokenize.sent_tokenize(ress[0]['_source']['text'])  
#gives 34 and is slower than second, but maybe we can include things to not tokenize for sentences (Lt. , Gov. , Rep.)

#approach4
#http://stackoverflow.com/questions/14095971/how-to-tweak-the-nltk-sentence-tokenizer
#from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
#punkt_param = PunktParameters()
#punkt_param.abbrev_types = set(['lt', 'gov', 'rep', 'mrs', 'mr', 'inc'])
#sentence_splitter = PunktSentenceTokenizer(punkt_param)
#text = ress[0]['_source']['text'].replace('?"', '? "').replace('!"', '! "').replace('."', '. "')
#sentences = sentence_splitter.tokenize(text)
#this is probably the best approach since you can send in specific abbreviations.
#however we need to fix weird quotes to normal quotes to get part of it to work as expected
#for that we look at ftfy above .. maybe we can incorporate that.

#approach 5 ( hopefully improved on approach4)
from __future__ import unicode_literals
from ftfy import fix_text
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
punkt_param = PunktParameters()
punkt_param.abbrev_types = set(['lt', 'gov', 'rep', 'mrs', 'mr', 'inc'])
sentence_splitter = PunktSentenceTokenizer(punkt_param)
text = fix_text(ress[0]['_source']['text']).replace('?"', '? "').replace('!"', '! "').replace('."', '. "')
sentences = sentence_splitter.tokenize(text)
#approach 5 WORKS THE BEST!!

c = 0
for s in sentences:
    print str(c) + ": "+ s 
    c = c + 1


# In[9]:

#*** Name found at spot( 1185 of 3963 ): 2009-04-02, news/falkenberg ,Lawmaker needs course in Medicaid 101 ,1735774
#prior_context = temp[start:loc+1].split(" ")[-20:-1]
#post_context = temp[loc:len(temp)-1].split(" ")[0:20]
#print " ".join(prior_context) + " " + " ".join(post_context)

#print temp[start:loc] #+ " " + post_context
#print "****"+temp[loc:(loc + len(name))]+"****" + temp[(loc+len(name)):]


# In[11]:

n = 0
for r in results['hits']['hits']: 
    if n < 80 and r["_score"] > .2:
        if query in r["_source"]["text"]:
            print "\n***found "+query+" with score: "+str(r["_score"]) + "\n" #+" in "+r["_source"]["text"] + "\n"
            text = ''.join([i if ord(i) < 128 else '' for i in r["_source"]["text"]])
            
            #before anything look for name in text  
            end = len(text)
            start = 0
            while start < end:
                loc = text.find(query,start)
                if loc == -1:
                    start = end
                    start = loc + len(query)
                else:
                    print "found at "+str(loc)+"\n"
                    print text[loc-10:loc+len(query)]
                    #print text[start:loc].rsplit(" ",1)[-1]
                
                
            #tokens = tokenize(text)
            #print tokens
            
            #entities = ner.extract_entities(tokens)
            
            #for e in entities:
                #range = e[0]
                #tag = e[1]
                #score = e[2]
                #score_text = "{:0.3f}".format(score)
                #entity_text = " ".join(tokens[i] for i in range)
                #print "\tScore: " + score_text + ": " + tag + ": " + entity_text
        n = n + 1        
print str(n)+" results found"





# In[132]:

#results['hits']['hits'][8217]

#results['hits']['hits'][8258]

#results['hits']['hits'][8319]

#results['hits']['hits'][357]


# In[363]:

#https://gist.github.com/troyane/c9355a3103ea08679baf
from nltk.tag.stanford import NERTagger
import nltk

nerpath = "/Users/dolano/htdocs/dama-larca/stanford-ner/stanford-ner-2015-01-30/"
st = NERTagger(nerpath+"classifiers/english.all.3class.distsim.crf.ser.gz", nerpath+'stanford-ner.jar')

#print st.tag('Gov. Rick Perry unexpectedly canceled plans to visit areas hit by a massive Central Texas wildfire.\nA Perry spokeswoman said the governor\'s scheduled visit on Saturday of damaged areas in Bastrop County near Austin, as well as his participation in a news conference with local and state officials, did not take place because of "logistical issues" with Perry arriving in Bastrop on time.\nPerry\'s office on Friday had announced the governor would visit the area.\nPerry spokeswoman Allison Castle said the governor was in Austin and was keeping in regular contact with officials on the wildfire.\nCastle did not say when Perry would return to Bastrop. Perry visited the area earlier this week after he cut short a presidential campaign trip to deal with the crisis.'.split())
tagged = st.tag('Gov. Rick Perry unexpectedly canceled plans to visit areas hit by a massive Central Texas wildfire.\nA Perry spokeswoman said the governor\'s scheduled visit on Saturday of damaged areas in Bastrop County near Austin, as well as his participation in a news conference with local and state officials, did not take place because of "logistical issues" with Perry arriving in Bastrop on time.\nPerry\'s office on Friday had announced the governor would visit the area.\nPerry spokeswoman Allison Castle said the governor was in Austin and was keeping in regular contact with officials on the wildfire.\nCastle did not say when Perry would return to Bastrop. Perry visited the area earlier this week after he cut short a presidential campaign trip to deal with the crisis.'.split())
#tagged1 = st.tag("With his Republican primary victory safely behind him, Texas Gov. Rick Perry is still working hard to court conservative voters.  Perry made a guest appearance Saturday night at an event in Tyler hosted by conservative radio and television talk-show host Glenn Beck.  Speculation is swirling that Perry may consider a run for president in 2012 and experts say appearing with Beck keeps the governor in the minds of conservative voters. Perry has denied he's considering a run.  Perry calls Beck a national leader with a powerful message about Washington and its out of control spending. Perry is running for a third term as governor. He faces former Houston Mayor Bill White, a Democrat, in November.".split())


# In[365]:

#nltk.download()
entities = nltk.chunk.ne_chunk(tagged)
tagged
#entities


# In[ ]:

#OR use java and call it
#http://stackoverflow.com/questions/18371092/stanford-named-entity-recognizer-ner-functionality-with-nltk
#java -mx1000m -cp stanford-ner.jar edu.stanford.nlp.ie.NERServer -loadClassifier classifiers/english.all.3class.distsim.crf.ser.gz -port 9191

#http://nlp.stanford.edu:8080/ner/process


# In[ ]:

#https://github.com/mit-nlp/MITIE
#comparable to Stanford - https://github.com/mit-nlp/MITIE/wiki/Evaluation
Diegos-MacBook-Pro:python dolano$ python ner.py 
loading NER model...

Tags output by this NER model: ['PERSON', 'LOCATION', 'ORGANIZATION', 'MISC']
Tokenized input: ['Gov', '.', 'Rick', 'Perry', 'unexpectedly', 'canceled', 'plans', 'to', 'visit', 'areas', 'hit', 'by', 'a', 'massive', 'Central', 'Texas', 'wildfire', '.', 'A', 'Perry', 'spokeswoman', 'said', 'the', 'governor', "'s", 'scheduled', 'visit', 'on', 'Saturday', 'of', 'damaged', 'areas', 'in', 'Bastrop', 'County', 'near', 'Austin', ',', 'as', 'well', 'as', 'his', 'participation', 'in', 'a', 'news', 'conference', 'with', 'local', 'and', 'state', 'officials', ',', 'did', 'not', 'take', 'place', 'because', 'of', '"', 'logistical', 'issues', '"', 'with', 'Perry', 'arriving', 'in', 'Bastrop', 'on', 'time', '.', 'Perry', "'s", 'office', 'on', 'Friday', 'had', 'announced', 'the', 'governor', 'would', 'visit', 'the', 'area', '.', 'Perry', 'spokeswoman', 'Allison', 'Castle', 'said', 'the', 'governor', 'was', 'in', 'Austin', 'and', 'was', 'keeping', 'in', 'regular', 'contact', 'with', 'officials', 'on', 'the', 'wildfire', '.', 'Castle', 'did', 'not', 'say', 'when', 'Perry', 'would', 'return', 'to', 'Bastrop', '.', 'Perry', 'visited', 'the', 'area', 'earlier', 'this', 'week', 'after', 'he', 'cut', 'short', 'a', 'presidential', 'campaign', 'trip', 'to', 'deal', 'with', 'the', 'crisis', '.']

Entities found: [(xrange(2, 4), 'PERSON', 1.4964058753217928), (xrange(14, 16), 'LOCATION', 0.6081528093396019), (xrange(19, 20), 'PERSON', 0.8578910868604561), (xrange(33, 35), 'LOCATION', 1.6928261371011268), (xrange(36, 37), 'LOCATION', 1.432602387519684), (xrange(64, 65), 'PERSON', 1.097299000266322), (xrange(67, 68), 'LOCATION', 1.1223108526168661), (xrange(71, 72), 'PERSON', 1.1581921796329224), (xrange(85, 86), 'PERSON', 0.9906898930002838), (xrange(87, 89), 'PERSON', 0.9442651334634773), (xrange(94, 95), 'LOCATION', 1.029676065451085), (xrange(112, 113), 'PERSON', 1.4203139855625926), (xrange(116, 117), 'LOCATION', 0.7508056193276653), (xrange(118, 119), 'PERSON', 1.3918731759656906)]

Number of entities detected: 14
   Score: 1.496: PERSON: Rick Perry
   Score: 0.608: LOCATION: Central Texas
   Score: 0.858: PERSON: Perry
   Score: 1.693: LOCATION: Bastrop County
   Score: 1.433: LOCATION: Austin
   Score: 1.097: PERSON: Perry
   Score: 1.122: LOCATION: Bastrop
   Score: 1.158: PERSON: Perry
   Score: 0.991: PERSON: Perry
   Score: 0.944: PERSON: Allison Castle
   Score: 1.030: LOCATION: Austin
   Score: 1.420: PERSON: Perry
   Score: 0.751: LOCATION: Bastrop
   Score: 1.392: PERSON: Perry


# In[31]:

import sys, os
mitiepath = "/Users/dolano/htdocs/dama-larca/mitie/MITIE-master/"
sys.path.append(mitiepath+"mitielib")

from mitie import *
from collections import defaultdict

ner = named_entity_extractor(mitiepath+'MITIE-models/english/ner_model.dat')
#tokens = tokenize(load_entire_file('../../sample_text.txt'))
tokens = tokenize("With his Republican primary victory safely behind him, Texas Gov. Rick Perry is still working hard to court conservative voters.  Perry made a guest appearance Saturday night at an event in Tyler hosted by conservative radio and television talk-show host Glenn Beck.  Speculation is swirling that Perry may consider a run for president in 2012 and experts say appearing with Beck keeps the governor in the minds of conservative voters. Perry has denied he's considering a run.  Perry calls Beck a national leader with a powerful message about Washington and its out of control spending. Perry is running for a third term as governor. He faces former Houston Mayor Bill White, a Democrat, in November.")
entities = ner.extract_entities(tokens)

for e in entities:
    range = e[0]
    tag = e[1]
    score = e[2]
    score_text = "{:0.3f}".format(score)
    entity_text = " ".join(tokens[i] for i in range)
    print "   Score: " + score_text + ": " + tag + ": " + entity_text


# In[ ]:

# Now let's run one of MITIE's binary relation detectors.  MITIE comes with a
# bunch of different types of relation detector and includes tools allowing you
# to train new detectors.  However, here we simply use one, the "person born in place" relation detector.
rel_detector = binary_relation_detector(mitiepath+"MITIE-models/english/binary_relations/rel_classifier_people.person.place_of_birth.svm")

# First, let's make a list of neighboring entities.  Once we have this list we
# will ask the relation detector if any of these entity pairs is an example of the "person born in place" relation.
neighboring_entities = [(entities[i][0], entities[i+1][0]) for i in xrange(len(entities)-1)]

# Also swap the entities and add those in as well.  We do this because "person
# born in place" mentions can appear in the text in as "place is birthplace of person".  
#So we must consider both possible orderings of the arguments.
neighboring_entities += [(r,l) for (l,r) in neighboring_entities]

# Now that we have our list, let's check each entity pair and see which one the detector selects.
for person, place in neighboring_entities:
    # Detection has two steps in MITIE. 
    #   First, you convert a pair of entities into a special representation.
    rel = ner.extract_binary_relation(tokens, person, place)
    #   Then you ask the detector to classify that pair of entities.  
    #      If the score value is > 0 then it is saying that it has found a relation.  
    #      The larger the score the more confident it is.  
    
    # Finally, the reason we do detection in two parts is so you can reuse the intermediate rel in many
    # calls to different relation detectors without needing to redo the processing done in extract_binary_relation().
    score = rel_detector(rel)
    # Print out any matching relations.
    if (score > 0):
        person_text     = " ".join(tokens[i] for i in person)
        birthplace_text = " ".join(tokens[i] for i in place)
        print person_text, "BORN_IN", birthplace_text

# The code above shows the basic details of MITIE's relation detection API.
# However, it is important to note that real world data is noisy any confusing.
# Not all detected relations will be correct.  Therefore, it's important to
# aggregate many relation detections together to get the best signal out of
# your data.  A good way to do this is to pick an entity you are in interested
# in (e.g. Benjamin Franklin) and then find all the relations that mention him
# and order them by most frequent to least frequent.  We show how to do this in
# the code below.
query = "Benjamin Franklin"
hits = defaultdict(int)

for person, place in neighboring_entities:
    rel = ner.extract_binary_relation(tokens, person, place)
    score = rel_detector(rel)
    if (score > 0):
        person_text     = " ".join(tokens[i] for i in person)
        birthplace_text = " ".join(tokens[i] for i in place)
        if (person_text == query):
            hits[birthplace_text] += 1

print "\nTop most common relations:"
for place, count in sorted(hits.iteritems(), key=lambda x:x[1], reverse=True):
    print count, "relations claiming", query, "was born in", place


# In[ ]:

Diegos-MacBook-Pro:MITIE-master dolano$ cd MITIE-models/english/binary_relations/

rel_classifier_book.written_work.author.svm
rel_classifier_film.film.directed_by.svm
rel_classifier_influence.influence_node.influenced_by.svm
rel_classifier_law.inventor.inventions.svm
rel_classifier_location.location.contains.svm
rel_classifier_location.location.nearby_airports.svm
rel_classifier_location.location.partially_contains.svm
rel_classifier_organization.organization.place_founded.svm
rel_classifier_organization.organization_founder.organizations_founded.svm
rel_classifier_organization.organization_scope.organizations_with_this_scope.svm
rel_classifier_people.deceased_person.place_of_death.svm
rel_classifier_people.ethnicity.geographic_distribution.svm
rel_classifier_people.person.ethnicity.svm
rel_classifier_people.person.nationality.svm
rel_classifier_people.person.parents.svm
rel_classifier_people.person.place_of_birth.svm
rel_classifier_people.person.religion.svm
rel_classifier_people.place_of_interment.interred_here.svm
rel_classifier_time.event.includes_event.svm
rel_classifier_time.event.locations.svm
rel_classifier_time.event.people_involved.svm


# In[ ]:

#http://nbviewer.ipython.org/github/charlieg/A-Smattering-of-NLP-in-Python/blob/master/A%20Smattering%20of%20NLP%20in%20Python.ipynb


# In[ ]:

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


# In[199]:

#Coreference resolution 
#https://groups.google.com/forum/#!topic/nltk-users/g1MsgI2PxXU

#https://code.google.com/p/nltk-drt/

get_ipython().system(u'easy_install linearlogic')

