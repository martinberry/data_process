#-*- coding: UTF-8 -*-
#################################################################
#    > File: filter.py
#    > Author: zhangminghua
#    > Mail: zhangmh1993@163.com
#    > Time: 2017-07-26 05:38:51 PM
#################################################################

from __future__ import division
import os
import sys
import codecs
import numpy
import logging
import json
import operator
from collections import defaultdict


def is_english_punctuation(uchar, en_punc):
    return uchar in en_punc

def is_chinese_punctuation(uchar, zh_punc):
    return uchar in zh_punc

def contains_en_punctuation(string):
    en_punc = u',.?!;:"'
    for c in string:
        if is_english_punctuation(c, en_punc):
            return True
    return False

def contains_zh_punctuation(string):
    zh_punc = u'，。？！：；、‘’“”《》〈〉（）…─～—·．「」『』〔〕【】□→×▲●〜'
    for c in string:
        if is_chinese_punctuation(c, zh_punc):
            return True
    return False

def contains_alphabet(string):
    for c in string:
        if rule_common.is_alphabet(c):
            return True
    return False

def parentheses_mismatch(string, paren):
    paren_L, paren_R = paren.values(), paren.keys()

    arr = list()
    for c in string:
        if c in paren_L:
            arr.append(c)
        elif c in paren_R:
            if arr and arr[-1] == paren[c]:
                arr.pop()
            else:
                return True

    return len(arr)>0


def multi_align(fields, **kwargs):
    if fields[-1] == 'src_multi' and fields[3][0] <= kwargs['multi_src_th']:
        return True
    elif fields[-1] == 'trg_multi' and fields[3][1] <= kwargs['multi_trg_th']:
        return True
    else:
        return False

def en_no_en(fields, **kwargs):
    if not contains_alphabet(fields[0]):
        return True
    else:
        return False

def zh_no_zh(fields, **kwargs):
    if not rule_common.contains_chinese(fields[1]):
        return True
    else:
        return False

def en_has_zhPunc(fields, **kwargs):
    if contains_zh_punctuation(fields[0]):
        return True
    else:
        return False

def zh_has_enPunc(fields, **kwargs):
    if contains_en_punctuation(fields[1]):
        return True
    else:
        return False

def start_with_Punc(fields, **kwargs):
    en_punc = u',.?!;:}])'
    zh_punc = u'，。？！：；、’”》〉）…─～—·．」』〕】□→×▲●〜'
    if is_english_punctuation(fields[0][0], en_punc) or is_chinese_punctuation(fields[0][0], zh_punc):
        return True
    elif is_english_punctuation(fields[1][0], en_punc) or is_chinese_punctuation(fields[1][0], zh_punc):
        return True
    else:
        return False

def zh_start_with_special(fields, **kwargs):
    if fields[1][0] in u'了的':
        return True
    else:
        return False

def en_end_with_special(fields, **kwargs):
    special = ['the']
    for suffix in special:
        if fields[0].endswith(suffix):
            return True
    return False

def en_paren_mismatch(fields, **kwargs):
    paren = {'}':'{', ']':'[', ')':'(', '>':'<'}
    if parentheses_mismatch(fields[0], paren) or parentheses_mismatch(fields[1], paren):
        return True
    else:
        return False

def zh_paren_mismatch(fields, **kwargs):
    paren = {u'）':u'（', u'》':u'《', u'】':u'【', u'〉':u'〈', u'」':u'「', u'』':u'『', u'〕':u'〔'}
    if parentheses_mismatch(fields[1], paren):
        return True
    else:
        return False

def ptr_sum_low(fields, **kwargs):
    if sum(fields[3]) < kwargs['ptr_sum_th']:
        return True
    else:
        return False

def ptr_or_low(fields, **kwargs):
    if (fields[3][0] < kwargs['ptr_src_th']) or (fields[3][1] < kwargs['ptr_trg_th']):
        return True
    else:
        return False

def lexicalW_zero(fields, **kwargs):
    if (fields[2][0] == 0.0) or (fields[2][1] == 0.0):
        return True
    else:
        return False

