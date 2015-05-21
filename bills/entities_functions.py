
'''
Given an entity (E1) and a Mongo query (dict field->value) that returns a single entity E2 related to E1
merges E1 unto E2,
updates E2,
and optionally (parameter drop) drops E1 from the database.
'''
def merge_entities(e1,query,collection, drop= False):
    cursor = collection.find(query)
    if cursor.count() >1:
        raise Exception('Non unique entity')

    e2 = cursor[0]
    
    # Merge bills:

    if 'bills'in e2.keys():
        e2_bills = e2['bills']
    else:
        e2_bills = []

    if 'bills'in e1.keys():
        for bill in e1['bills']:
            if bill not in e2_bills:
                e2_bills.append(bill)

    # Update list of aliases

    if 'aliases' in e2.keys():
        e2_aliases = e2['aliases']
    else:
        e2_aliases = []

    if 'aliases'in e1.keys():
        for alias in e1['aliases']:
            if alias not in e2_aliases:
                e2_aliases.append(alias)
    
    # Update tags
    print e2
    if 'tags' in e2.keys():
        e2_tags = e2['tags']
    else:
        e2_tags = {}

    if 'tags'in e1.keys():
        for (tag,count) in e1['tags'].items():
            if tag in e2_tags:
                e2_tags[tag] += count
            else:
                e2_tags[tag] = count

    tags = [(y,x) for (x,y) in e2_tags.items()]
    tags.sort(reverse=True)
    tag = tags[0][1]

    collection.update(query,{'$set':{'bills':e2_bills,'aliases':e2_aliases,'tags':e2_tags,'tag':tag}})

    if drop:
        collection.remove({'name': e1['name']})

