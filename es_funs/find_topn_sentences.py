#!/usr/bin/python

'''
This file is help to find top n sentences in elastic search with a input sentence.
It use simple_query_string mode to search result, default_operator is "AND". Which 
means all words need to be presented in the result. 
'''

import elasticsearch
import sys

es = elasticsearch.Elasticsearch(['192.168.1.168', '192.168.1.151'], timeout=60)

if len(sys.argv) < 3:
    print 'find_topn_sentences.py index "sentence" [topn]'
    print 'index: which index will be searched?'
    print '"sentence": the input sentence'
    print '[topn]: optional, specify the n. If not provided, topn = 10.'
    print '[default_operator]: optoinal, value is "AND" or "OR". "AND" means all words in input sentence must be present. default is "OR".'
    sys.exit(-1)

indic = sys.argv[1]
input_sentence = sys.argv[2]
topn = 10
default_operator = 'OR'
if len(sys.argv) > 3:
    topn = int(sys.argv[3])

if len(sys.argv) > 4:
    default_operator = sys.argv[4]

res = es.search(
    index=indic, 
    doc_type='sentence',
    body={
        'size': topn,
        '_source': ["text"],
        'query': {
            'simple_query_string' : {
                'query' : input_sentence,
                'default_operator': default_operator
            }
        }
    }
    )

if 'hits' in res and 'hits' in res['hits']:
    for hit in res['hits']['hits']:
        print hit['_source']['text'].strip()
