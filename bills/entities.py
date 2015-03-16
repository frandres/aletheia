import sys, os
parent = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent + '/MITIE/mitielib')
from collections import defaultdict

from pyner import ner
from mitie import *
from string import punctuation

parent = os.path.dirname(os.path.realpath(__file__))
ner = named_entity_extractor(parent+'/MITIE/MITIE-models/spanish/ner_model.dat')
#TODO:
# FIX XRANGE.
# FIX NAMES.
# COMPLETE

def get_entities_mit(body):
    body = body.encode('utf-8')
    tokens = tokenize(body)
    entities = []
    for x in ner.extract_entities(tokens):
        entity = {}
        entity['name'] = " ".join(tokens[i] for i in x[0])
        entity['tag'] = x[1]
        entity['range'] = x[0]
        entities.append(entity)

    entities = clean_entities(entities)
    #merge_initials(entities,body)
    entities_dict = {}
    
    # Build the dictionary.
    for entity in entities:
        if entity['name'] == '':
            continue

        name = entity['name']
        if name not in entities_dict:

            entities_dict[name] = {}
            entities_dict[name]['name'] = name
            entities_dict[name]['freq'] = 1
            entities_dict[name]['aliases'] = [name]
            entities_dict[name]['tags'] = {entity['tag']:1}
        else:
            entities_dict[name]['freq']+=1

            if entity['tag'] in entities_dict[name]['tags']:
                entities_dict[name]['tags'][entity['tag']]+=1
            else:
                entities_dict[name]['tags'][entity['tag']]=1
            
    return entities_dict
'''
def merge_initials(entities,body):
    initials = []
    non_initials = []
    for ent in entities:
        if ent['name'].isupper():
            initials.append(ent)
        else:
            non_initials.append(ent)
    aliases= {}
    for initial_ent in initials:
        for whole_ent in non_initials:    
            print initial_ent['range']
            if abs(min(initial_ent['range'])-max(whole_ent['range'])<=2) or 
               abs(max(initial_ent['range'])-min(whole_ent['range'])<=2):
                #Initials and names very close, probably the same entity.
                aliases[initial_ent['name']] = whole_ent['name']
                entities.remove(initial_ent)

    return (entities,aliases)
'''
            
def clean_entities(entities):
    for ent in entities:
        name = ent['name']
        # Clean punctuation
        name = name.replace('.','')
        for punct in punctuation:
            name = name.replace(punct, ' ')
        # Remove double whitespces
        name = name.replace('   ',' ')
        name = name.replace('  ',' ')
        # And remove trailing spaces
        name = name.strip()
        ent['name'] = name
    return entities
        
def get_entities(body):
    return get_entities_mit(body)

def get_entities_standford(body):
    tagger = ner.SocketNER(host='localhost', port=9192)
    results = tagger.get_entities(body)
    entities = {}
    
    for ent_type in ['ORG','PERS','OTROS']:
        if ent_type in results:
            for entity in results[ent_type]:
                if entity in entities:
                    entities[entity]+=1
                else:
                    entities[entity]=1
    return entities

#print get_entities('La Casa es muy buena. La Casa de Panchou. I.C.V.. "La Casa de Panchou". La Casa de Panchou.')


