from bs4 import BeautifulSoup
import requests
import unicodedata
import re
import wget
import urllib
failed_articles = []

def get_url_soup(url,items_present,max_tries=100):
    try_again = True
    tries = 0
    while try_again and tries<max_tries:
        tries+=1
        try:
            try_again = False
            print ' Trying'
            page = requests.get(url,verify=False,timeout=10)
            print ' Fetched'
            soup = BeautifulSoup(page.content)
            for x in items_present:
                try_again = try_again or soup.find(**x) is None
        except Exception:
            try_again = True

    if not try_again:
        print ' Voila'
        return BeautifulSoup(page.content)
    else:
        print 'Ooops'
        failed_articles.append(url)
        return None

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn')


regexp = re.compile('.*?(Llei.*?),.*')

def process_url(url,folder):
    soup = get_url_soup(url,[{'name':'div', 'attrs':{'class':'llista_completa'}}])
    soup = soup.find('div',{'class':'llista_completa'})
    for d in soup.find_all('li',{'class':'word'}):
        for x in d.find_all('a',{'hreflang':'es'}):
            url = 'http://www.parlament.cat'+ x['href']
            name = regexp.findall(x['title'])[0]
            name = name.replace(' ','_')
            name = name.replace('/','-')
            name = folder+name+'.docx'
            urllib.urlretrieve (url, name)
            print url
            

def main():

    for i in range(1,33):
        process_url('http://www.parlament.cat/web/activitat-parlamentaria/lleis?p_pagina='+str(i),'./spanish/')

main()
