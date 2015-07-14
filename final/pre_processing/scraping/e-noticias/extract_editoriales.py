from bs4 import BeautifulSoup
import requests
import unicodedata
import sys
import re
import datetime
import time
failed_articles = []

def strip_accents(s):
   s = s.strip()
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
        except Exception as e:
            try_again = True
    
    if not try_again:    
        print ' Voila' 
        return BeautifulSoup(page.content)
    else:
        print 'Ooops'
        print url
        failed_articles.append(url)
        return None

month_string_to_month={
    'Gener':'1',
    'Febrer':'2',
    'Mar':'3',
    'Abril':'4',
    'Maig':'5',
    'Juny':'6',
    'Juliol':'7',
    'Agost':'8',
    'Setembre':'9',
    'Octubre':'10',
    'Novembre':'11',
    'Desembre':'12',
}
def get_date(soup):
    day = None
    month = None
    year = None

    date_p = soup.find('p',{"class":"texto_fecha_cab"})
    if date_p is None:
        return None

    date = date_p.text
    date = date.replace(' ','')

    match=re.search(r'(\d+/\d+/\d+)',date)
    if match is None:
        return None

    date = match.group(1)
    (day,month,year) = tuple([str(int(x)) for x in date.split('/')])

    if len(year)==2:
        year = '20'+year


    if len(year)==1:
        year = '200'+year

    if day is None or month is None or year is None:
        print date

    return (year,month,day)
    
def process_news_url(url,folder,tentative_date):
    print url
    soup = get_url_soup(url,[{'name':'div', 'attrs':{ "id" : "bloque1" }},{'name':'div', 'attrs':{ "class" : "div_cuerpo" }}])
    if soup is None:
        return None

    title_p = soup.find('p',{"class":"noti_titular_noticia_princ"})

    title = ''
    if title_p is not None:
        title = strip_accents(title_p.text)


    subtitle_p = soup.find('p',{"class":"subtitular_noticia_interior"})
    subtitle = ''
    if subtitle_p is not None:
        subtitle = strip_accents(subtitle_p.text)
    
    title_name = title.encode('utf8')
    title_name = title_name.replace('/','')
    title_name = '-'.join(title_name.split(' ')[0:10])

    (year,month,day)= get_date(soup)
    print (year,month,day)
    if year is None or month is None or day is None:
        (year,month,day) = tentative_date
        year = str(int(tentative_date[0]))
        month = str(int(tentative_date[1]))
        day = str(int(tentative_date[2]))

    date = '/'.join([day,month,year])
    # The article is structured in several ways, so we use different rules

    paragraphs = soup.find_all('p',{"class":"texto_cuerpo2N"})
    if len(paragraphs)>0:
        cleaned_paragraphs = [strip_accents(x.get_text()) for x in paragraphs[0:len(paragraphs)]]

    if len(paragraphs) ==0:
        paragraphs = soup.find_all('p',{"class":"texto_cuerpo2"})
        if len(paragraphs)>0:
            cleaned_paragraphs = [strip_accents(x.get_text()) for x in paragraphs[0:len(paragraphs)]]

    if len(paragraphs) ==0:
        p = soup.find("span",{"id":"txt_cuerpo"})
        if not p is None:
            whole_p = str(p).replace('\r\n','')
            
            soup_no_nl = BeautifulSoup('\||| '.join([x.strip() for x in whole_p.split('<br/><br/>')]))
            paragraphs = soup_no_nl.text.split('\|||')
            if len(paragraphs)>0:
                cleaned_paragraphs = [strip_accents(x) for x in paragraphs[0:len(paragraphs)]]

    if len(paragraphs) ==0:
        p = soup.find('p',{'class':'textnot'})
        if not p is None:

            whole_p = str(p).replace('\r\n','')
            
            soup_no_nl = BeautifulSoup('\||| '.join([x.strip() for x in whole_p.split('<br/><br/>')]))
            paragraphs = soup_no_nl.text.split('\|||')

            if len(paragraphs)>0:
                cleaned_paragraphs = [strip_accents(x) for x in paragraphs[0:len(paragraphs)]]

    if len(paragraphs) ==0:
        failed_articles.append(url)

    text = '\n'.join([title,subtitle,date]+cleaned_paragraphs)
    print url
    #print folder+'/'.join([year,month,day])+'/'+'-'.join([day,month,year])+'_'+title_name+'.txt'
    with open (folder+'/'.join([year,month,day])+'/'+'-'.join([day,month,year])+'_'+title_name+'.txt','w') as f:
        f.write(text.encode('utf8'))

def process_news_div(soup):
    urls =[]
    for div in soup.find_all('div',{'class':'div_preg_list_int'}):
        if div.find('a').get('href') is not None:
            urls.append(div.find('a').get('href'))
    return urls

def process_index_page(folder,date,section_name):
    (year,month,day) = tuple(date.split('/'))
    url = 'http://opinio.e-noticies.cat/hemeroteca/'+'-'.join([year,month,day])+'/'+section_name+'/'

    print url
    news_url = []
    
    soup = get_url_soup(url,[{'name':'div', 'attrs':{ "class" : "div_cuerpo_big" }}])

    if soup is None:
        return None

    news_url += process_news_div(soup)

    for url in news_url:
        process_news_url('http://opinio.e-noticies.cat'+url,folder+section_name+'/',(year,month,day))

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

