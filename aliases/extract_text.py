import re
from nltk.tokenize import sent_tokenize

def extract_closest_context(regexp,string):
    match = re.search(regexp,string)
    if match:
        return match.group(1)
    else:
        raise('Closest context not found')

def extract_context(id0,id1,text,both_ways=False):
    # Let's find all occurrences of pairs (id0<WHATEVER>id1)
    f_regexp = re.compile(id0+'.*?'+id1, re.DOTALL)
    new_c = re.findall(f_regexp, text)
    # And make sure we use the smallest one
    c_regexp = re.compile('.*'+id0+'(.*)'+id1,re.DOTALL)
    l = [extract_closest_context(c_regexp,p) for p in new_c]    
    if both_ways:
        l = l +  extract_context(id1,id0,text)
    return l

def extract_all_contexts(ids0, ids1, text, both_ways = False):
    # Segment the text into sentences:
    sentences = sent_tokenize(text)

    # And extract the context for every sentence and pair <id0,id1>
    for sentence in sentences:
        for id0 in ids0:
            for id1 in ids1:
                try:
                    for x in extract_context(id0,id1,sentence,both_ways):
                        yield x
                except Exception:
                    print sentence, id0, id1










