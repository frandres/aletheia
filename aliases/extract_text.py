import re
from nltk.tokenize import sent_tokenize

def extract_context(string,text):
    # Let's find all occurrences of pairs (id0<WHATEVER>id1)
    regexp = re.compile('(.*)((?:[A-Z]\w* .{0,5})*'+string+'(?:.{0,5} [A-Z]\w*)*)(.*)', re.DOTALL)

    match = re.search(regexp,text)
    
    pre_context = ''
    alias = '' 
    post_context = ''

    if match is not None:
        if match.group(1) is not None:
            pre_context = match.group(1).strip().lower()
        if match.group(2) is not None:
            alias = match.group(2).strip()
        if match.group(3) is not None:
            post_context = match.group(3).strip().lower()

    return (pre_context,alias,post_context)


def extract_all_contexts(string, text):
    # Segment the text into segments:
    segments= sent_tokenize(text)

    contexts = []
    # And extract the context for every chunk
    for segment in segments:
        contexts.append(extract_context(string,segment))

    return contexts

