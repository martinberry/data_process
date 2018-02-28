#!/usr/bin/python

'''
This file is help to find top n sentences in elastic search with a input sentence.
It use simple_query_string mode to search result, default_operator is "AND". Which 
means all words need to be presented in the result. 
'''

import elasticsearch
import sys
import codecs

es = elasticsearch.Elasticsearch(['192.168.1.151'], timeout=60)

if len(sys.argv) < 6:
    print 'find_topn_sentences.py index "sentence" [topn]'
    print 'index: which index will be searched?'
    print '[topn]: optional, specify the n. If not provided, topn = 10.'
    print '[default_operator]: optoinal, value is "AND" or "OR". "AND" means all words in input sentence must be present. default is "OR".'
    print '"input": the input file for sentences to be searched'
    print '"output": the result file'
    sys.exit(-1)

indic = sys.argv[1]
topn = int(sys.argv[2])
default_operator = sys.argv[3]
input_file = sys.argv[4]
output_file = sys.argv[5]

with codecs.open(input_file, 'r', 'utf-8') as in_f:
    with codecs.open(output_file, 'w', 'utf-8') as out_f:
        cnt = 0
        for line in in_f:
            cnt += 1
            line = line.strip()

            try:
                res = es.search(
                    index=indic,
                    doc_type='sentence',
                    body={
                        'size': topn,
                        '_source': ["text", "id"],
                        'query': {
                            'simple_query_string': {
                                'query': line,
                                'default_operator': default_operator
                            }
                        }
                    }
                )

                if 'hits' in res and 'hits' in res['hits']:
                    for hit in res['hits']['hits']:
                        out_f.write(line + '\t' + str(hit['_source']['id']) + '\t' + hit['_source']['text'].strip() + '\n')
            except:
                print 'Exception occured when querying: %s' % line

            if cnt % 10000 == 0:
                print 'processed %d queries' % cnt
