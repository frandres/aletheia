#!/usr/bin/python3

# -*- coding: utf-8 -*-

"""
Shows how to control GoogleScraper programmatically. Uses selenium mode.
"""

import re
from GoogleScraper import scrape_with_config, GoogleSearchError
from GoogleScraper.database import ScraperSearch, SERP, Link, get_session

from os import linesep

def getCount(phrase):
    phrase = phrase.replace('.','')
    m = re.search('.*?(\d*) resul.*', phrase)
    if m is None:
        print(phrase)
    return int(m.group(1))

def query(e1,e2,prox=20):
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

def generate_query_file(pairs):
    with open('queries.txt','wt') as f:
        f.writelines(linesep.join([query(x,y) for (x,y) in pairs]))

def ask_google(ent, entities):
    pairs = [(ent,x) for x in entities]
    generate_query_file(pairs)
    
    config = {
    'SCRAPING': {
            'use_own_ip': 'True',
#        'keywords': 'prueba',
           'keyword_file': 'queries.txt',
            'search_engines': 'google',
#       'num_results_per_page': '15',
#       'number_of_pages': '10'
            'num_workers': 4,
        },
        'SELENIUM': {
            'sel_browser': 'chrome',
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
    except GoogleSearchError as e:
        print(e)

    count = {}
    for (p,tp) in pairs:
        q = session.query(SERP).filter(Link.serp_id == SERP.id).filter(SERP.query==query(p,tp))
        if q.count()>0:
            count[tp] = getCount(q[0].num_results_for_query)
        else:
            count[tp] = 0
    return count


