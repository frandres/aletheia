from pymongo import MongoClient

from bisect import bisect_left

from entities_functions import merge_entities
'''
Fetch all entities from the Database, 
compute the most frequent tag,
and set a field called 'tag' with that value.
'''
def set_main_tag(collection):
    
    for entity in collection.find():
        tags = [(y,x) for (x,y) in entity['tags'].items()]
        tags.sort(reverse=True)
        tag = tags[0][1]
        collection.update({'name':entity['name']},{'$set':{'tag':tag}})
        
'''
Fetch all locations from the Database,
fetch all entities and check if by camelizing the names we match non-location entities with locations
This solves the problem of locations like CATALUNYA, BARCELONA that are in uppercase and not recognize
by the system as a location.
'''
def normalize_locations(collection):
    locations = [camelize(entity['name']) for entity in collection.find({'tag':'LOCATION'})]
    locations.sort()

    for entity in collection.find():
        name = camelize(entity['name'])
        # If it is already camelized, it doesn't make sense to analyze it again.
        if name == entity['name']:
            continue 
        # Otherwise, check if by camelizing it we recognize one of the locations.
        i = bisect_left(locations,name)
        if i == len(locations) or locations[i] != name:
            continue
      
        # If it matches a location, merge it with the location.

        # Check if there is a camelized version in the database; otherwise update this entity:
        cursor = collection.find({'name':name})
        if cursor.count() >1:
            raise Exception('Non unique entity')

        print name
        if cursor.count() ==0 :
            
            print 'Updating'
            print entity
            print 'New name: '+ name
            collection.update({'name':entity['name']},{'$set':{'name':name}})
        else:
            print 'Merging'
            print entity
            merge_entities(entity,{'name':name},collection,drop=True)
        print ''

'''
Given an entity, return the number of times it occurs accross all bills in the database. 
'''
def get_entity_freq(db,entity):
    collection = db.entities_bills
    cursor = collection.find({'name':entity['name']})
    freq = 0
    for entity_bill in cursor:
        freq+= entity_bill['freq']
    return freq
'''
This function goes through the list of found entities and removes entities with very low frequency.
This is useful for noise reduction (ie removing mistaken entities)
'''
def remove_entities_with_low_frequency(db,min_freq=3):
    collection = db.entities
    i = 0
    for entity in collection.find():
        freq = get_entity_freq(db,entity)
        if freq<=min_freq:
            i+=1
            print entity['name']
           
            #collection.remove({'name': entity['name']})
    print i


def postprocess_entities():
    conn = MongoClient()
    db = conn.catalan_bills
    #set_main_tag(entities_db)
    #normalize_locations(entities_db)
    remove_entities_with_low_frequency(db)

def camelize(string):
    to_upper_case = True
    new_string = ''
    for x in string:
        if to_upper_case:
            new_string+=x.upper()
        else:
            new_string+=x.lower()

        to_upper_case = x == ' '
    return new_string

postprocess_entities()
