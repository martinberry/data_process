# -*- coding: utf-8 -*-
from rule import *
import re
import codecs
import shutil
import jieba
import os
import sys
import cPickle
import numpy as np
import requests
import time
import traceback
import json
import datetime
import elasticsearch as es
import base64
from subprocess import Popen, PIPE
import jellyfish, edit_distance
from nltk.tokenize.moses import MosesTokenizer, MosesDetokenizer
from HTMLParser import HTMLParser

# from toolwrapper import ToolWrapper
reload(sys)
sys.setdefaultencoding('utf8')


def is_contain_ms_special_character(line):
    """
    The line with character '\xe2\x80\a8' which comes from ms data will be removed in bpe process,
    because this character will force to generate a line feed leading to non-corresponding between
    source and target sentence.
    """
    return '\xe2\x80\xa8' in line


def is_chinese(uchar):
    return uchar >= u'\u4e00' and uchar <= u'\u9fa5'


def is_chinese_punctuation(uchar):
    return uchar in u'，。？！：；、‘’“”《》〈〉（）…─～—·．「」『』〔〕【】□→×▲●' or uchar == u'〜'  # 37


def is_ascii_printable(uchar):
    return uchar >= u'\u0021' and uchar <= u'\u007e'  # 93


def is_ascii_supplement(uchar):
    return uchar >= u'\u0080' and uchar <= u'\u00fe'  # 127


def is_latin_extended_a(uchar):
    return uchar >= u'\u0100' and uchar <= u'\u017f'  # 128


def is_latin_extended_b(uchar):
    return uchar >= u'\u0180' and uchar <= u'\u024f'  # 208


def is_greek_or_coptic(uchar):
    return uchar >= u'\u0370' and uchar <= u'\u03ff'  # 135


def is_general_punctuation(uchar):
    return uchar >= u'\u2000' and uchar <= u'\u206f'  # 111


def is_superscript_or_subscript(uchar):
    return uchar >= u'\u2070' and uchar <= u'\u209f'  # 42


def is_currency_symbol(uchar):
    return uchar >= u'\u20a0' and uchar <= u'\u20cf'  # 31


def is_letterlike_symbol(uchar):
    return uchar >= u'\u2100' and uchar <= u'\u214f'  # 80


def is_number_form(uchar):
    return uchar >= u'\u2150' and uchar <= u'\u218f'  # 60


def is_math_operator(uchar):
    return uchar >= u'\u2200' and uchar <= u'\u22ff'  # 256


def is_enclosed_alphanumeric(uchar):
    return uchar >= u'\u2460' and uchar <= u'\u24ff'  # 160


def is_math_operator_supplement(uchar):
    return uchar >= u'\u2a00' and uchar <= u'\u2aff'  # 256


def is_enclosed_cjk_letter(uchar):
    return uchar >= u'\u3220' and uchar <= u'\u3229' \
           or uchar >= u'\u3251' and uchar <= u'\u325f' \
           or uchar >= u'\u3280' and uchar <= u'\u3289' \
           or uchar >= u'\u32b1' and uchar <= u'\u32bf'  # 48


def is_cjk_compatibility(uchar):
    return uchar >= u'\u3371' and uchar <= u'\u3376' \
           or uchar >= u'\u3380' and uchar <= u'\u33dd'  # 100


def is_halfwidth_or_fullwidth(uchar):
    return uchar >= u'\uff01' and uchar <= u'\uff64' \
           or uchar >= u'\uffe0' and uchar <= u'\uffe2' \
           or uchar == u'\uffe5' \
           or uchar == u'\uffe6'  # 105


def is_number(uchar):
    if uchar >= '0' and uchar <= '9':
        return True
    else:
        return False


def is_alphabet(uchar):
    if uchar >= 'A' and uchar <= 'Z':
        return True
    elif uchar >= 'a' and uchar <= 'z':
        return True
    else:
        return False


def contains_number_alphabet(string):
    if not string:
        return False
    for c in string:
        if is_number(c) or is_alphabet(c):
            return True
    return False


def contains_chinese(string):
    if not string:
        return False
    for c in string:
        if is_chinese(c):
            return True
    return False


# class MosesTokenizer(ToolWrapper):
#     """A module for interfacing with ``tokenizer.perl`` from Moses.
#
#     This class communicates with tokenizer.perl process via pipes. When the
#     MosesTokenizer object is no longer needed, the close() method should be
#     called to free system resources. The class supports the context manager
#     interface. If used in a with statement, the close() method is invoked
#     automatically.
#
#     ###Note: ToolWrapper is only supported in py3###
#
#     """
#
#     def __init__(self, lang="en"):
#         self.lang = lang
#         program = os.path.join(
#             os.path.dirname(__file__),
#             "tokenizer/tokenizer.perl"
#         )
#         argv = ["perl", program, "-q", "-l", self.lang]
#
#         super().__init__(argv)
#
#     def __str__(self):
#         return "MosesTokenizer(lang=\"{lang}\")".format(lang=self.lang)
#
#     def __call__(self, sentence):
#         """Tokenizes a single sentence.
#
#         Newline characters are not allowed in the sentence to be tokenized.
#         """
#         assert isinstance(sentence, str)
#         sentence = sentence.rstrip("\n")
#         assert "\n" not in sentence
#         if not sentence:
#             return []
#         self.writeline(sentence)
#         return self.readline()

# 在for line in ...语句中\u2028会被当作额外一行，不能用RULELINE方法替换
class Remove_Add_Line_Char(Rule_File):
    def __init__(self):
        super(self.__class__,self).__init__()
        self.set_desc("remove \u2028 char to fix align problem",self)
        self.pattern = re.compile(ur'[\u2028]', re.IGNORECASE)
    def run(self, file):
        file = file[0]
        self.file_exist(file)
        with codecs.open(file,'r','utf-8') as f, codecs.open(self.output,'w','utf-8') as f2:

            buf = f.read(50000)
            while buf:
                buf = re.sub(self.pattern, '', buf)
                f2.write(buf)
                buf = f.read(50000)
        return [self.output]

