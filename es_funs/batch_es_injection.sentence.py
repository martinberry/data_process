# -*- coding: utf-8 -*-
import argparse
import sys

from elasticsearch import Elasticsearch
from elasticsearch.helpers import *

reload(sys)
sys.setdefaultencoding('utf8')


def parse_args():
    parser = argparse.ArgumentParser("batch injection")
    parser.add_argument("-s", "--server", required=True, help="server")
    parser.add_argument("-i", "--index", required=True, help="index name")
    parser.add_argument("-t", "--doctype", required=True, help="doctype")
    parser.add_argument("-f", "--file", required=True, help="file")
    return parser.parse_args()


def batch_injection(host, filename, index, doctype):
    es = Elasticsearch([host], timeout=60)
    with open(filename) as f:
        cnt = 0
        line = f.readline()
        actions = []
        while line and line != '\n':
            cnt += 1
            body_data = {}
            body_data["text"] = line.decode('utf-8')
            body_data["id"] = cnt
            body_data["_op_type"] = 'index'
            body_data["_index"] = index
            body_data["_type"] = doctype
            actions.append(body_data)
            if cnt % 10000 == 0:
                bulk(es, actions, stats_only=True)
                actions = []
                print 'processed %d requests' % cnt

            line = f.readline()

        if len(actions):
            bulk(es, actions, stats_only=True)
        print 'done: total %d requests' % cnt


if __name__ == '__main__':
    args = parse_args()
    batch_injection(args.server, args.file, args.index, args.doctype)

