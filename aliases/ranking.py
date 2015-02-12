from extract_text import extract_all_contexts
from longest_subsequence import  get_longest_subsequence
from preprocess import preprocess_ids, preprocess_context,strip_html
from nltk import pos_tag

def is_useful_context(text):
    text = text.split(' ')
    poss = pos_tag(text)
    has_verb = False
    has_noun = False
    valid = True
    for i in range(0,len(poss)):
        pos = poss[i][1]
        if i+1< len(poss):
            next_pos = poss[i+1][1]
            valid = valid and (pos!='DT' or next_pos[0:2]=='NN')
            valid = valid and (pos[0]!='V' or next_pos[0:2]!='IN')
            valid = valid and (pos!='IN' or next_pos[0]!='V')
        has_verb = has_verb or pos[0] == 'V'
        has_noun = has_noun or pos[0:2] == 'NN'

    return has_verb or has_noun #and valid

# Given a list of counts of words, computes some relevats statistics and returns this in a string representation
def process_word_counts(word_counts):
#    return [' 'for counts in word_counts]
    return ['(' + str(min(counts))+' '+ str(max(counts))+')' for counts in word_counts]

# Returns true if string s1 contains all the words of s2 in their order
def str_contains(s1,s2):
    s1 = s1.split(' ')
    s2 = s2.split(' ')

    i = 0
    j = 0
    while i <len(s2):
        while j<len(s1) and s2[i]!=s1[j]:
            j+=1
        i+=1
        j+=1

    return j<=len(s1)
'''
    If every word of s2 is in s1, return the number of words that occur between every
    two consecutive words of s1 in s2.
    Otherwise, return None.
'''
def count_words_inbetween(s1,s2):
    s1 = s1.split(' ')
    s2 = s2.split(' ')

    s_count = [None]*(len(s2)+1)

    s2_i = 0
    s1_i = 0
    while(s1_i<len(s1) and s2[s2_i]!=s1[s1_i]):
        s1_i+=1

    '''
    if s1_i == len(s1) and (len(s2)>1 or s2[s2_i]!=s1[s1_i]):
        return None
    '''

    s_count[0] = s1_i

    s2_i+=1

    while(s2_i<len(s2) and s1_i<len(s1)):
        tmp = s1_i
        s1_i+=1
        while(s1_i<len(s1) and s2[s2_i]!=s1[s1_i]):
            s1_i+=1
        s_count[s2_i] = s1_i-tmp-1
        s2_i+=1

    if (s2_i<len(s2)): 
    # The previous while stopped without running through all the words of s2.
        return None

    if (s1_i==len(s1)):
    # The previous while stopped in the last word of s2 and that word doesnt match
    # a word in s1
        return None

    # Otherwise, they match.

    s_count[len(s2)] = len(s1)-s1_i-1

    return s_count

'''
    Given a list of contexts, processes them by extracting all the pairwise longest subsequences and keeping a count of the words between each word of the longest subsequence. Then filter out words with low frequency and that are not useful, build a sorted frequency table and filter out contexts which can be expressed with a higher frequency.

'''
def build_ranking(contexts,minimum_freq, minimum_size = 3):
    lss = {}
    for i in range(0,len(contexts)):
        for j in range(i,len(contexts)):
            t = get_longest_subsequence(contexts[i],contexts[j])
            if t is not None:
                words = t.split(' ')
                if len(words)>minimum_size:
                    if t in lss.keys():
                        lss[t]+=2
                    else: 
                        lss[t]= 2

    ''' Now we do two things:

        1) filter out contexts whose frequency are below are a certain threshold
        and that are not linguistically useful (contexts not containing content words
        and the such)

        2) for every possible context and longest subsequence, find if the longest subsequence
           matches that context and if so, count how many words are in between.
    '''
    sorted_text = []
    processed_contexts = {}
    for (lss_context,freq) in lss.items():
        if freq>=minimum_freq and is_useful_context(lss_context):
            real_freq = 0
            w= lss_context.split(' ')
            word_counts = [[] for x in range(0,len(w)+1)]
            for c in contexts:
                cw = count_words_inbetween(c,lss_context)
                if cw is not None:
                    real_freq+=1
                    for i in range(0,len(cw)):
                        count = cw[i]
                        word_counts[i].append(count)

            if real_freq> minimum_freq:
                sorted_text.append((real_freq,lss_context,word_counts))

    '''
        We now sort by frequency.
    '''
    sorted_text.sort(reverse= True)

    ''' Now we need to go through this list and filter our contexts which
        can be expressed by contexts with a higher frequency.
    '''
    filtered_sorted_text  = []
    for (freq,text,word_counts) in sorted_text:
        contained = False
        for (f_freq,f_text,f_word_counts) in filtered_sorted_text: 
            if str_contains(text,f_text):
                contained = True
                break
        if(not contained):
            filtered_sorted_text.append((freq,text,word_counts))


    ''' Now let's introduce the in-between counts between each of the contexts:'''
    flattened_filtered_sorted_text = [None] * len(filtered_sorted_text)

    for j in range(0,len(filtered_sorted_text)):
        freq = filtered_sorted_text[j][0]
        text = filtered_sorted_text[j][1]
        word_counts = filtered_sorted_text[j][2]

        words = text.split(' ')
        context =''
        processed_word_counts = process_word_counts(word_counts)
        for i in range(0,len(words)):
            context+=processed_word_counts[i]+words[i]
        context+=processed_word_counts[len(processed_word_counts)-1]
        flattened_filtered_sorted_text[j] = (freq,context)
    '''Et voila!'''
    return flattened_filtered_sorted_text



'''
    Given a list [(text,[id0,id1])] returns a ranking of the words
'''
def get_ranking(triplets, minimum_freq = 2,contexts=None):
    if contexts == None:
        contexts = []
        i = 0
        for (text,ids0,ids1) in triplets:
            i+=1
            #print 'Analyzing: ' + str(i)+ ', ' +ids0[0].encode('utf8')
        
            # Let's get rid of HTML:

            text = strip_html(text)

            # Let's now get all contexts and building a list with it.
            for t in extract_all_contexts(preprocess_ids(ids0),preprocess_ids(ids1),text,both_ways=True):
                t = preprocess_context(t)
                contexts.append(t)

        print 'Found: ' + str(len(contexts)) + ' base contexts.'
    else:
        for i in range(0,len(contexts)):
            contexts[i] = preprocess_context(contexts[i])

    sorted_text = build_ranking(contexts,minimum_freq)
    print "Found: " + str(len(sorted_text)) + ' contexts'
    print '-------------- RANKING ----------------'
    for i in range(0,min(100,len(sorted_text))):
        print str(i) + ' |' + sorted_text[i][1].encode('utf8') + '| with freq: '+ str(sorted_text[i][0])
        print ' '