class Fix_Labels(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc("Only used to clean data with lines of en\tzh. "
                      "When '(Fig.' occurs at the tail of the en sentence, remove it and its corresponding translation in zh. "
                      "When zh contains '（图（图', remove this line.", self)

    def run(self, line):
        if not line:
            return None

        src, trg = line.split('\t')

        if trg.find(u'（图（图') > -1 or trg.find(u'[图[图') > -1:
            return None

        if src.endswith('(Fig.'):
            src = src[:-5]
            if re.search(u'（图\d）。\Z',trg):
                trg = trg[:-5]
            elif trg.endswith(u'（图。'):
                trg = trg[:-3]
        line = '\t'.join([src,trg])

        return line


class Replace_HTML_Entities(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.parser = HTMLParser()
        self.set_desc("Replace HTML entities with corresponding utf-8 character.", self)

    def run(self, line):
        if not line:
            return None

        line = self.parser.unescape(line)

        line = line.strip()
        return line


class FullWidth_To_Halfwidth(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.init_dict()
        self.set_desc('Change fullwidth character to halfwidth character.', self)

    def init_dict(self):
        # ascii
        keys = [unichr(i) for i in range(0xff01,0xff5f)]
        values = [unichr(i-65248) for i in range(0xff01,0xff5f)]

        # ¢,£,¬,¯,¦,¥,₩
        keys.extend([u'\uffe0', u'\uffe1', u'\uffe2', u'\uffe3', u'\uffe4', u'\uffe5', u'\uffe6'])
        values.extend([u'\u00a2', u'\u00a3', u'\u00ac', u'\u00af', u'\u00a6', u'\u00a5', u'\u20a9'])

        self.dict = dict(zip(keys, values))

    def run(self, line):
        if not line:
            return None

        new_line = []
        for w in line.strip():
            new_line.append(self.dict.get(w, w))

        line = ''.join(new_line)
        return line


class FullWidth_To_Halfwidth_v2(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.init_dict()
        self.set_desc('Change fullwidth character to halfwidth character.', self)

    def init_dict(self):
        # ascii
        keys = [unichr(i) for i in range(0xff01, 0xff5f)]
        values = [unichr(i-65248) for i in range(0xff01, 0xff5f)]

        # ¢,£,¬,¯,¦,¥,₩
        keys.extend([u'\uffe0', u'\uffe1', u'\uffe2', u'\uffe3', u'\uffe4', u'\uffe5', u'\uffe6'])
        values.extend([u'\u00a2', u'\u00a3', u'\u00ac', u'\u00af', u'\u00a6', u'\u00a5', u'\u20a9'])

        self.dict = dict(zip(keys, values))

        # chinese punctuations to exclude
        excludes = [u'！', u'（', u'）', u'，', u'：', u'；', u'？', u'～']

        for c in excludes:
            if c in self.dict:
                del self.dict[c]

    def run(self, line):
        if not line:
            return None

        new_line = []
        for w in line.strip():
            new_line.append(self.dict.get(w, w))

        line = ''.join(new_line)
        return line


class Pair_Punctuation_Close_Check(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.init_pairs(kwargs)
        self.set_desc('Check if punctuations in pair are closed, if not, remove this line.', self)

    def init_pairs(self, kwargs):
        puncpairs = ["\"\"","{}","[]","()","‘’","“”","《》","｛｝","（）"]
        self.puncpairs = [pair.decode('utf-8') for pair in puncpairs]

        if 'newpairs' in kwargs:
            self.puncpairs.extend([pair.decode('utf-8') for pair in kwargs['newpairs']])

    def run(self, line):
        if not line:
            return None

        stacks = []
        puncs = []
        for puncpair in self.puncpairs:
            puncs.extend(list(puncpair))

        for w in line:
            if w in puncs:
                if len(stacks) == 0:
                    stacks.append(w)
                elif stacks[-1] + w in self.puncpairs:
                    stacks.pop()
                else:
                    stacks.append(w)

        if len(stacks) != 0:
            return None

        return line

class Pair_Slot_Tag_NoTrans(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Replace not translated template with special tag', self)

        self.notrans_tag = kwargs["notrans_tag"] if 'notrans_tag' in kwargs else '<NOTRANS>'
        self.len_tag = len(self.notrans_tag)
        patterns_list = [ur'http[:：]//[a-zA-Z0-9\-_~\*\'@&=\+\$/\?#\.]+[a-zA-Z0-9/#]',
                    ur'(www\.[A-Za-z0-9\-_~\*\'@&=\+\$/\?#\.]+[a-zA-Z0-9/#])',
                    ur'(([A-Za-z0-9\.-]+\.[A-Za-z0-9-]+|[A-Za-z]+)@[A-Za-z0-9\.-]+[A-Za-z])']

        self.patterns_list = list(map(re.compile, patterns_list))
        self.len_patterns_list = len(self.patterns_list)

    def run(self, line):
        if not line:
            return None

        line = line.strip()
        line_frags = line.split('\t')

        if len(line_frags) != 2 or not len(self.patterns_list):
            return line

        source_str = line_frags[0].strip()
        target_str = line_frags[1].strip()
        target_start_pos = 0
        target_end_pos = len(target_str)
        var_tag_start = target_start_pos  # var_tag_start, var_tag_end are the boundary of substr
        var_tag_end = target_end_pos

        if target_start_pos < target_end_pos:
            while var_tag_start < var_tag_end:
                if target_str[var_tag_start] == ' ':  # substr is begin with non-space character
                    var_tag_start += 1
                elif target_str[var_tag_end - 1] == ' ':  # substr is end with non-space character
                    var_tag_end -= 1
                else:
                    substr = target_str[var_tag_start:var_tag_end]  # get the substr
                    var_src_start = source_str.find(substr)  # find the start position of substr in source_str
                    if var_src_start >= 0:
                        for i in range(self.len_patterns_list):  # match every pattern, end with match a pattern or nothing
                            m = self.patterns_list[i].search(substr)
                            if m:
                                startpos = m.start()
                                endpos = m.end()
                                len_substr = len(substr)
                                cut_src_start = var_src_start + startpos  # caclute the start and end position of str cutting
                                cut_src_end = cut_src_start + endpos - startpos
                                cut_tag_start = var_tag_start + startpos
                                cut_tag_end = cut_tag_start + endpos - startpos
                                source_str = source_str[:cut_src_start] + self.notrans_tag + source_str[cut_src_end:]  # add the non-trans tag
                                target_str = target_str[:cut_tag_start] + self.notrans_tag + target_str[cut_tag_end:]

                                var_tag_end = cut_tag_start + len_substr - endpos + self.len_tag  # caclute the matching ending position in new target_str after adding the non-trans tag
                                target_end_pos = target_end_pos + self.len_tag - (endpos - startpos)  # the ending boundary of target_str should be caculated again
                                break

                        var_tag_start = var_tag_end
                        var_tag_end = target_end_pos
                    else:
                        if var_tag_end == var_tag_start + 1:
                            var_tag_start += 1
                            var_tag_end = target_end_pos
                        else:
                            var_tag_end -= 1

        return source_str + '\t' + target_str + '\n'


class Pair_Slot_Tag_Number(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Replace number with number_tag', self)
        self.number_tag = kwargs["number_tag"] if 'number_tag' in kwargs else '<N>'
        En_Reg_List = [
            ur'\b\d{1,3}(,\d{3})+(\.\d+)? ?(m|million|bn|billion|trillion|tn)\b',  # Strict format
            ur'\b\d{1,3}( \d{3})+(\.\d+)? ?(m|million|bn|billion|trillion|tn)\b',  # Strict format
            ur'\b\d+(\.\d+)? ?(m|million|bn|billion|trillion|tn)\b'  # Arbitrary format
        ]

        Zh_Reg_List = [
            ur'\b\d{1,3}(,\d{3})+(\.\d+)?\s*(万亿|万|亿)',  # Strict format num
            ur'\b\d{1,3}( \d{3})+(\.\d+)?\s*(万亿|万|亿)',  # Strict format num
            ur'\b\d+(\.\d+)?\s*(万亿|万|亿)'  # Arbitrary format num
        ]
        self.En_Reg_List = [re.compile(r, re.IGNORECASE) for r in En_Reg_List]
        self.Zh_Reg_List = [re.compile(r, re.IGNORECASE) for r in Zh_Reg_List]

    def correct_illion(self, num):
        pure_num = re.sub(r'(?P<d>\d) ?(m|million|bn|billion|trillion|tn)$', r'\g<d>', num)
        if pure_num != num:
            unit = num[len(pure_num):].lstrip()
            pure_num = re.sub(r',| ', '', pure_num)
            if unit.startswith('m'):
                result = self.increase_magnitude(pure_num, 6)
            elif unit.startswith('b'):
                result = self.increase_magnitude(pure_num, 9)
            else:
                result = self.increase_magnitude(pure_num, 12)
        else:
            result = pure_num

        return result

    def correct_wan_yi(self, num):
        pure_num = re.sub(ur'(?P<d>\d) ?(万亿|万|亿)$', r'\g<d>', num)
        if pure_num != num:
            unit = num[len(pure_num):].lstrip()
            pure_num = re.sub(r',| ', '', pure_num)
            if unit == u'万':
                result = self.increase_magnitude(pure_num, 4)
            elif unit == u'亿':
                result = self.increase_magnitude(pure_num, 8)
            else:
                result = self.increase_magnitude(pure_num, 12)
        else:
            result = pure_num

        return result

    def increase_magnitude(self, orig_num, mag):
        point_pos = orig_num.find('.')
        if point_pos < 0:
            new_num = orig_num + mag * '0'
        else:
            intg = orig_num[:point_pos]
            frct = orig_num[point_pos + 1:]
            if len(frct) == mag:
                new_num = orig_num.replace('.', '')
            elif len(frct) > mag:
                new_num = intg + frct[:mag] + '.' + frct[mag:]
                new_num = new_num.rstrip('0.')
            else:
                new_num = intg + frct + (mag - len(frct)) * '0'

            new_num = new_num.lstrip('0')
            if new_num.startswith('.'):
                new_num = '0' + new_num

        return new_num

    def match_frags(self, frag, reg):
        if frag[1]:
            line = frag[0]
            start = 0
            frags = []
            for match in reg.finditer(line):
                frags.append([line[start: match.span()[0]], True])
                frags.append([match.group(), False])

                start = match.span()[1]

            last_frag_text = line[start:]
            if last_frag_text:
                frags.append([last_frag_text, True])

            return frags

        else:
            return [frag]

    def slot_tag(self, src_line, trg_line):
        src_reglist, trg_reglist = self.En_Reg_List, self.Zh_Reg_List
        src_frags, trg_frags = [(src_line, True)], [(trg_line, True)]

        for src_reg in src_reglist:
            new_src_frags = []
            for frag in src_frags:
                sub_frags = self.match_frags(frag, src_reg)
                new_src_frags.extend(sub_frags)

            src_frags = new_src_frags

        for trg_reg in trg_reglist:
            new_trg_frags = []
            for frag in trg_frags:
                sub_frags = self.match_frags(frag, trg_reg)
                new_trg_frags.extend(sub_frags)

            trg_frags = new_trg_frags

        src_match_list = []
        trg_match_list = []
        for pos in range(len(src_frags)):
            if not src_frags[pos][1]:
                src_match_list.append([self.correct_illion(src_frags[pos][0]), pos])

        for pos in range(len(trg_frags)):
            if not trg_frags[pos][1]:
                trg_match_list.append([self.correct_wan_yi(trg_frags[pos][0]), pos])

        if src_match_list and trg_match_list:
            for src_val in src_match_list:
                 for trg_val in trg_match_list:
                    if src_val[0] == trg_val[0] and trg_val[1] >= 0:  # align
                        src_frags[src_val[1]][0] = self.number_tag  # replace number with number_tag
                        trg_frags[trg_val[1]][0] = self.number_tag
                        trg_val[1] = -1  # target should be aligned once
                        break

        src_texts = []
        for frag in src_frags:
            text = frag[0]
            src_texts.append(text)

        trg_texts = []
        for frag in trg_frags:
            text = frag[0]
            trg_texts.append(text)

        return "".join(src_texts), "".join(trg_texts)

    def run(self, line):

        if not line:
            return None

        line = line.strip()
        line_frags = line.split('\t')

        if len(line_frags) != 2:
            return line

        source_str = line_frags[0].strip()
        target_str = line_frags[1].strip()

        source_str, target_str = self.slot_tag(source_str, target_str)

        return source_str + '\t' + target_str


class Separate_Number_Unit(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r'\b(?P<number>\d+(,\d+)*(\.\d+)?)(?P<unit>[a-z]+)\b',
                     f,
                     r'\g<number> \g<unit>'))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Separate the Number Unit', self)


class Remove_Square_Content(Rule_Line):
    def __init__(self, **kwargs):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r"（", f, "("))
        re_s.append((r"）", f, ")"))
        re_s.append((r"【", f, "("))
        re_s.append((r"】", f, ")"))
        re_s.append((r"<", f, "("))
        re_s.append((r">", f, ")"))
        re_s.append((r"\([^\)]+\)", f, ""))
        re_s.append((r"\(", f, ""))
        re_s.append((r"\)", f, ""))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove all square and its content', self)


class Remove_Single_Quotation(Rule_Line):
    def __init__(self, **kwargs):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r"^'", f, ""))
        re_s.append((r"'$", f, ""))
        re_s.append((r"'\t", f, "\t"))
        re_s.append((r"([^s])'([ ,.?!])", f, "\\1 \\2"))
        re_s.append((r"([ ,.?!])'", f, "\\1"))
        re_s.append((r"\([^s]\)' ", f, "\\1 "))
        re_s.append((r" '", f, " "))
        re_s.append((r"‘", f, ""))
        re_s.append((r"`", f, ""))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove single quotation marks, except in real word', self)


# Remove English
class Remove_Single_Quotation_v2(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Remove single quotation marks, except in real word', self)

    def run(self, line):
        if not line:
            return None
        line = line.strip()

        idx = line.find('\'')
        while idx >= 0:
            if idx == 0:
                line = line[1:]
                idx = line.find('\'')
            else:
                if line[idx - 1].lower() != 's':
                    if idx == len(line) - 1:
                        line = line[:idx]
                        break
                    elif not (line[idx - 1] == '>' or (line[idx - 1].lower() >= 'a' and line[idx - 1].lower() <= 'z')) \
                            or not (line[idx + 1].lower() >= 'a' and line[idx + 1].lower() <= 'z'):
                        line = line[:idx] + line[idx + 1:]
                        idx = line.find('\'', idx)
                    else:
                        idx = line.find('\'', idx + 1)
                else:
                    idx = line.find('\'', idx + 1)

        line = re.sub(ur'‘|’|`', '', line)

        return line


class Remove_Bad_Begin(Rule_Line):
    def __init__(self, **kwargs):
        re_s = []
        f = re.IGNORECASE
        re_s.append((ur"^[,.?!:;*#\-> ，。？！：；、]+", f, ""))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove bad beginning characters', self)


class Remove_Special_Chars(Rule_Line):
    def __init__(self, **kwargs):
        re_s = []
        f = re.IGNORECASE
        re_s.append((ur"[\u200b]", f, ""))
        re_s.append((ur"[\ufeff]", f, ""))
        re_s.append((ur"[\u2028]", f, ""))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove special characters', self)


class Remove_Empty_Line(Rule_Line):
    def __init__(self, **kwargs):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r"^$", f, ""))
        re_s.append((r"^\s\+\t.*", f, ")"))
        re_s.append((r"^.*\t\s+$", f, ""))
        re_s.append((r"^.*\t$", f, ""))
        re_s.append((r"^\t.*", f, ""))
        re_s.append((r"^.*-{5,}.*", f, ""))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove all empty and no-sense lines', self)


class Remove_Redundant_Spaces(Rule_Line):
    def __init__(self, **kwargs):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r"^[ ]+", f, ""))
        re_s.append((r"[ ]+$", f, ""))
        re_s.append((r"[ ]+", f, " "))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove redundant spaces', self)


