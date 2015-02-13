from bs4 import BeautifulSoup
import requests
import unicodedata
import sys
import json
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
                try_again = soup.find(**x) is None
        except Exception:
            try_again = True
    
    if not try_again:    
        print ' Voila' 
        return BeautifulSoup(page.content)
    else:
        print 'Ooops'
        failed_articles.append(url)
        return None

def process_url(url,path,count):
    soup = get_url_soup(url,[{'name':'div','attrs':{'class': 'article-body'}}])
    js = {}
    text = soup.find('div',{'class':'article-body'}).findAll('p')
    js['text'] = '\n'.join([x.text for x in text])
    js['date'] = soup.find('h5', class_ = 'timestamp')['title']
    if js["date"] != "":
        js["date"] = js["date"].split("T")[0]
    js['title'] = soup.find('h1', class_ = 'headline entry-title').text
    js["url"] = url;
    js["section"] = js["url"].split("http://www.chron.com/")[1].split("/article/")[0];
    js["status"] = "success";
    js["news-source"] = "Houston Chronicle";
    ps = js["url"].split(".php")[0].split('-');
    js["article-num"] = ps[len(ps) - 1];
    #print js

    with open(path+"/"+js["article-num"]+".json", 'w') as outfile:
        json.dump(js, outfile)
    
    return count + 1 

def main():
    urls = sys.argv[1]
    path = sys.argv[2]
    count = 0
    with open(urls,'r') as f:
        for line in f:
            line = line.strip()
            count = process_url(line,path,count)

main() 
