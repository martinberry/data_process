# -*- coding: utf-8 -*-
import argparse
import sys

from elasticsearch import Elasticsearch

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
    es = Elasticsearch([host])
    with open(filename) as f:
        cnt = 0
        line = f.readline()
        data = []
        while line and line != '\n':
            data.append(line)
            cnt += 1
            if cnt % 6000 == 0:
                tmp = ''.join(data)
                # print tmp
                es.bulk(index=index, doc_type=doctype, body=tmp)
                print 'processed %d requests' % (cnt/2)
                data = []

            line = f.readline()

        if cnt > 0:
            es.bulk(index=index, doc_type=doctype, body=''.join(data))
        print 'done: total %d requests' % (cnt/2)


if __name__ == '__main__':
    args = parse_args()
    batch_injection(args.server, args.file, args.index, args.doctype)