class Restore_Entity(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc(
            'Restore entity slots. Note: it should be used after General_Tokenizer/General_Sentence_Tokenizer', self)
        self.entity_tag = kwargs["entity_tag"] if 'entity_tag' in kwargs else None
        case_sens = kwargs["case_sensitive"] if 'case_sensitive' in kwargs else 'False'
        self.is_case_sens = case_sens.lower() == 'true'

    def match_frags(self, text, regex, entity_types):
        start = 0
        frags = []
        for match in regex.finditer(text):
            match_beg = match.span()[0]
            match_end = match.span()[1]

            frags.append(text[start: match_beg])

            entity = text[match_beg:match_end]
            tag = entity[1: entity.find('>')]
            content = entity[len(tag) + 2: len(entity) - len(tag) - 3]

            if tag in entity_types:
                frags.append(
                    '<' + tag + ':' + base64.b64encode(base64.b16decode(content.replace(' ', '').upper())) + '>')
            else:
                frags.append(entity)

            start = match_end

        last_frag_text = text[start:]
        if last_frag_text:
            frags.append(last_frag_text)

        return frags

    def run(self, line):
        if not line:
            return None

        line = line.strip()

        if not self.entity_tag:
            return line

        entity_tags = self.entity_tag.split('|')
        for tag in entity_tags:
            line = line.replace('&gt; &apos; s ', '&gt; &apos;s ')
            if self.is_case_sens:
                line = line.replace('&lt; %s &gt;' % tag, '<%s>' % tag)
                line = line.replace('&lt; / %s &gt;' % tag, '</%s>' % tag)
            else:
                line = line.replace('&lt; %s &gt;' % tag.lower(), '<%s>' % tag)
                line = line.replace('&lt; / %s &gt;' % tag.lower(), '</%s>' % tag)

        try:
            # Reform entity content for decoding
            entity_content_slot_reg = re.compile(r'<([A-Za-z]+)>[^<]+</\1>')
            line = ''.join(self.match_frags(line, entity_content_slot_reg, entity_tags))
        except:
            print line
            line = ''

        return line


class Restore_Entity_v2(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc(
            'Restore entity slots. Note: it should be used after General_Tokenizer/General_Sentence_Tokenizer', self)
        self.entity_tag = kwargs["entity_tag"] if 'entity_tag' in kwargs else None

    def run(self, line):
        if not line:
            return None

        line = line.strip()

        if not self.entity_tag:
            return line

        entity_tags = self.entity_tag.split('|')
        for tag in entity_tags:
            line = re.sub(r'\b' + tag.lower() + r' _ (\d+)\b', r'%s_\1' % tag)

        return line


class Remove_No_Entity_Line(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Remove the pairs that don\'t contain entity or one of which doesn\'t contain entity', self)

        entity_tag = kwargs["entity_tag"] if 'entity_tag' in kwargs else None
        self.entity_tokens = []
        if entity_tag:
            self.entity_tokens = ['<%s>' % x for x in entity_tag.split('|')]

    def run(self, line):
        if not line:
            return None

        line = line.strip()
        line_frags = line.split('\t')

        if len(line_frags) != 2 or not len(self.entity_tokens):
            return line

        both_contain = True
        for frag in line_frags:
            contain = False
            for token in self.entity_tokens:
                if token in frag:
                    contain = True
                    break

            if not contain:
                both_contain = False
                break

        if both_contain:
            return line

        return None


class Norm_Ellipsis(Rule_Line):
    def __init__(self, **kwargs):
        re_s = []
        ell = '...'
        f = re.IGNORECASE
        re_s.append((r"\?\.\?\.\?\. \?", f, ell))
        re_s.append((r"\?\.\?\.\?\.\?\.", f, ell))
        re_s.append((r"\?\.\?\.\?\.", f, ell))
        re_s.append((r"\?\.\?\. \?\.", f, ell))
        re_s.append((r"\.\?\.\?\.", f, ell))
        re_s.append((r"\?\.\?\.", f, ell))
        re_s.append((r"\. \. \.", f, ell))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Normalize illegal ellipsis (e.g. .?.?.?)', self)


class Entity_URL(Rule_Line):
    def __init__(self, **kwargs):
        re_s = []
        f = re.IGNORECASE
        u = '<URL>'
        re_s.append((r"https?://[a-zA-Z0-9/\.@\-#\?&]+", f, u))
        re_s.append((r"www\.[a-zA-Z0-9/\.@\-#?&]+", f, u))
        re_s.append((
            r"(http://|https://)?[a-zA-Z0-9/\.@\-#?&]+(\.com|\.net|\.edu|\.cn|\.org|\.info)[a-zA-Z0-9/\.@\-#?&]*",
            f, u))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Entity: replace URLs to <URL>', self)


class Entity_Digit_StyleA(Rule_Line):
    def __init__(self, **kwargs):
        re_s = [(r"[0-9]", re.IGNORECASE, "0")]
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Entity: replace all digits to 0, this is regarded as style A', self)


class Segment_Jieba(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Jieba segment, please only apply to Chinese sentence', self)

    def run(self, line):
        if not line:
            return None
        line = line.strip()
        return " ".join(jieba.cut(line, cut_all=False))


class To_Lower(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Convert to lower case', self)

    def run(self, line):
        if not line:
            return None
        return line.lower()


class General_Sentence_Detokenizer(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('general sentence level detokenizer (same as in Moses)', self)

        lang = 'en'
        if 'lang' in kwargs:
            lang = kwargs['lang']

        self.detokenizer = MosesDetokenizer(lang)

    def run(self, line):
        if not line:
            return None
        return self.detokenizer.detokenize(line.strip().split(), return_str=True)

class General_Sentence_Detokenizer_Bracketfix(Rule_Line):
    '''
    解决翻译后([{右侧有空格的问题
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('general sentence level detokenizer (same as in Moses)', self)

        lang = 'en'
        if 'lang' in kwargs:
            lang = kwargs['lang']

        self.detokenizer = MosesDetokenizer(lang)

    def run(self, line):
        if not line:
            return None
        line = re.sub('\( ','(',line)
        line = re.sub('\{ ','{',line)
        line = re.sub('&#91; ','&#91;',line)
        line = re.sub(r' *\\ *','\\\\',line)
        line = re.sub(r' */ *', '/', line)
        return self.detokenizer.detokenize(line.strip().split(), return_str=True)

class General_Sentence_Tokenizer(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('general sentence level tokenizer (same as in Moses), URLs not impacted', self)
        self.lang = 'en'
        if 'lang' in kwargs:
            self.lang = kwargs['lang']
        self.tokenizer = MosesTokenizer(self.lang)
        tokenizer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tokenizer', 'tokenizer.perl')
        self.tokenizer_cmd = [tokenizer_path, "-l", self.lang, "-q", "-"]
        self.url_re = re.compile(ur'https?[:：]//[a-z0-9\-_~\*\'@&=\+\$/\?#]+[a-zA-Z0-9/#]', re.IGNORECASE)

    def tokenize(self, line):
        return self.tokenizer.tokenize(line, return_str=True)

    def run(self, line):
        if not line:
            return None

        line = line.strip()
        sentence, en_frags = self._match_frags(line, self.url_re)

        sentence = self.tokenize(sentence)

        if sentence.count('UUU') != len(en_frags):
            sentence = self.tokenize(line)
        else:
            en_idx = 0
            rp_idx = sentence.find('UUU')
            while rp_idx >= 0:
                sentence = sentence[:rp_idx] + en_frags[en_idx] + sentence[rp_idx + 1:]
                rp_idx = sentence.find('UUU', rp_idx + len(en_frags[en_idx]))
                en_idx += 1

        return sentence.strip()

    def _match_frags(self, line, reg):
        start = 0
        frags = []
        en_frags = []
        for match in reg.finditer(line):
            frags.append(line[start: match.span()[0]])

            matched_str = line[match.span()[0]: match.span()[1]]
            frags.append('UUU')
            en_frags.append(matched_str)

            start = match.span()[1]

        last_frag_text = line[start:]
        if last_frag_text:
            frags.append(last_frag_text)

        return ''.join(frags), en_frags

class Align_Sentence_Detokenizer(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('align sentence level detokenizer (same as in Moses)', self)

        lang = 'en'
        if 'lang' in kwargs:
            lang = kwargs['lang']

        if 'mode' in kwargs:
            self.mode = kwargs['mode']
        else:
            self.mode = 'script'
        self.detokenizer = MosesDetokenizer(lang)

        detok_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tokenizer', 'detokenizer.perl')
        self.tokenizer_cmd = [detok_path, "-l", lang, "-q", "-"]

    def run(self, align_enabled, tgt_origin, src_origin):
        if not align_enabled or not tgt_origin or not src_origin:
            return None, None
        if self.mode == 'script':
            return self.detokenize_with_perl(tgt_origin), self.detokenize_with_perl(src_origin)
        else:
            return self.detokenize_with_nlkt_mosestokenizer(tgt_origin), self.detokenize_with_nlkt_mosestokenizer(src_origin)

    def detokenize_with_nlkt_mosestokenizer(self, src):
        self.pre_process(src)
        retval = []
        for each in src:
            retval.append(self.detokenizer.detokenize([each.decode('utf8')], return_str=True))
        return retval

    # todo: this function will later be substituted by detokenize_with_nlkt_mosestokenizer
    def detokenize_with_perl(self, src):
        self.pre_process(src)
        detokenizer = Popen(self.tokenizer_cmd, stdin=PIPE, stdout=PIPE)
        target = detokenizer.communicate('\n'.join(src))[0]
        return target.split('\n')[: -1]

    def pre_process(self, src):
        for index in range(len(src)):
            item = src[index]
            if item.startswith('<N:') and item.endswith('>'):
                try:
                    src[index] = base64.decodestring(item[3:-1])
                except:
                    src[index] = item
            else:
                src[index] = item


class Remove_Consecutive_Dash_Or_Underscore(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r'(\s?-\s?){2,}|(\s?_\s?){2,}', f, ' '))
        super(self.__class__, self).__init__(re_s)
        self.set_desc("Dedupe the repeated English punctuations of fix number problem", self)


class BD_Recover(Rule_Line):
    def __init__(self, **kwargs):
        re_s = []
        f = 0
        re_s.append((r"<B>(.) ", f, "\\1"))
        re_s.append((r"<M>(.) ", f, "\\1"))
        re_s.append((r"<M>(.) ", f, "\\1"))
        re_s.append((r"<E>(.)", f, "\\1"))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Recover BD breaking to word', self)


class BPE_Recover(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Recover BPE from word format: p1@@ p2@@ ...pn-1@@ pn', self)

    def run(self, line):
        if not line:
            return None
        return line.replace('@@ ', '')


class BPE_Recover_v2(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Recover BPE from word format: _p1 p2 ...pn', self)

    def run(self, line):
        if not line:
            return None

        line = line.replace(' ', '')
        line = re.sub(r'_(.)', ' \\1', line)

        return line


class Remove_Heading_Numbers(Rule_Line):
    def __init__(self, **kwargs):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r"^(20[0-9][0-9])", f, "ccc\\1"))
        re_s.append((r"^(19[0-9][0-9])", f, "ccc\\1"))
        re_s.append((r"^[0-9., ]+", f, ""))
        re_s.append((r"^ccc(20[0-9][0-9])", f, "\\1"))
        re_s.append((r"^ccc(19[0-9][0-9])", f, "\\1"))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove heading numbers except years', self)


class BD_Break_Line(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Line: break word to character according to a voc', self)
        if 'voc' not in kwargs:
            print 'voc not found, check schema'
            raise Exception
        self.dic = set()
        with codecs.open(kwargs['voc'], 'r', 'utf-8') as f:
            lines = f.readlines()
            for l in lines:
                self.dic.add(l.strip())

    def run(self, line):
        if not line:
            return None
        return self.convert_line_to_mixed_wc(line.strip(), self.dic)

    def convert_word_to_chars(self, word):
        new_words = []
        w_len = len(word)
        for i in xrange(w_len):
            if i == 0:
                prefix = '<B>'
            elif i == w_len - 1:
                prefix = '<E>'
            else:
                prefix = '<M>'
            new_words.append(prefix + word[i])

        # print '%s => %s' % (word, new_words)
        return new_words

    def convert_line_to_mixed_wc(self, line, dic):
        words = line.split()
        new_words = []
        for w in words:
            if w not in dic:
                new_words.extend(self.convert_word_to_chars(w))
            else:
                new_words.append(w)
        return " ".join(new_words)


class Levenshtein_Distance(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Line: Compute Levenshtein Distance between two strings in word or char level', self)
        self.mode = 'char'
        if 'mode' in kwargs:
            if kwargs['mode'] not in ['word', 'char']:
                print 'Only support two modes: char or word'
                raise Exception
            else:
                self.mode = kwargs['mode']

    def run(self, line):
        if not line:
            return None

        frags = line.strip().split('\t')
        if len(frags) != 2:
            print 'Format error: the input line must be two strings separated with \t'
            raise Exception

        if self.mode == 'char':
            return str(jellyfish.levenshtein_distance(frags[0], frags[1]))
        else:
            s1_seqs = frags[0].split()
            s2_seqs = frags[1].split()
            return str(edit_distance.edit_distance(s1_seqs, s2_seqs)[0])


class Fuzzy_Match_Score(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Line: Compute Fuzzy Match Score between two strings in word or char level', self)
        self.mode = 'char'
        if 'mode' in kwargs:
            if kwargs['mode'] not in ['word', 'char']:
                print 'Only support two modes: char or word'
                raise Exception
            else:
                self.mode = kwargs['mode']

    def run(self, line):
        if not line:
            return None

        frags = line.strip().split('\t')
        if len(frags) != 2:
            print 'Format error: the input line must be two strings separated with \t'
            raise Exception

        if self.mode == 'char':
            ed = jellyfish.levenshtein_distance(frags[0], frags[1])
            fms = 1. - ed * 1. / max(len(frags[0]), len(frags[1]))
        else:
            s1_seqs = frags[0].split()
            s2_seqs = frags[1].split()
            ed = edit_distance.edit_distance(s1_seqs, s2_seqs)[0]
            fms = 1. - ed * 1. / max(len(s1_seqs), len(s2_seqs))

        return str(fms)


class Align_Target_Source(Rule_Line):
    def __init__(self, append_space=False):
        super(self.__class__, self).__init__()
        self.append_space = bool(append_space)
        self.set_desc('Align target and source translation result with index', self)

    def run(self, align_enabled, tgt_array, src_array, tgt_src_mapping):
        if not align_enabled or not tgt_array or not src_array or not tgt_src_mapping:
            return None, None, None
        tgt_array_src_mapping = [[tgt_array[i], int(tgt_src_mapping[i])] for i in range(len(tgt_array))]

        index = 0
        temp = ''

        # is_in_word_sythesis(default True) is a flag to enter synthesis(word.endswith('@@')) model
        is_in_word_synthesis = False
        is_in_compound = False
        src_origin = []

        len_arc_array = len(src_array)

        while index < len_arc_array:
            item = src_array[index]
            is_need_update = index in tgt_src_mapping
            if item.endswith('@@'):
                temp += item[: -2]
                is_in_word_synthesis = True
                is_append_model = not is_in_compound
                self.update_mapping(is_need_update, tgt_array_src_mapping, src_origin, index,
                                    is_append_model=is_append_model)
            elif item.startswith("'") and len_arc_array != 1:
                src_origin[-1] += item
                self.update_mapping(is_need_update, tgt_array_src_mapping, src_origin, index, is_append_model=False)
            elif item == '<->':
                src_origin[-1] += '-'
                is_in_compound = True
                self.update_mapping(is_need_update, tgt_array_src_mapping, src_origin, index, is_append_model=False)
            else:
                if is_in_compound:
                    if is_in_word_synthesis:
                        temp += item
                        is_in_word_synthesis = False
                        self.update_mapping(is_need_update, tgt_array_src_mapping, src_origin, index,
                                            is_append_model=False)
                        src_origin[-1] += temp
                        temp = ''
                    else:
                        src_origin[-1] += item
                        self.update_mapping(is_need_update, tgt_array_src_mapping, src_origin, index,
                                            is_append_model=False)
                    is_in_compound = False
                else:
                    if is_in_word_synthesis:
                        temp += item
                        is_in_word_synthesis = False
                        self.update_mapping(is_need_update, tgt_array_src_mapping, src_origin, index)
                        src_origin.append(temp)
                        temp = ''
                    else:
                        self.update_mapping(is_need_update, tgt_array_src_mapping, src_origin, index)
                        src_origin.append(item)

            index += 1

        tgt_origin = []
        mapping = []

        current_index = -1
        is_in_word_synthesis=False

        for item in tgt_array_src_mapping:
            end_with_compound_punc = False
            if item[0].endswith('@@'):
                element = item[0][: -2]
                end_with_compound_punc = True
            elif item[0].startswith('\''):
                element = item[0]
                is_in_word_synthesis = True
            elif item[0] == '<->':
                element = '-'
                is_in_word_synthesis = True
                end_with_compound_punc = True
            else:
                element = item[0]
            index = item[1]
            if index == current_index:
                if self.append_space == True:
                    if is_in_word_synthesis:
                        tgt_origin[-1]+=element
                    else:
                        tgt_origin[-1] += (' ' + element)
                else:
                    tgt_origin[-1] += element
            else:
                tgt_origin.append(element)
                current_index = index
                mapping.append(index)
            is_in_word_synthesis = False
            if end_with_compound_punc:
                is_in_word_synthesis = True

        for i in range(len(mapping)):
            if mapping[i] == len(src_array):
                mapping[i] = len(src_origin)
        return tgt_origin, src_origin, mapping

    def update_mapping(self, is_need_update, mapping, src_origin, index, is_append_model=True):
        if is_need_update:
            len_mapping = len(mapping)
            for i in range(len_mapping):
                if mapping[i][1] == index:
                    mapping[i][1] = len(src_origin) if is_append_model else len(src_origin) - 1


###########################################################################################
##      File rules below
###########################################################################################


class Sort(Rule_File_Shell):
    def __init__(self, **kwargs):
        self.reverse = 0
        if 'reverse' in kwargs: self.reverse = kwargs['reverse']
        self.num_sort = 0
        if 'num_sort' in kwargs: self.num_sort = kwargs['num_sort']
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: sort file', self)

    # only take one file to process
    def run(self, files):
        file = files[0]
        self.file_exist(file)
        r = ''
        if self.reverse: r = '-r'
        n = ''
        if self.num_sort: n = '-n'
        cmd = r"sort %s %s %s > %s" % (r, n, file, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class Cut_Lines(Rule_File_Shell):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: get file line from x to y', self)
        self.start = 0
        if 'start' in kwargs: self.start = kwargs['start']
        self.end = 0  # closed end
        if 'end' in kwargs: self.end = kwargs['end']

    # only take one file to process
    def run(self, files):
        file = files[0]
        self.file_exist(file)
        if self.start < 1 or self.end < 1 or self.start > self.end:
            print 'wrong start end line numbers, %d-%d' % (self.start, self.end)
            raise Exception
        cmd = r"sed -n '%d,%dp' %s  > %s" % (self.start, self.end, file, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class Replace_Content(Rule_File_Shell):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: replace content in file', self)
        if 'pattern' in kwargs:
            self.pattern = kwargs['pattern']
        else:
            print "pattern is required as input, check schema"
            raise Exception
        if 'repl' in kwargs:
            self.repl = kwargs['repl']
        else:
            print "repl is required as input, check schema"
            raise Exception

    # only take one file to process
    def run(self, files):
        file = files[0]
        self.file_exist(file)
        cmd = r"sed 's/%s/%s/g' %s > %s" % (self.pattern, self.repl, file, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class Uniq(Rule_File_Shell):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: uniq file', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        cmd = r"uniq %s > %s" % (file, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class Shuffle_Single(Rule_File_Shell):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: shuffle single file', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        cmd = r"shuf %s > %s" % (file, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class Remove_Lines_With_Content(Rule_File_Shell):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: delete lines with specific content', self)
        self.content = ''
        if 'content' in kwargs: self.content = kwargs['content']

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        cmd = r"sed '/%s/d' %s > %s" % (self.content, file, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class Split_To_Twin_Files(Rule_File_Shell):
    def __init__(self, **kwargs):  # delimiter should be single char
        self.delim = ''
        if 'delim' in kwargs: self.delim = kwargs['delim']
        if self.delim: self.delim = '-d%s' % self.delim
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: split single file to twin files according to delim (default is tab)', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        outfile_l = '%s.%s' % (self.output, 'left')
        outfile_r = '%s.%s' % (self.output, 'right')
        cmd = r"cut %s -f1 < %s > %s && cut %s -f2 < %s > %s " % (
            self.delim, file, outfile_l, self.delim, file, outfile_r)
        self.execute_cmd(cmd)
        return [outfile_l, outfile_r]


class Split_To_Twin_Files_v2(Rule_File):
    def __init__(self, **kwargs):
        self.delim = '\t'
        if 'delim' in kwargs: self.delim = kwargs['delim']
        super(self.__class__, self).__init__()
        self.set_desc('File cmd: split single file to twin files according to delim and drop irregular lines', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        outfile_l = '%s.%s' % (self.output, 'left')
        outfile_r = '%s.%s' % (self.output, 'right')
        with codecs.open(file, "r", "utf-8") as i_f:
            with codecs.open(outfile_l, "w", "utf-8") as ol_f:
                with codecs.open(outfile_r, "w", "utf-8") as or_f:
                    for line in i_f:
                        line = line.strip("\r\n")
                        pair = line.split('\t')
                        if len(pair) != 2 or not len(pair[0]) or not len(pair[1]):
                            continue

                        ol_f.write(pair[0] + '\n')
                        or_f.write(pair[1] + '\n')

        return [outfile_l, outfile_r]


class Split_To_Twin_Files_v3(Rule_File):
    def __init__(self, **kwargs):
        self.delim = '\t'
        if 'delim' in kwargs: self.delim = kwargs['delim']
        super(self.__class__, self).__init__()
        self.set_desc('File cmd: split single file to twin files according to delim and drop irregular lines', self)

        self.line_separators = [u'\u2028', u'\u2029']  # Add unicode line separators here
        self.line_separators = [x.encode('utf-8') for x in self.line_separators]
        self.line_separators.extend(['\x0a', '\x0b', '\x0c', '\x0d', '\x1c', '\x1d', '\x1e'])  # Add utf-8 line separators here

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        outfile_l = '%s.%s' % (self.output, 'left')
        outfile_r = '%s.%s' % (self.output, 'right')
        with open(file, "r") as i_f:
            with open(outfile_l, "w") as ol_f:
                with open(outfile_r, "w") as or_f:
                    for line in i_f:
                        line = line.strip()
                        for sep in self.line_separators:
                            line = line.replace(sep, '')

                        pair = line.split('\t')
                        if len(pair) != 2 or not len(pair[0]) or not len(pair[1]):
                            continue

                        ol_f.write(pair[0] + '\n')
                        or_f.write(pair[1] + '\n')

        return [outfile_l, outfile_r]


class Remove_Separator_Symbols(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File cmd: remove the symbol separating line, beside newline ', self)

        self.line_separators = [u'\u2028', u'\u2029']  # Add unicode line separators here
        self.line_separators = [x.encode('utf-8') for x in self.line_separators]
        self.line_separators.extend(['\x0b', '\x0c', '\x0d', '\x1c', '\x1d', '\x1e'])  # Add utf-8 line separators here

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        with open(file, "r") as i_f:
            with open(self.output, "w") as o_f:
                for line in i_f:
                    for sep in self.line_separators:
                        line = line.replace(sep, '')

                    o_f.write(line)

        return [self.output]


class Combine_Twin_Files(Rule_File_Shell):
    def __init__(self, **kwargs):
        self.delim = "\\t"
        if 'delim' in kwargs: self.delim = kwargs['delim']
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: combine twin files to a single file according to delim (default is tab)', self)

    def run(self, files):
        file_l = files[0]
        file_r = files[1]
        self.file_exist(file_l)
        self.file_exist(file_r)
        cmd_part = "{getline f2 < \"%s\"; print $0\"%s\"f2}" % (file_r, self.delim)
        cmd = r"awk '%s' %s > %s" % (cmd_part, file_l, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class Fast_Align(Rule_File_Shell):
    def __init__(self, **kwargs):  # delimiter should be single char
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: fast alignment tool', self)
        self.exe = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'word_alignment', 'fast_align')

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        output_table = "%s.tabel" % self.output
        output_align = "%s.align" % self.output
        cmd = r"chmod 755 %s; %s -i %s -d -o -v -p %s > %s" % (self.exe, self.exe, file, output_table, output_align)
        self.execute_cmd(cmd)
        return [output_table, output_align]


class General_Tokenizer(Rule_File_Shell):
    def __init__(self, **kwargs):  # delimiter should be singlself.exe, e char
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: general tokenizer (same as in Moses)', self)
        self.lang = 'en'
        if 'lang' in kwargs: self.lang = kwargs['lang']
        self.exe = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'tokenizer', 'tokenizer.perl')

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        cmd = r"chmod 755 %s; %s -l %s < %s > %s" % (self.exe, self.exe, self.lang, file, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class General_Tokenizer_v2(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: general tokenizer (same as in Moses), URLs not impacted', self)
        tokenizer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tokenizer', 'tokenizer.perl')
        lang = 'en'
        if 'lang' in kwargs:
            lang = kwargs['lang']
        if 'mode' in kwargs:
            self.mode = kwargs['mode']
        else:
            self.mode = 'script'
        self.tokenizer = MosesTokenizer(lang)
        self.tokenizer_cmd = [tokenizer_path, "-l", lang, "-q", "-"]
        self.url_re = re.compile(ur'https?[:：]//[a-z0-9\-_~\*\'@&=\+\$/\?#]+[a-zA-Z0-9/#]', re.IGNORECASE)

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        with codecs.open(file, 'r', 'utf-8') as in_f:
            with codecs.open(self.output, 'w', 'utf-8') as out_f:
                counter = 0
                for line in in_f:
                    line = line.strip()
                    sentence, en_frags = self._match_frags(line)
                    if self.mode == 'script':
                        sentence = self.tokenize_with_perl(sentence)
                    else:
                        sentence = self.tokenize_with_nlkt_mosestokenizer(sentence)
                    try:
                        en_idx = 0
                        rp_idx = sentence.find('U')
                        while rp_idx >= 0:
                            sentence = sentence[:rp_idx] + en_frags[en_idx] + sentence[rp_idx + 1:]
                            rp_idx = sentence.find('U', rp_idx + len(en_frags[en_idx]))
                            en_idx += 1
                    except:
                        print line

                    result = re.sub(r"\s+", " ", sentence)
                    result = result.strip()

                    out_f.write(result + '\n')

                    counter += 1
                    if counter % 10000 == 0:
                        print 'processed %d lines' % counter

        return [self.output]

    def _match_frags(self, line):
        start = 0
        frags = []
        en_frags = []
        for match in self.url_re.finditer(line):
            frags.append(line[start: match.span()[0]])

            matched_str = line[match.span()[0]: match.span()[1]]
            frags.append('U')
            en_frags.append(matched_str)

            start = match.span()[1]

        last_frag_text = line[start:]
        if last_frag_text:
            frags.append(last_frag_text)

        return ''.join(frags), en_frags

    # todo: this function will later be substituted by tokenize_with_nlkt_mosestokenizer
    def tokenize_with_perl(self, sentence):
        tokenizer = Popen(self.tokenizer_cmd, stdin=PIPE, stdout=PIPE)
        sentence, _ = tokenizer.communicate(sentence)
        return sentence

    def tokenize_with_nlkt_mosestokenizer(self, sentence):
        return self.tokenizer.tokenize(sentence, return_str=True)


class General_Detokenizer(Rule_File_Shell):
    def __init__(self, **kwargs):  # delimiter should be singlself.exe, e char
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: general detokenizer (same as in Moses)', self)
        self.lang = 'en'
        if 'lang' in kwargs: self.lang = kwargs['lang']
        self.exe = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'tokenizer', 'detokenizer.perl')

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        cmd = r"chmod 755 %s; %s -l %s < %s > %s" % (self.exe, self.exe, self.lang, file, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class Bleu(Rule_File_Shell):
    def __init__(self, **kwargs):  # delimiter should be single char
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: BLEU score evaluation (same as Moses), need reference file in schema', self)
        self.ref = ''
        if 'reference' in kwargs:
            self.ref = kwargs['reference']
            self.file_exist(self.ref)
        self.exe = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'bleu', 'multi-bleu.perl')

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        if not self.ref:
            if len(files) > 1:
                self.ref = files[1]
                self.file_exist(self.ref)
            else:
                print 'reference file is required in inputs if it is not passed through \'reference\' arg'
                raise Exception

        cmd = r"chmod 755 %s; %s %s < %s > %s" % (self.exe, self.exe, self.ref, file, self.output)
        # cmd = r"%s %s < %s | tee %s" % (self.exe, self.ref, file, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class BPE_Apply(Rule_File_Shell):
    def __init__(self, **kwargs):  # delimiter should be single char
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: apply BPE codebook to file', self)
        if 'code' in kwargs:
            self.code = kwargs['code']
        else:
            print 'need code file for BPE, check schema'
            raise Exception
        self.exe = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'BPE', 'subword_nmt', 'apply_bpe.py')

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        cmd = r"python %s -c %s -i %s -o %s" % (self.exe, self.code, file, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class Translate_Atman(Rule_File_Shell):
    def __init__(self, **kwargs):  # delimiter should be single char
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: run atman translation script', self)
        self.script = ''
        if 'script' in kwargs:
            self.script = kwargs['script']
        else:
            print 'translation script is required, check schema'
            raise Exception
        if 'model' in kwargs:
            self.model = kwargs['model']
        else:
            print 'model is required, check schema'
            raise Exception
        if 'x_voc' in kwargs:
            self.x_voc = kwargs['x_voc']
        else:
            print 'x_voc is required, check schema'
            raise Exception
        if 'y_voc' in kwargs:
            self.y_voc = kwargs['y_voc']
        else:
            print 'y_voc is required, check schema'
            raise Exception

        self.file_exist(self.script)
        self.script = os.path.abspath(self.script)

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        cmd = r"python %s --infile %s --outfile %s --model %s --x_voc %s --y_voc %s" % \
              (self.script, file, self.output, self.model, self.x_voc, self.y_voc)
        self.execute_cmd(cmd)
        return [self.output]


class Tidy_Translated_Result(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input translated file, recover paragraphs', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        lines = open(file).readlines()
        with open(self.output, 'w') as f:
            p = []
            for l in lines:
                if l != '\n':
                    p.append(l.strip())
                else:
                    f.write(" ".join(p) + '\n\n')
                    p = []

        return [self.output]


class Translate_3rd_Party(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input translated file, recover paragraphs', self)
        self.base_url = 'http://api.atman360.com:3000/api/translate'
        if 'from' not in kwargs:
            print 'no "from" field, check schema'
            raise Exception
        if 'to' not in kwargs:
            print 'no "to" field, check schema'
            raise Exception
        if 'engine' not in kwargs:
            print 'no "engine" field, check schema'
            raise Exception
        self.params = {
            'text': '',
            'from': kwargs['from'],
            'to': kwargs['to'],
            'engine': kwargs['engine']
        }

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        print 'translating doc using %s engine' % self.params['engine']
        lines = codecs.open(file, 'r', 'utf-8').readlines()
        with codecs.open(self.output, 'w', 'utf-8') as f:
            cnt = 0
            for l in lines:
                cnt += 1
                if l == '\n':
                    f.write('\n')
                else:
                    self.params['text'] = l.strip()
                    print 'translating sentence: %s' % l
                    code, retry_cnt = 0, 0
                    while code != 200 and retry_cnt < 3:
                        if retry_cnt > 1: print 'failed %d times, retrying...' % retry_cnt

                        resp = requests.get(self.base_url, self.params)
                        code = resp.status_code
                        retry_cnt += 1

                        time.sleep(0.5)

                    if resp.status_code != 200:
                        print 'error to translate sentence after tried %d times: %s' % (retry_cnt, l)
                        f.write("[ERROR: resp code %s]\n" % resp.status_code)
                    else:
                        j = resp.json()
                        if not j or 'dst' not in j or not j['dst']:
                            f.write("[ERROR: empty response]\n")
                            print 'result: [ERROR: empty response]'
                        else:
                            f.write("%s\n" % j['dst'])
                            print 'result: %s' % j['dst']

                    if cnt % 10 == 0:
                        print 'translated %d sentences' % cnt

        print 'translated all sentences, total %d' % cnt
        return [self.output]


class Select_Input(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input list of files, select one file per input index (start from 0)', self)
        if 'input' in kwargs:
            self.input = kwargs['input']
        else:
            print 'no input for Select_Input, check schema'
            raise Exception

    def run(self, _):
        for f in self.input:
            self.file_exist(f)
        return self.input


class Select_Output(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input list of files, select one file per input index (start from 0)', self)
        self.index = None
        self.select_outputs = None
        if 'index' in kwargs:
            self.index = kwargs['index']
        else:
            print 'no index for Select_Output, check schema'
            raise Exception
        if 'output' in kwargs: self.select_outputs = kwargs['output']
        if self.index and self.select_outputs and len(self.index) != len(self.select_outputs):
            print 'length of index or output mismatch, check schema'
            raise Exception

    def run(self, files):
        outs = []
        if not self.select_outputs:
            for i in self.index:
                if i >= len(files) or i < 0:
                    print 'invalid index, check schema'
                    raise Exception
                outs.append(files[i])
        else:
            for i, out in zip(self.index, self.select_outputs):
                if i >= len(files) or i < 0:
                    print 'invalid index, check schema'
                    raise Exception
                shutil.move(files[i], out)
                outs.append(out)
        return outs


class Statistic_Word_Vocab(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input file, produce vocabulary (format: freq\tword)', self)
        self.skip_words = kwargs["skip_words"] if 'skip_words' in kwargs else None

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        voc = {}
        with codecs.open(file, "r", "utf-8") as f:
            line = f.readline()
            while line:
                words = line.strip().split()
                for w in words:
                    if w in voc:
                        voc[w] += 1
                    else:
                        voc[w] = 1
                line = f.readline()

        if self.skip_words:
            skip_words = set(self.skip_words.split('|'))
        else:
            skip_words = None


        with codecs.open(self.output, "w", "utf-8") as f:
            for w, freq in voc.iteritems():
                if skip_words and w not in skip_words:
                    f.write("%s\t%s\n" % (freq, w))


        return [self.output]


class Statistic_Character_Set(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input file, produce character set (format: freq\tword)', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        voc = {}
        with codecs.open(file, "r", "utf-8") as f:
            i = 0
            line = f.readline()
            while line:
                for w in line:
                    if w in voc:
                        voc[w] += 1
                    else:
                        voc[w] = 1
                line = f.readline()
                i += 1
                if i % 500000 == 0:
                    print 'processed %d lines' % i

        with codecs.open(self.output, "w", "utf-8") as f:
            for w, freq in voc.iteritems():
                # f.write("%s\t%s\n" % (w, freq))
                f.write("%s\t%s\n" % (freq, w))

        return [self.output]


class Translate_Atman_By_Shell(Rule_File_Shell):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Translate Atman by shell', self)
        if 'shell_script' in kwargs: self.script = kwargs['shell_script']

    def run(self, file):
        cmd = r'sh %s %s %s' % (self.script, file[0], self.output)
        self.execute_cmd(cmd)
        return [self.output]


class Insert_Line(Rule_File_Shell):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File Shell cmd: insert content on specific line', self)
        self.line_num = 1
        if 'line_num' in kwargs: self.line_num = kwargs['line_num']
        self.content = ''
        if 'content' in kwargs: self.content = kwargs['content']

    # only take one file to process
    def run(self, files):
        file = files[0]
        self.file_exist(file)
        if self.line_num < 1:
            print 'wrong line numbers, %d' % self.line_num
            raise Exception
        cmd = r"sed '%di%s' %s > %s" % (self.line_num, self.content, file, self.output)
        self.execute_cmd(cmd)
        return [self.output]


class Words_To_Tokens(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input file and voc, convert words to ids', self)

    def run(self, files):  # need to take two files: first is sentence file, second is w2i file
        if len(files) != 2:
            print 'need 2 input files, current: %s, check schema' % files
            raise Exception
        sen_f = files[0]
        w2i_f = files[1]
        self.file_exist(sen_f)
        self.file_exist(w2i_f)

        d = {}
        with codecs.open(w2i_f, "r", "utf-8") as f:
            lines = f.readlines()
            for i, l in enumerate(lines):
                d[l.strip()] = i

        with codecs.open(sen_f, "r", "utf-8") as i_f:
            with codecs.open(self.output, "w", "utf-8") as o_f:
                line = i_f.readline()
                cnt = 0
                while line:
                    cnt += 1
                    if cnt % 100000 == 0:
                        print 'converted %d lines to ids' % cnt
                    words = line.strip().split()
                    t = [str(d.get(w, d['_UNK'])) for w in words]
                    o_f.write(" ".join(t) + '\n')
                    line = i_f.readline()

        return [self.output]


class Words_To_Tokens_V2(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input file and voc, convert words to ids', self)
        self.voc = None
        if 'voc' not in kwargs:
            print "need to have a voc passed in"
            raise Exception
        else:
            self.voc = kwargs["voc"]

    def run(self, files):  # need to take two files: first is sentence file, second is w2i file
        sen_f = files[0]
        w2i_f = self.voc
        self.file_exist(sen_f)
        self.file_exist(w2i_f)

        d = {}
        with codecs.open(w2i_f, "r", "utf-8") as f:
            lines = f.readlines()
            for i, l in enumerate(lines):
                d[l.strip()] = i

        with codecs.open(sen_f, "r", "utf-8") as i_f:
            with codecs.open(self.output, "w", "utf-8") as o_f:
                line = i_f.readline()
                cnt = 0
                while line:
                    cnt += 1
                    if cnt % 100000 == 0:
                        print 'converted %d lines to ids' % cnt
                    words = line.strip().split()
                    t = [str(d.get(w, d['_UNK'])) for w in words]
                    o_f.write(" ".join(t) + '\n')
                    line = i_f.readline()

        return [self.output]


class Tokens_To_Words(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input file and voc, convert ids to words', self)

    def run(self, files):  # need to take two files: first is sentence file, second is w2i file
        if len(files) != 2:
            print 'need 2 input files, current: %s, check schema' % files
            raise Exception
        sen_f = files[0]
        w2i_f = files[1]
        self.file_exist(sen_f)
        self.file_exist(w2i_f)

        d = []
        with codecs.open(w2i_f, "r", "utf-8") as f:
            lines = f.readlines()
            for i, l in enumerate(lines):
                d.append(l.strip())

        with codecs.open(sen_f, "r", "utf-8") as i_f:
            with codecs.open(self.output, "w", "utf-8") as o_f:
                cnt = 0
                for line in i_f:
                    cnt += 1
                    if cnt % 100000 == 0:
                        print 'converted %d lines to words' % cnt
                    ids = line.strip().split()
                    words = [d[int(id)] for id in ids]
                    o_f.write(" ".join(words) + '\n')

        return [self.output]


class WordProb_To_PKL(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from word prob file, convert to pkl for easy use in future', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        lm_dict = {}
        tmp_dict = {}
        with open(file, 'r') as f:
            line = f.readline()
            while line:
                parsed = line.split('\t')
                lw = parsed[0]
                rw = parsed[1]
                sc = parsed[2]

                if lw not in tmp_dict:
                    tmp_dict[lw] = {}
                    tmp_dict[lw][rw] = pow(np.e, float(sc))
                else:
                    if rw in tmp_dict[lw]:
                        print 'dup rw %s in lw %s' % (rw, lw)
                    tmp_dict[lw][rw] = pow(np.e, float(sc))

                line = f.readline()

            for k, dt in tmp_dict.iteritems():
                lm_dict[k] = sorted(dt, key=dt.get)[::-1]

        print 'saving lm dict file (format: word->[word1, word2...])'
        cPickle.dump(lm_dict, open(self.output, 'w'))

        return [self.output]


class WordProb_To_PKL_v2(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from word prob file, convert to pkl for easy use in future. Keep probs.', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        tmp_dict = {}
        with open(file, 'r') as f:
            for line in f:
                parsed = line.split('\t')
                lw = parsed[0]
                rw = parsed[1]
                sc = parsed[2]

                if lw not in tmp_dict:
                    tmp_dict[lw] = {}
                    tmp_dict[lw][rw] = pow(np.e, float(sc))
                else:
                    if rw in tmp_dict[lw]:
                        print 'dup rw %s in lw %s' % (rw, lw)
                    tmp_dict[lw][rw] = pow(np.e, float(sc))

        print 'saving lm dict file (format: word->[word1:prob1, word2:prob2, ...])'
        cPickle.dump(tmp_dict, open(self.output, 'w'))

        return [self.output]


class WordList_To_PKL(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from word list file, convert to pkl for easy use in future', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        words = []
        with open(file, 'r') as f:
            lines = f.readlines()
            for l in lines:
                l = l.strip()
                words.append(l)

        cPickle.dump(words, open(self.output, 'w'))

        return [self.output]


class Group_Lines_With_Tags_If_Exist(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input files and tags, group them into one file line by line', self)
        if 'tags' not in kwargs or len(kwargs['tags']) < 1:
            print 'no valid tags found, check schema'
            raise Exception
        self.tags = kwargs['tags']

    @staticmethod
    def get_file_line_num(f):
        n = sum(1 for _ in f.read().strip().split('\n'))  # need to exclude heading/tailing empty lines
        f.seek(0)
        return n

    @staticmethod
    def close_all(f_list):
        for t in f_list:
            t.close()

    def run(self, files):
        if len(files) < 2:
            print 'need at least 2 files for this rule'
            raise Exception
        if len(files) != len(self.tags):
            print 'need same number of files with tags, check schema'
            raise Exception
        ff, tt = [], []
        for f, t in zip(files, self.tags):
            if os.path.exists(f):
                ff.append(f)
                tt.append(t)
        if len(ff) < 2:
            print 'need at least 2 files for this rule'
            raise Exception
        else:
            files = ff
            self.tags = tt

        with open(files[0], 'r') as src:
            l_num_src = self.get_file_line_num(src)
            with open(self.output, 'w') as out:
                tgt_list = []
                for t in files[1:]:
                    f = open(t, 'r')
                    tgt_list.append(f)
                    if l_num_src != self.get_file_line_num(f):
                        print("line number not consistant of src and tgt file %s", f.name)
                        self.close_all(tgt_list)
                        raise Exception

                for i in xrange(l_num_src):
                    line = src.readline()
                    if line == '\n':
                        for f in tgt_list:
                            f.readline()
                        continue
                    out.write(self.tags[0])
                    out.write(line)
                    for k, f in enumerate(tgt_list):
                        out.write("%s" % self.tags[k + 1])
                        out.write(f.readline())
                    out.write("\n")

                self.close_all(tgt_list)

        return [self.output]


class Translate_Atman_HTTP(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input file, use Atman HTTP API to translate', self)
        if 'baseurl' in kwargs:
            self.baseurl = kwargs['baseurl']
        else:
            print 'baseurl is required, check schema'
            raise Exception

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        avg_per = avg_loss = 0
        text = open(file).read()
        if not text:
            print "empty content in file %s" % file
            ret = "[empty input content]"
        else:
            resp = None
            cnt = 0
            while cnt < 3:
                cnt += 1
                try:
                    resp = requests.post(self.baseurl,
                                         {
                                             "text": text,
                                             "processed": 1
                                         })
                    break
                except Exception, e:
                    traceback.print_exc(e)
                    print 'retrying...'

            if not resp: raise Exception
            j = resp.json()
            ret, avg_per, avg_loss = j['result'], j['avg_per'], j['avg_loss']

        ret_f, score_f = self.output + "ret", self.output + "score"
        with open(ret_f, 'w') as o:
            o.write(ret)
        with open(score_f, 'w') as o:
            o.write("average_perplexity:%.5f\taverage_loss:%.5f" % (avg_per, avg_loss))
        return [ret_f, score_f]


class Extract_Text_From_Raw_Doc(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input file, split doc and meta', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        with open(file, 'r') as f:
            data = json.load(f)

        # valid
        new_data = {}
        if 'original_doc' not in data:
            # print 'invalid json file field, check your input json file'
            # raise Exception

            new_data['original_doc'] = data
        else:
            new_data = data

        with open(self.output, 'w') as f:
            f.write("\n".join(new_data['original_doc']['paragraphs']))

        meta_file = self.output + ".meta"
        with open(meta_file, 'w') as f:
            json.dump(new_data, f)

        return [self.output, meta_file]


class Create_ES_Data_Type_transdoc(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from input files, create final ES transdoc type json data', self)
        self.processed_method = "unknow"
        if 'processed_method' in kwargs: self.processed_method = kwargs['processed_method']

    def run(self, files):
        origin_f = files[0]
        self.file_exist(origin_f)
        processed_f = files[1]
        self.file_exist(processed_f)

        with open(origin_f, 'r') as f:
            all = json.load(f)

        all['processed_doc'] = dict(
            processed_method=self.processed_method,
            date=datetime.datetime.now().isoformat(),
            paragraphs=[]
        )

        paragraphs = []
        with open(processed_f, 'r') as f:
            lines = f.readlines()
            sens = []
            for l in lines:
                if l != '\n':
                    sens.append(l)
                else:
                    if len(sens) > 0:
                        paragraphs.append({"sentences": sens})
                        sens = []

        all['processed_doc']['paragraphs'] = paragraphs

        with open(self.output, 'w') as f:
            json.dump(all, f)

        return [self.output]


class Index_to_ElasticSearch(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: push input json to ES index', self)
        if 'host' not in kwargs or 'index' not in kwargs or 'type' not in kwargs:
            print 'host, index or type not found, check schema'
            raise Exception
        self.host = kwargs['host']
        self.index = kwargs['index']
        self.type = kwargs['type']
        self.es = es.Elasticsearch(
            [self.host],
        )

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        with open(file, 'r') as f:
            data = json.load(f)

        id = base64.urlsafe_b64encode(data['original_doc']['source'])
        res = self.es.index(index=self.index, doc_type=self.type, id=id, body=data, request_timeout=600)

        with open(self.output, 'w') as f:
            json.dump(res, f)

        return [self.output]


class Create_ES_Index_If_No_Exists(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: create ES index and set mapping if not exist', self)
        if 'host' not in kwargs or 'index' not in kwargs or 'type' not in kwargs:
            print 'host, index or type not found, check schema'
            raise Exception
        self.host = kwargs['host']
        self.index = kwargs['index']
        self.type = kwargs['type']
        self.es = es.Elasticsearch(
            [self.host]
        )

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        with open(file, 'r') as f:
            mapping = json.load(f)

        if self.index in self.es.indices.get_aliases():
            print 'index %s already exists, skip creating new...' % self.index
            with open(self.output, 'w') as f:
                f.write("skip\n")
            return [self.output]

        res = self.es.indices.create(index=self.index, body=dict(
            mappings=mapping,
            settings=dict(
                number_of_shards=5,
                number_of_replicas=1
            )
        ))

        with open(self.output, 'w') as f:
            json.dump(res, f)

        return [self.output]


class BD_Break(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: break word to character according to a voc', self)
        if 'voc' not in kwargs:
            print 'voc not found, check schema'
            raise Exception
        self.voc = kwargs['voc']
        self.entity_safe = False
        if kwargs['entity_safe']:
            if kwargs['entity_safe'].lower() == 'true':
                self.entity_safe = True

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        dic = set()
        with codecs.open(self.voc, 'r', 'utf-8') as f:
            lines = f.readlines()
            for l in lines:
                dic.add(l.strip())

        with codecs.open(file, 'r', 'utf-8') as i_f:
            with codecs.open(self.output, 'w', 'utf-8') as o_f:
                i = 0
                for l in i_f:
                    o_f.write(self.convert_line_to_mixed_wc(l, dic) + '\n')
                    i += 1
                    if i % 500000 == 0:
                        print 'processed %d lines' % i

        return [self.output]

    def convert_word_to_chars(self, word):
        new_words = []
        w_len = len(word)
        for i in xrange(w_len):
            if i == 0:
                prefix = '<B>'
            elif i == w_len - 1:
                prefix = '<E>'
            else:
                prefix = '<M>'
            new_words.append(prefix + word[i])

        # print '%s => %s' % (word, new_words)
        return new_words

    def convert_line_to_mixed_wc(self, line, dic):
        words = line.split()
        new_words = []
        for w in words:
            if w not in dic:
                if self.entity_safe and w.startswith('<') and w.endswith('>') and ':' in w:
                    new_words.append(w)
                else:
                    new_words.extend(self.convert_word_to_chars(w))
            else:
                new_words.append(w)
        return " ".join(new_words)


class Create_Orig_Json_From_Text(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from txt file to json doc with dummy meta', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        with open(file) as f:
            lines = f.readlines()

        paragraphs_data = []
        for l in lines:
            if l != '\n':
                paragraphs_data.append(l)

        all = dict(
            original_doc=dict(
                source=os.path.basename(file),
                lang="en",
                categories=["finance", "news"],
                tags=[""],
                date=datetime.datetime.now().isoformat(),
                structured_content=dict(
                    title="",  # TBD
                    author="",  # TBD
                    publication_date=datetime.date(1900, 1, 1).isoformat(),
                ),
                paragraphs=paragraphs_data
            )
        )

        with open(self.output, 'w') as f:
            json.dump(all, f)

        return [self.output]


class Remove_Length_Not_Balanced_Pair(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: pairs with not balanced length', self)
        self.mix_ratio = 0.5
        self.max_ratio = 2.0
        self.left_mode = 'word'
        self.right_mode = 'word'
        if 'min_ratio' in kwargs: self.min_ratio = float(kwargs['min_ratio'])
        if 'max_ratio' in kwargs: self.max_ratio = float(kwargs['max_ratio'])
        if 'left_mode' in kwargs: self.left_mode = kwargs['left_mode']
        if 'right_mode' in kwargs: self.right_mode = kwargs['right_mode']

    def sentence_char_number(self, sentence):
        chars = []
        sen_phrases = sentence.split()
        for phrase in sen_phrases:
            if not len(phrase): continue
            if not is_chinese(phrase[0]):
                chars.append(phrase)
            else:
                for c in phrase:
                    chars.append(c)
        return len(chars)

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        with codecs.open(file, 'r' 'utf-8') as i_f:
            with codecs.open(self.output, 'w', 'utf-8') as o_f:
                with codecs.open(self.output + '.unbalanced_removed', 'w', 'utf-8') as r_f:
                    line = i_f.readline()
                    i = 0
                    while line:
                        pair = line.rstrip().split('\t')
                        if not pair or len(pair) != 2:
                            r_f.write(line)

                        if self.left_mode == 'char':
                            l_len = self.sentence_char_number(pair[0].decode('utf-8'))
                        else:
                            l_len = len(pair[0].split())

                        if self.right_mode == 'char':
                            r_len = self.sentence_char_number(pair[1].decode('utf-8'))
                            # print pair[1]
                            # print r_len
                        else:
                            r_len = len(pair[1].split())

                        if r_len < l_len * self.min_ratio or r_len > l_len * self.max_ratio:
                            r_f.write(line)
                        else:
                            o_f.write(line)

                        line = i_f.readline()
                        i += 1
                        if i % 500000 == 0:
                            print 'processed %d lines' % i

        return [self.output]


class Filter_Sentence_With_Illegal_Chars(Rule_File):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Remove lines with illegal chars', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        keep_file = self.output + '.good'
        remove_file = self.output + '.bad'
        with open(file, 'r') as i_f:
            with open(keep_file, 'w') as o_f:
                with open(remove_file, 'w') as r_f:
                    i = 0
                    for line in i_f:
                        sentence = line.decode('utf-8').strip()
                        if self.check_chars(sentence):
                            o_f.write(line)
                        else:
                            r_f.write(line)

                        i += 1
                        if i % 100000 == 0:
                            print 'processed %d lines' % i

        return [keep_file, remove_file]

    def check_chars(self, line):
        if is_contain_ms_special_character(line):
            print 'Remove line: %s' % line
            return False
        for char in line:
            if char in ' \t\r\n' \
                    or is_ascii_printable(char) \
                    or is_ascii_supplement(char) \
                    or is_chinese(char) \
                    or is_chinese_punctuation(char) \
                    or is_latin_extended_a(char) \
                    or is_latin_extended_b(char) \
                    or is_greek_or_coptic(char) \
                    or is_general_punctuation(char) \
                    or is_superscript_or_subscript(char) \
                    or is_currency_symbol(char) \
                    or is_letterlike_symbol(char) \
                    or is_number_form(char) \
                    or is_math_operator(char) \
                    or is_enclosed_alphanumeric(char) \
                    or is_math_operator_supplement(char) \
                    or is_enclosed_cjk_letter(char) \
                    or is_cjk_compatibility(char) \
                    or is_halfwidth_or_fullwidth(char):
                continue
            else:
                print 'Remove line: %s' % line
                return False

        return True


class Pre_Replacing_Rule(Rule):
    def __init__(self, bifrost_instance):
        super(self.__class__, self).__init__()
        self.set_desc('Pre_Replacing_Rule: ', self)
        self.bifrost = bifrost_instance

    def run(self, line):
        return self.bifrost.pre_process(line)


class Post_Replacing_Rule(Rule):
    def __init__(self, bifrost_instance):
        super(self.__class__, self).__init__()
        self.set_desc('Post_Replacing_Rule: ', self)
        self.bifrost = bifrost_instance

    def run(self, line):
        return self.bifrost.post_process(line)


class BPE_Apply_Line(Rule):
    def __init__(self, bpe_instance):
        super(self.__class__, self).__init__()
        self.set_desc('Line: break word to character according to a voc', self)
        self.bpe = bpe_instance

    def run(self, line):
        if not line:
            return None

        return self.bpe.segment(line).strip()
