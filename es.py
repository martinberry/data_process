from datetime import datetime
from elasticsearch import Elasticsearch
import json

es = Elasticsearch(
    ['http://192.168.1.168:9200']
)
doc = json.load(open('es.json'))
res = es.create(index="testidx", doc_type='trans', id='1', body=doc)
print res
res = es.index(index="testidx", doc_type='trans', id='1', body=doc)
print res

