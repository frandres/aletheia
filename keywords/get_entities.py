#! /usr/bin/python

########################################################################
#
#  Example client to call TextServer XLIKE service 
#  to process a plain text
#
########################################################################

# import required libraries
import urllib2
import zipfile
from cStringIO import StringIO
# You may need to install "poster" python module for these two:
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import xml.etree.ElementTree as ET
from server_config import user, pwd
def get_entities(text,lang):
# Register the streaming http handlers with urllib2
    register_openers()

# set missing query elements
    target = 'entities'

# Encode query in a form-data.
# 'headers' contains the necessary Content-Type and Content-Length.
# 'datagen' is a generator object that yields the encoded parameters.
    datagen, headers = multipart_encode({'username':user,
                                         'password':pwd,
                                         'text_input':text,
                                         'language':lang,
                                         'target':target,
                                         'size':'0',
                                         'interactive':'1'
                                         } )
# service URL
    service = "xlike"
    url = "http://frodo.lsi.upc.edu:8080/TextWS/textservlet/ws/processQuery/"+service

# Create the Request object
    request = urllib2.Request(url, datagen, headers)
# Actually do the request, and get the response
    try:
      resp =  urllib2.urlopen(request).read()
# check for success in connection
    except urllib2.HTTPError, e:
        print e.code, e.reason
        exit()

# check for an error message from TextServer (invalid user, service not available, ...) 
    if (resp.find("<XML>") != -1) : 
      print resp
      exit()

# unzip and extract response
    zpf = zipfile.ZipFile(StringIO(resp), "r")
    for fname in zpf.namelist() : 
      if (fname.find(".out") == len(fname)-4) :
         res = zpf.read(fname)
    root = ET.fromstring(res)

    entities = {}
    for node in root.find('nodes'):
        if node.attrib['class'] == 'location':
            continue

        entities[node.attrib['displayName']] = []
        mentions = node.find('mentions')
        for mention in mentions.findall('mention'):
            entities[node.attrib['displayName']].append(mention.attrib['words'])

    return entities
