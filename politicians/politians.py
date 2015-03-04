import csv
import sys
import unicodedata

def strip_accents(s):
    if type(s) is not unicode:
        s = s.decode('utf-8')
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

political_parties = {'erc':['esquerra republicana','izquierda republicana','erc'],
                     'erc (cat-si)':['esquerra republicana','izquierda republicana','erc'],
                     'socialista (psc)':['socialista','psc'],
                     'ciu (cdc)':['ciu','cdc','convergencia i unio','convergencia democratica', 'convergencia y union'],
                     'ciu (cda-pna)':['ciu','cdc','convergencia i unio','convergencia democratica', 'convergencia y union'],
                     'ciu (udc)':['ciu','udc','convergencia i unio','union democratica', 'unio democratica'],
                     'icv-euia (icv)':['icv','catalunya verds', 'cataluna verde'],
                     'icv-euia (euia)':['euia','esquerra unida', 'izquierda unida'],
                     'c\'s':['ciutadans','ciudadanos'],
                     'C\'s (Independent)':['ciutadans','ciudadanos'],
                     'ppc':['partit popular','partido popular', 'pp'],
                     'mixt (cup)':['cup','unitat popular','unidad popular']}

def get_politicians_search_terms(f):
    search_terms = {}

    with open(f, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        next(reader) # skip header
        for row in reader:
            for i in range(0,len(row)):
                row[i]= strip_accents(row[i])

            keywords = []

            political_party = row[1].lower().strip()
            if political_party in political_parties:
                print political_parties[political_party]
                keywords = list(political_parties[political_party])

            stopwords = [' i', ' de']
            for x in stopwords:
                row[0] = row[0].replace(x,'')
            names = row[0].split(' ')
            for i in range(1,len(names)):
                keywords.append(names[0] + ' '+ names[i]) 
            
            print row[0]
            print ' '+'|'.join(keywords)    
def main():
    csv = sys.argv[1]
    get_politicians_search_terms(csv)

main()
