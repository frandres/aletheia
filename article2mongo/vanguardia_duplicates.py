from bson.objectid import ObjectId

from pymongo import MongoClient
conn = MongoClient() 
newsdb = conn.newsdb
collec = newsdb["catnews.spanish"]



#so from 1999-1-1 to 2015-1-20
years = ['1999', '2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015']
months = [1, 2, 3, 4, 5, 6, 7, 8, 9 , 10, 11, 12]
days = [1, 2, 3, 4, 5, 6, 7, 8, 9 , 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]

import string

#change this path to wherever you want to store the tsv output file (its not totally necessary, but its a way to monitor the status of things)
with open("/Applications/MAMP/htdocs/dama-larca/catalan2/vanguardia/dupes.tsv", "a") as myfile:
    myfile.write("appended text")
    myfile.write("date\ttitle\tnumber\tkeep\tremove\n")
    for y in years:
        for m in months:
            for d in days:
                date = y+"-"+str(m)+"-"+str(d)
                print "calling "+date
                resag = collec.aggregate([{"$match":{"date":date}},{ "$group": { "_id": { "title": "$title" }, 
                               "count": { "$sum": 1 }, "docs": { "$push": "$_id" }}},
                  { "$match": { "count": { "$gt" : 1 }}}, {'$limit': 10000}],allowDiskUse=True)
                i = 0
                for resa in resag['result']:
                    if i == 0:
                        print "\t" +date+": found duplicates- "+str(len(resag['result']))
                    i = i + 1
                    output = date+"\t"+resa["_id"]["title"] + "\t"+ str(resa["count"])
                    c = 0
                    for rd in resa["docs"]:
                        #print rd
                        if c == 0:
                            output = output + "\t" + str(rd) +"\t"
                            master_article = rd
                            collec.update({'_id': rd},{'$set':{'duplicate': False}},upsert=False, multi=False)
                        else:
                            output = output + str(rd)+", "
                            collec.update({'_id': rd},{'$set':{'duplicate': True,'parent':master_article}},upsert=False, multi=False)
                        c = c + 1   
                    #print output    
                    newout = filter(lambda x: x in string.printable, output)
                    myfile.write(newout+"\n")

