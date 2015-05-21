#!/usr/bin/python3

# -*- coding: utf-8 -*-

"""
Shows how to control GoogleScraper programmatically. Uses selenium mode.
"""

import re
from GoogleScraper import scrape_with_config, GoogleSearchError
from GoogleScraper.database import ScraperSearch, SERP, Link, get_session
from math import floor
from os import linesep

def getCount(phrase):
    phrase = phrase.replace('.','')
    phrase = phrase.replace(',','')
    phrase = phrase.replace(' ','')
    phrase = phrase.replace(' ','')
    # = re.search('\w*(\d*).*?', phrase)
    m = re.search('[^\d]*(\d*).*?', phrase)

    if m is None or m.group(1) == '':
        m = re.search('^(\d*).*', phrase)
        if m is None or m.group(1) == '':
            print ('Ruskie?{}'.format(phrase))
            phrase = phrase.replace(' ','')
            m = re.search('.*?(\d*)$', phrase)
            if m is None:
                print ('No: {}'.format(phrase))
                return 0

    count = 0
    try:
        count = int(m.group(1))
    except Exception :
        print(phrase)
    print(phrase,count)
    return count

def query_individual(entity):
    return '"{}"'.format(entity['name'])

def query_pairs(e1,e2,prox=20):
    if e1['tag'] == 'ORGANIZATION':
        e1['google_search'] = '('+ ' OR '.join(['"'+x+'"' for x in e1['aliases']]) + ')'
    else:
        e1['google_search'] = '("'+ e1['name'] +'")'

    if e2['tag'] == 'ORGANIZATION':
        e2['google_search'] = '('+ ' OR '.join(['"'+x+'"' for x in e2['aliases']]) + ')'
    else:
        e2['google_search'] = '("'+ e2['name'] +'")'

    return e1['google_search'] + ' AND ' + e2['google_search'] 
#    return '"'+t1+'" AROUND('+str(prox)+') "'+t2+'"'
'''
with open('politicians.txt') as f:
    politicians = [x.strip() for x in f.readlines()]

with open('third_parties.txt') as f:
    third_parties = [x.strip() for x in f.readlines()]
'''

def generate_query_file(queries,filename):
    with open(filename,'wt') as f:
        f.writelines(linesep.join(queries))
    return filename
    
def ask_google_individual(entities):
    queries = []
    for entity in entities:
        queries.append((entity,query_individual(entity)))
    filename = 'queries_individual_entities.txt'

    return execute_queries(queries,filename)

def ask_google_pairs(ent, entities):
    queries = []
    for entity in entities:
        queries.append((entity,query_pairs(ent,entity)))
    filename = 'queries_{}.txt'.format(ent['name'])

    return execute_queries(queries,filename)

def execute_queries(queries, queries_filename):
    generate_query_file([y for (x,y) in queries], queries_filename)
    num_workers = int(floor((len(queries)/15))+1)
    num_workers = 16
    print('Numthreads:{}'.format(num_workers))
    config = {
    'SCRAPING': {
            'use_own_ip': 'True',
#        'keywords': 'prueba',
            'keyword_file': queries_filename,
            'search_engines': 'google',
#       'num_results_per_page': '15',
#       'number_of_pages': '10'
            'num_workers': num_workers,
        },
        'SELENIUM': {
            'sel_browser': 'firefox',
            'manual_captcha_solving': True,

        },
        'GLOBAL': {
            'do_caching': 'False',
#       'proxy_file': 'proxies.txt',
        }
    }

    Session = get_session(scoped=False)
    session = Session()
    try:
        sqlalchemy_session = scrape_with_config(config)
    except Exception as e:
        print(e)
    print ('Finished searching')

    count = []
    for (entity,query) in queries:
        q = session.query(SERP).filter(Link.serp_id == SERP.id).filter(SERP.query==query)
        if q.count()>0:
            if q[0].effective_query == '0':
                count.append((entity, getCount(q[0].num_results_for_query)))
            else:
                count.append((entity, 0))
        else:
            print ('{} null'.format(query))

    return count


