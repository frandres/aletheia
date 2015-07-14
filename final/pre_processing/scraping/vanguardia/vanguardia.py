from config import get_folder, get_index_builder

from bs4 import BeautifulSoup
import requests
import unicodedata
import sys

failed_articles = []

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

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

def clean_paragraphs(paragraphs):
    phrases_to_remove = ['TEMAS RELACIONADOS','NOTICIAS RELACIONADAS','MAS INFORMACION']
    for p in phrases_to_remove:
        if p in paragraphs:
            paragraphs.remove(p)
    return paragraphs
    
def process_article_page(url):
    text = ''

    soup = get_url_soup(url,[{'name':'div','attrs':{'class': 'text'}}])
    if soup is not None:
        paragraphs = soup.find('div',{'class': 'text'}).find_all('p')
        cleaned_paragraphs = clean_paragraphs([strip_accents(x.get_text()) for x in paragraphs] )

        text = '\n'.join(cleaned_paragraphs)
    return text

def process_news_div(div,folder,section_name):

    (day,month,year) = tuple([str(int(x)) for x in div.find('p',{'class':'p2'}).get_text().encode('utf8').split('/')])
    url = div.find('a').get('href').encode('utf8')
    title = div.find('a').get_text()
    title = title.lower() 
    title = strip_accents(title)
    title = title.replace('/','')  

    title_name = title.encode('utf8') 
    title_name = '-'.join(title.split(' ')[0:10])

    text = title+'\n'+ process_article_page(url)
    with open(folder+'/'+'/'.join([year,month,day])+'/'+'-'.join([day,month,year])+'_'+section_name+'_'+title_name+'.txt','w')as f:
        f.write(text.encode('utf8'))

def process_index_page(folder,index_builder,section_name,initial_range,final_range):
    for i in range(initial_range,final_range):
        url = build_index_url(index_builder,i)
        print url 
        soup = get_url_soup(url,[{'name':'div', 'attrs':{ "class" : "colAB" }}])
        if soup is not None:

            news = soup.find("div", { "class" : "colAB" }).find('div', {'class' : 'group'})

            for div in news.findChildren(recursive=False):
                process_news_div(div,folder,section_name)

def build_index_url(index_builder,page_number):
    return str(page_number).join(index_builder)

def main():
    initial_range = int(sys.argv[1])
    final_range = int(sys.argv[2])
    section_name = sys.argv[3]
    
    folder = get_folder(section_name)
    index_builder = get_index_builder(section_name)

    process_index_page(folder,index_builder,section_name,initial_range,final_range)
    for x in failed_articles:
        print x

main()

