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


def process_news_url(url,folder,tentative_date):
    print url
    soup = get_url_soup(url,[{'name':'div', 'attrs':{ "class" : "columna_principal" }}])
    if soup is None:
        return None
    soup = soup.find('div',{"class":"columna_principal"})

    title = ''
    if soup.find('h1') is not None:
        title = strip_accents(soup.find('h1').text)
    subtitle = ''
    if soup.find('h2') is not None:
        subtitle = strip_accents(soup.find('h2').text)
    
    title_name = title.encode('utf8')
    title_name = title_name.replace('/','')
    title_name = '-'.join(title_name.split(' ')[0:10])

    (year,month,day)=tuple([str(int(x)) for x in list (tentative_date)])

    '''
    if soup.find('span',{'class':'fecha_hora'}) is not None:
        r= re.search(r'(\d+.\d+.\d+)',soup.find('span',{'class':'fecha_hora'}).text)
        if r is not None:# and r.group(1) is not None:
            (day,month,year) = tuple([str(int(x)) for x in r.group(1).split('.')])
    '''
   
    date = '/'.join([day,month,year])

    # Get the news text.
    
    cleaned_paragraphs = []
    if soup.find('div',{'class':'cuerpo_noticia'}) is not None:
        paragraphs = soup.find('div',{'class':'cuerpo_noticia'}).find_all('p')
        if len(paragraphs)==0:
            failed_articles.append(url)
            return None

        cleaned_paragraphs = [strip_accents(x.get_text()) for x in paragraphs[0:len(paragraphs)]]

    else:
        print soup
    if len(cleaned_paragraphs)==0:
        failed_articles.append(url)
        return None

    text = '\n'.join([title,subtitle,date]+cleaned_paragraphs)
    with open (folder+'/'.join([year,month,day])+'/'+'-'.join([day,month,year])+'_'+title_name+'.txt','w') as f:
        f.write(text.encode('utf8'))

def process_news_div(soup):
    urls =[]

    for div in soup.find_all('div',{ "class" : "article destacada estirar" }):
        if div.find('a') is not None and div.find('a').get('href') is not None:
            urls.append(div.find('a').get('href'))

    for div in soup.find_all('div',{ "class" : "article estirar" }):
        if div.find('a').get('href') is not None:
            urls.append(div.find('a').get('href'))
    return urls


def process_index_page(folder,date,section_name):
    (year,month,day) = tuple(date.split('/'))
    url = 'http://elpais.com/diario/'+'/'.join([year,month,day])+'/'+section_name+'/'
    print url
    news_url = []
    
    soup = get_url_soup(url,[{'name':'div', 'attrs':{ "class" : "secciones" }}])
    if soup is None:
        failed_articles.append(url)
        return None

    soup = soup.find('div',{ "class" : "secciones" })


    news_url += process_news_div(soup)

    for url in news_url:
        #print 'http://elpais.com/'+url
        process_news_url('http://elpais.com/'+url,folder+section_name+'/',(year,month,day))

def next_date(date):
    (year,month,day) = tuple([int(x) for x in date.split('/')])
    x = datetime.datetime(year,month,day)
    y = x+datetime.timedelta(days=1)
    year = str(y.year)
    month = str(y.month)
    day = str(y.day)

    if len(month)==1:
        month='0'+month
        
    if len(day)==1:
        day='0'+day
    return year+'/'+month+'/'+day

def date_before(date1,date2):
    (year,month,day) = tuple([int(x) for x in date1.split('/')])
    date1 = datetime.datetime(year,month,day)
    
    (year,month,day) = tuple([int(x) for x in date2.split('/')])
    date2 = datetime.datetime(year,month,day)
    
    return date1<=date2


def main():
   
    
    initial_date = sys.argv[1]
    final_date = sys.argv[2]
    section = sys.argv[3]

    while date_before(initial_date,final_date):
        print initial_date
        process_index_page('./',initial_date,section)
        initial_date = next_date(initial_date)

    print failed_articles
    print len(failed_articles)

main()