def len_diff(fields, **kwargs):
    lens = [len(fields[0].split()), len(fields[1].split())]
    ratio = max(lens) / min(lens)
    if ratio >= kwargs['ratio_bound']:
        return True
    else:
        return False


def judge(fields):
    for rule in conf['filter']['rules']:
        if eval(rule[0])(fields, **rule[1]):
            return rule[0]
    return 'pass'


def main(path_to_data):

    logging.info('Loading data ...')
    with codecs.open(path_to_data, 'r', 'utf-8') as fin:
        lines = fin.readlines()
    
    srcTran = defaultdict(list)
    trgTran = defaultdict(list)
    all_fields = list()
    for i in xrange(len(lines)):
        fields = lines[i].strip().split('\t')
        fields[2] = [ float(item) for item in fields[2].strip().split(' ') ]
        fields[3] = [ float(item) for item in fields[3].strip().split(' ') ]
        fields[4] = int(fields[4])
        all_fields.append(fields)

        srcTran[fields[0]].append(i)
        trgTran[fields[1]].append(i)
    
    with codecs.open(path_to_data+'.multi', 'w', 'utf-8') as fout:
        for ngram in srcTran:
            if len(srcTran[ngram]) > 1:
                for i in srcTran[ngram]:
                    all_fields[i].append('src_multi')

                if conf['filter']['debug']:
                    for i in srcTran[ngram]:
                        fout.write(lines[i])

        for ngram in trgTran:
            if len(trgTran[ngram]) > 1:
                for i in trgTran[ngram]:
                    all_fields[i].append('trg_multi')

                if conf['filter']['debug']:
                    for i in trgTran[ngram]:
                        fout.write(lines[i])

    logging.info('Filtering data ...')
    src_len_counts = defaultdict(int)
    trg_len_counts = defaultdict(int)
    drop_counts = defaultdict(int)
    with codecs.open(path_to_data+'.stay', 'w', 'utf-8') as fout:
        with codecs.open(path_to_data+'.drop', 'w', 'utf-8') as fdrop:
            for i in xrange(len(lines)):
                rule_name = judge(all_fields[i])
                
                if rule_name != 'pass':
                    drop_counts[rule_name] += 1
                    fdrop.write(lines[i].strip()+'\t'+rule_name+'\n')
                else:
                    len_src = len(all_fields[i][0].split())
                    len_trg = len(all_fields[i][1].split())
                    src_len_counts[len_src] += 1.
                    trg_len_counts[len_trg] += 1.
                    fout.write(lines[i])
    
    if conf['filter']['debug']:
        with codecs.open(path_to_data+'.count', 'w', 'utf-8') as fout:
            fout.write('src length:\n')
            fout.write( '\t'.join([ ('%d:%f' % (len_, src_len_counts[len_])) for len_ in src_len_counts]) +'\n' )
            fout.write('trg length:\n')
            fout.write( '\t'.join([ ('%d:%f' % (len_, trg_len_counts[len_])) for len_ in trg_len_counts]) +'\n' )

            fout.write('drop reason:\n')
            fout.write( '\t'.join([ ('%s:%f' % (rule, drop_counts[rule])) for rule in drop_counts ]) +'\n' )


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'usage : %s alignment file! ' % sys.argv[0]
        exit(1)
    else:
        fileHandler = logging.FileHandler(os.path.abspath('.')+'/log.'+sys.argv[0], mode='w', encoding='UTF-8')
        formatter = logging.Formatter('%(asctime)s %(filename)s[%(lineno)d] %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S')
        fileHandler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(fileHandler)

        fconf = os.path.join(os.path.split(os.path.abspath(sys.argv[0]))[0], sys.argv[0].split('.')[0]+'_conf.json')
        with codecs.open(fconf, 'r', 'utf-8') as fin:
            conf = json.load(fin)

        sys.path.append(conf['meta']['data_process'])
        import rule_common
        
        main(sys.argv[1])


