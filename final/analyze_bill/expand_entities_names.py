import sys
from nltk.tokenize import sent_tokenize
from elasticsearch import Elasticsearch

from nltk.corpus import stopwords
from collections import defaultdict
from string import punctuation
punctuation = punctuation.replace('-','')

sys.setrecursionlimit(2000)

def camelize(string):
    if string.isupper() or len(string.split(' '))==0:
        return string

    to_upper_case = True
    new_string = ''
    for x in string:
        if to_upper_case:
            new_string+=x.upper()
        else:
            new_string+=x.lower()

        to_upper_case = x == ' '
    return new_string

def remove_punctuation(text):
    text = text.replace('.','')
    for punct in punctuation:
        text = text.replace(punct, ' ')
    return text
     
def clean_text(text):
    # Clean punctuation

    text = remove_punctuation(text)

    # Remove double whitespces
    text = text.replace('   ',' ')
    text = text.replace('  ',' ')
    # And remove trailing spaces
    text = text.strip()

    # Camelize.
    text = camelize(text)

    return text


def longest_common_substring(s1, s2):
    s1 = s1.split(' ')
    s2 = s2.split(' ')
    m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in xrange(1, 1 + len(s1)):
        for y in xrange(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    tokens = s1[x_longest - longest: x_longest]
    return ' '.join(tokens)

def get_longest_substrings_n(sentences, original,name,stopwords,min_freq=7):
    lcss = []

    # First we find LCSs between the extracted entity and it's context, and the extracted sentences from the articles.

    for sentence in sentences:
        lcs = longest_common_substring(sentence,original)
        lcss.append(lcs)

    # Now let's see what are the most repeated patterns
    lcss_ = []
    for i in range(0,len(lcss)):
        for j in range(i+1,len(lcss)): 
            lcs = longest_common_substring(lcss[i],lcss[j])
            if lcs != '' and lcs not in lcss_ and name in lcs and len(lcs)>len(name):
                lcss_.append(lcs)

    freq = defaultdict(lambda:0)

    # Let's filter stopwords and build a freq table.

    name_words = name.split(' ')
    first_word = name_words[0]
    last_word = name_words[len(name_words)-1]

    for lcs in lcss_:
        lcs = remove_punctuation(lcs)
        words = lcs.split(' ')
        # Verify that no stopwords were added.
        for i in range(0,3):
            if len(words)==0:
                break
            index = 0
            if words[index] != first_word and words[index].lower() in stopwords:
                words.pop(index)
        for i in range(0,3):
            if len(words)==0:
                break
            index = len(words)-1
            if words[index] != first_word and words[index].lower() in stopwords:
                words.pop(index)

        candidate = ' '.join(words)
        for sentence in sentences:
            if candidate in sentence:
                freq[candidate]+=1

    # Sort them by length and freq.

    ranking = [(len(x),y,x.strip()) for (x,y) in freq.items()]
    ranking.sort(reverse=True)

    for (_,y,string) in ranking:
        
        if y>=min_freq :
            return string
    return None


def get_candidate_entities(pre_context,name,post_context,ind):
    should_clause = [{'match_phrase': {'body': {'analyzer': 'analyzer_shingle', 'query': x}}} for x in [ pre_context, post_context] if len(x)>0]

    q = {'query': {'bool': {'disable_coord': True, 'must': [{'match_phrase': {'body': {'analyzer': 'analyzer_shingle', 'query': name}}}], 'should':  should_clause,}}}
    es = Elasticsearch()
    results = es.search(index=ind, body=q, search_type = 'dfs_query_then_fetch',size =10)['hits']['hits']
    articles = [x['_source']['body'] for x in results]
    candidate_entities = []
    for article in articles:
        sentences = sent_tokenize(article)
        for sentence in sentences:
            sentence = sentence.encode('utf8')
            sentence = clean_text(sentence)
            if name in sentence:
                candidate_entities.append(sentence)
    return candidate_entities

'''
    should = []
    for i in range(0,initial+2):
        # 3 grams
        should.append(tokens[i:i+3])

        # 3 grams
        should.append(tokens[i:i+3])
'''

    
def query_name(pre_context,name,post_context,index):
    pre_context = clean_text(pre_context)
    name = clean_text(name)
    post_context = clean_text(post_context)
    candidate_entities=get_candidate_entities(pre_context,name,post_context,index)
    sws = stopwords.words("spanish")
    sws.append('efe')
    sws.append('europa press')
    sws.append('-')

    longest = get_longest_substrings_n(candidate_entities, ' '.join([pre_context,name,post_context]),name,sws)
    if longest is not None and longest != name:
        return longest
    else:
        return None
    
