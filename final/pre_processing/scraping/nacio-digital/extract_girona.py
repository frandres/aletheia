from bs4 import BeautifulSoup
import requests
import unicodedata
import sys
import re
import datetime
import time
failed_articles = []

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def get_url_soup(url,items_present,max_tries=100):
    try_again = True
    tries = 0
    while try_again and tries<max_tries:
        tries+=1
        if tries%50==0:
            time.sleep(30)
        try:
            try_again = False
            print ' Trying'
            page = requests.get(url,verify=False,timeout=10)
            print ' Fetched'
            soup = BeautifulSoup(page.content)
            if 'licitat no existeix' in soup.text: # The page explicitly said its unavailable.
                return None
            for x in items_present:
                try_again = try_again or soup.find(**x) is None
        except Exception:
            try_again = True
    
    if not try_again:    
        print ' Voila' 
        return BeautifulSoup(page.content)
    else:
        print 'Ooops'
        print url
        failed_articles.append(url)
        return None

def process_news_url(url,folder,date):

    print url

    soup = get_url_soup(url,[{'name':'div', 'attrs':{ "id" : "seccio" }}])
    if soup is None:
        return None

    soup = soup.find('div',{"id":"seccio"})

    title = ''
    if soup.find('h2') is not None:
        title = strip_accents(soup.find('h2').text)
    subtitle = ''
    if soup.find('h3') is not None:
        subtitle = strip_accents(soup.find('h3').text)
    
    title_name = title.encode('utf8')
    title_name = title_name.replace('/','')
    title_name = '-'.join(title_name.split(' ')[0:10])

    #date_div = soup.find('span',{'id':'txtactualitzatel'})

    match=re.search(r'Actualitzat el (\d+/\d+/\d+)',soup.text)
    if match is not None:
        date = match.group(1)

    (day,month,year)=tuple([str(int(x)) for x in date.split('/')])

    content_soup = soup.find('div',{'class':'textnoticia'})
    if content_soup is None:
        content_soup = soup.find('div',{'id':'textnoticia'})

    cleaned_paragraphs = []

    if content_soup is not None:
        content = str(content_soup).replace('\n','')
        content = content.replace('\r','')

        content_no_nl = BeautifulSoup('\||| '.join([x.strip() for x in content.split('<br/><br/>')]))
        paragraphs = content_no_nl.text.split('\|||')

        if len(paragraphs)>0:
            cleaned_paragraphs = [strip_accents(x) for x in paragraphs[0:len(paragraphs)]]

    if len(cleaned_paragraphs)==0:
        failed_articles.append(url)
        return date
        
    text = '\n'.join([title,subtitle,date]+cleaned_paragraphs)

    with open (folder+'/'.join([year,month,day])+'/'+'-'.join([day,month,year])+'_'+title_name+'.txt','w') as f:
        f.write(text.encode('utf8'))
    return date

def process_news_div(soup,section_number):
    urls =[]
    for div in soup.find_all('div',{'class':'noticia categoria'+section_number}):
        if div.find('a').get('href') is not None:
            urls.append(div.find('a').get('href'))
    return urls

def process_index_page(folder,url,section_name,section_number):
    print url
    news_url = []
    
    soup = get_url_soup(url,[{'name':'div', 'attrs':{ "id" : "seccio" }}])

    if soup is None:
        print url
        raise Exception('Null index page')

    if soup.find('div', { "id" : "seccio"}) is not None:
        news_url += process_news_div(soup,section_number)

    date = ''
    for url in news_url:
        date = process_news_url(url,folder+section_name+'/',date)

def main():

    number_pages = int(sys.argv[1])
    section_name = sys.argv[2]
    section_number = sys.argv[3]

    for i in range(1,number_pages):
        process_index_page('./girona/','http://www.naciodigital.cat/gironainfo/noticies/'+section_number+'/pagina'+str(i),section_name,section_number)

    print failed_articles
    print len(failed_articles)

main()

