# -*- coding: utf-8 -*-
from rule import *
import rule_common as common
import re
import jieba
import codecs
import base64
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from zh_conversion import convtable


class Remove_Bullet(Rule_Line):
    def __init__(self):
        re_s = []
        t = r"^((\d+|[xiv]+|[a-f－・•￭■□♦◦●○◊►√∗*＊②③]|[一二三四五六七八九十百]+)\s?(\.|、)|(\(|（|【)?\s?(\d+|[xiv]+|[a-f]|[一二三四五六七八九十百]+)\s?(\)|）|】)\s?(\.|、)?|((\d+|[a-z]+)\.)+(\d+|[a-z]+)\.?)"
        re_s.append((t, re.IGNORECASE, ""))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove bullets', self)


class Remove_Bullet_v2(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Remove Chinese bullets', self)

    def run(self, line):
        if not line:
            return None
        line = line.strip()

        ignore_first_re = False
        m = re.match(r'\d+\.', line)
        if m and m.span()[1] < len(line):
            next_char = line[m.span()[1]]
            if next_char >= '0' and next_char <= '9':
                ignore_first_re = True

        if not ignore_first_re:
            line = re.sub(r'^((\d+|[xiv]+|[a-f]|[一二三四五六七八九十百]+)(\.|、)|(\(|（|【)?(\d+|[xiv]+|[a-f]|[一二三四五六七八九十百]+)(\)|）|】)|((\d+|[a-z]+)\.)+(\d+|[a-z]+)\.?)'.decode('utf-8'), '', line, flags=re.IGNORECASE)

        if line:
            line = re.sub(r'^[－・•￭■□♦◦●○◊►√∗*＊①②③④⑤⑥⑦⑧⑨⑩ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩]'.decode('utf-8'), '', line)

        return line


class Remove_Punctuation(Rule_Line):
    def __init__(self):
        re_s = [(r"'|\"|-|—|“|”|《|》", re.IGNORECASE, " ")]
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove punctuations', self)


class Remove_Punctuation_v2(Rule_Line):
    def __init__(self):
        re_s = [(r"\"| - |—|“|”|《|》", re.IGNORECASE, " ")]
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove punctuations V2', self)


class Replace_English_Punctuation(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.init_dict()
        self.set_desc('Replace English punctuations with the corresponding Chinese ones.', self)

    def init_dict(self):
        keys = [u'!', u'(', u')', u',', u':', u';', u'?', u'~']
        values = [u'！', u'（', u'）', u'，', u'：', u'；', u'？', u'～']

        self.dict = dict(zip(keys, values))

    def run(self, line):
        if not line:
            return None

        new_line = []
        for w in line.strip():
            new_line.append(self.dict.get(w, w))

        line = ''.join(new_line)
        line = line.replace(u'...', u'……')
        return line


class Remove_Not_Contain_Chinese(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Remove lines that do not contain any Chinese character', self)

    def run(self, line):
        if not line or not common.contains_chinese(line):
            return None
        return line


class Convert_Traditional_To_Simplified(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Convert all traditional Chinese chars to the corresponding simplified chinese ones', self)

    def run(self, line):
        if not line:
            return None

        new_chars = []
        for c in line:
            if c in convtable.trad2simp:
                new_chars.append(convtable.trad2simp[c])
            else:
                new_chars.append(c)

        return ''.join(new_chars)


class Dedupe_Repeated_Punctuation(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((ur'，{2,}', f, u"，"))
        re_s.append((ur'。{2,}', f, u"。"))
        re_s.append((ur'？{2,}', f, u"？"))
        re_s.append((ur'！{2,}', f, u'！'))
        re_s.append((ur'；{2,}', f, u'；'))
        re_s.append((ur'：{2,}', f, u'：'))
        re_s.append((ur'“{2,}', f, u'“'))
        re_s.append((ur'”{2,}', f, u'”'))
        re_s.append((ur'‘{2,}', f, u'‘'))
        re_s.append((ur'’{2,}', f, u'’'))
        re_s.append((ur'、{2,}', f, u'、'))
        re_s.append((ur'·{2,}', f, u'·'))
        re_s.append((ur'（{2,}', f, u'（'))
        re_s.append((ur'）{2,}', f, u'）'))
        re_s.append((ur'—{2,}', f, u'—'))
        re_s.append((ur'–{2,}', f, u'–'))  # En dash
        re_s.append((ur'—{2,}', f, u'—'))  # Em dash
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Dedupe the repeated Chinese punctuations', self)


class Slot_Tag_Number(Rule_Line):
    '''
    Basic rule for number slot tagging in training data generation.
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Number slot tagging', self)
        self.zh_month_tag = "ZH_M"

        self.number_tag = "N"
        if "number_tag" in kwargs:
            self.number_tag = kwargs["number_tag"]

    def match_frags(self, frag, reg):
        if frag[1]:
            line = frag[0]
            start = 0
            frags = []
            for match in reg[0].finditer(line):
                frags.append((line[start: match.span()[0]], True))

                if reg[1] == self.number_tag:
                    frags.append((reg[1], False))
                elif reg[1] == self.zh_month_tag:
                    matched_str = line[match.span()[0]: match.span()[1]]
                    frags.append((matched_str, False))

                start = match.span()[1]

            last_frag_text = line[start:]
            if last_frag_text:
                frags.append((last_frag_text, True))

            return frags

        else:
            return [frag]

    def slot_tag(self, line, reg_list):
        frags = [(line, True)]
        for reg in reg_list:
            new_frags = []
            for frag in frags:
                sub_frags = self.match_frags(frag, reg)
                new_frags.extend(sub_frags)
            frags = new_frags

        texts = []
        for frag in frags:
            text = frag[0]
            texts.append(text)

        return " ".join(texts)

    def run(self, line):
        Zh_Reg_List = [
            (r'\d+\s*月', self.zh_month_tag),  # Special case, not replace the num before "月"
            (r'\b\d{1,3}(,\d{3})+(\.\d+)?\b', self.number_tag),  # Strict format number
            (r'\b\d{1,3}( \d{3})+(\.\d+)?\b', self.number_tag),  # Strict format number
            (r'\b\d+(\.\d+)?\b', self.number_tag)  # Arbitrary format number
        ]
        Zh_Reg_List = [(re.compile(r[0].decode('utf-8'), re.IGNORECASE), r[1]) for r in Zh_Reg_List]
        return self.slot_tag(line, Zh_Reg_List)


class Slot_Tag_Number_v2(Rule_Line):
    '''
    Number slot tagging in training data generation.
    Integers under 1000 won't be tagged.
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Number slot tagging', self)

        self.number_tag = "N"
        if "number_tag" in kwargs:
            self.number_tag = kwargs["number_tag"]

    def match_frags(self, frag, reg):
        if frag[1]:
            line = frag[0]
            start = 0
            frags = []
            for match in reg[0].finditer(line):
                frags.append((line[start: match.span()[0]], True))

                matched_str = line[match.span()[0]: match.span()[1]]
                if re.match(r'^\d{1,3}$', matched_str):  # ignore integer less than 1000
                    frags.append((matched_str, False))
                else:
                    frags.append((reg[1], False))

                start = match.span()[1]

            last_frag_text = line[start:]
            if last_frag_text:
                frags.append((last_frag_text, True))

            return frags

        else:
            return [frag]

    def slot_tag(self, line, reg_list):
        frags = [(line, True)]
        for reg in reg_list:
            new_frags = []
            for frag in frags:
                sub_frags = self.match_frags(frag, reg)
                new_frags.extend(sub_frags)
            frags = new_frags

        texts = []
        for frag in frags:
            text = frag[0]
            texts.append(text)

        return " ".join(texts)

    def run(self, line):
        Zh_Reg_List = [
            (r'\b\d{1,3}(,\d{3})+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), self.number_tag),  # Strict format num
            (r'\b\d{1,3}( \d{3})+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), self.number_tag),  # Strict format num
            (r'\b\d+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), self.number_tag),  # Arbitrary format num
            (r'\b\d{1,3}(,\d{3})+(\.\d+)?\b'.decode('utf-8'), self.number_tag),  # Strict format num
            (r'\b\d{1,3}( \d{3})+(\.\d+)?\b'.decode('utf-8'), self.number_tag),  # Strict format num
            (r'\b\d+(\.\d+)?\b'.decode('utf-8'), self.number_tag)  # Arbitrary format num
        ]

        Zh_Reg_List = [(re.compile(r[0].decode('utf-8'), re.IGNORECASE), r[1]) for r in Zh_Reg_List]
        return self.slot_tag(line, Zh_Reg_List)


class Slot_Tag_Number_v3(Rule_Line):
    '''
    Number slot tagging in decoding.
    Integers under 1000 won't be tagged.
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Number slot tagging', self)

        self.number_tag = "N"
        if "number_tag" in kwargs:
            self.number_tag = kwargs["number_tag"]

    def match_frags(self, frag, reg):
        if frag[1]:
            line = frag[0]
            start = 0
            frags = []
            for match in reg[0].finditer(line):
                frags.append((line[start: match.span()[0]], True))

                matched_str = line[match.span()[0]: match.span()[1]]
                if reg[1] == 'N':
                    if re.match(r'^\d{1,3}$', matched_str):  # ignore integer under 1000
                        frags.append((matched_str, False))
                    else:
                        tag = self.number_tag.strip('<>')
                        frags.append(('<{}>{}</{}>'.format(tag, base64.b16encode(matched_str), tag), False))
                elif reg[1] == 'E':
                    frags.append((matched_str, False))

                start = match.span()[1]

            last_frag_text = line[start:]
            if last_frag_text:
                frags.append((last_frag_text, True))

            return frags

        else:
            return [frag]

    def slot_tag(self, line, reg_list):
        frags = [(line, True)]
        for reg in reg_list:
            new_frags = []
            for frag in frags:
                sub_frags = self.match_frags(frag, reg)
                new_frags.extend(sub_frags)
            frags = new_frags

        texts = []
        for frag in frags:
            text = frag[0]
            texts.append(text)

        return " ".join(texts)

    def run(self, line):
        Zh_Reg_List = [
            (r'<([A-Za-z]+)>[^<]+</\1>', 'E'),
            (r'\b\d{1,3}(,\d{3})+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), 'N'),  # Strict format num
            (r'\b\d{1,3}( \d{3})+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), 'N'),  # Strict format num
            (r'\b\d+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), 'N'),  # Arbitrary format num
            (r'\b\d{1,3}(,\d{3})+(\.\d+)?\b'.decode('utf-8'), 'N'),  # Strict format num
            (r'\b\d{1,3}( \d{3})+(\.\d+)?\b'.decode('utf-8'), 'N'),  # Strict format num
            (r'\b\d+(\.\d+)?\b'.decode('utf-8'), 'N')  # Arbitrary format num
        ]

        Zh_Reg_List = [(re.compile(r[0].decode('utf-8'), re.IGNORECASE), r[1]) for r in Zh_Reg_List]
        return self.slot_tag(line, Zh_Reg_List)


class Slot_Tag_Number_v4(Rule_Line):
    '''
    Number slot tagging in training data generation.
    Only numbers with '万/亿' will be tagged.
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Number slot tagging', self)

        self.number_tag = "N"
        if "number_tag" in kwargs:
            self.number_tag = kwargs["number_tag"]

    def match_frags(self, frag, reg):
        if frag[1]:
            line = frag[0]
            start = 0
            frags = []
            for match in reg[0].finditer(line):
                frags.append((line[start: match.span()[0]], True))

                frags.append((reg[1], False))

                start = match.span()[1]

            last_frag_text = line[start:]
            if last_frag_text:
                frags.append((last_frag_text, True))

            return frags

        else:
            return [frag]

    def slot_tag(self, line, reg_list):
        frags = [(line, True)]
        for reg in reg_list:
            new_frags = []
            for frag in frags:
                sub_frags = self.match_frags(frag, reg)
                new_frags.extend(sub_frags)
            frags = new_frags

        texts = []
        for frag in frags:
            text = frag[0]
            texts.append(text)

        return " ".join(texts)

    def run(self, line):
        Zh_Reg_List = [
            (r'\b\d{1,3}(,\d{3})+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), self.number_tag),  # Strict format num
            (r'\b\d{1,3}( \d{3})+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), self.number_tag),  # Strict format num
            (r'\b\d+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), self.number_tag),  # Arbitrary format num
        ]

        Zh_Reg_List = [(re.compile(r[0].decode('utf-8'), re.IGNORECASE), r[1]) for r in Zh_Reg_List]
        return self.slot_tag(line, Zh_Reg_List)


class Slot_Tag_Number_v5(Rule_Line):
    '''
    Number slot tagging in decoding.
    Only numbers with '万/亿' will be tagged.
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Number slot tagging', self)

        self.number_tag = "N"
        if "number_tag" in kwargs:
            self.number_tag = kwargs["number_tag"]

    def match_frags(self, frag, reg):
        if frag[1]:
            line = frag[0]
            start = 0
            frags = []
            for match in reg[0].finditer(line):
                frags.append((line[start: match.span()[0]], True))

                matched_str = line[match.span()[0]: match.span()[1]]
                if reg[1] == 'N':
                    tag = self.number_tag.strip('<>')
                    frags.append(('<{}>{}</{}>'.format(tag, base64.b16encode(matched_str), tag), False))
                elif reg[1] == 'E':
                    frags.append((matched_str, False))

                start = match.span()[1]

            last_frag_text = line[start:]
            if last_frag_text:
                frags.append((last_frag_text, True))

            return frags

        else:
            return [frag]

    def slot_tag(self, line, reg_list):
        frags = [(line, True)]
        for reg in reg_list:
            new_frags = []
            for frag in frags:
                sub_frags = self.match_frags(frag, reg)
                new_frags.extend(sub_frags)
            frags = new_frags

        texts = []
        for frag in frags:
            text = frag[0]
            texts.append(text)

        return " ".join(texts)

    def run(self, line):
        Zh_Reg_List = [
            (r'<([A-Za-z]+)>[^<]+</\1>', 'E'),
            (r'\b\d{1,3}(,\d{3})+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), 'N'),  # Strict format num
            (r'\b\d{1,3}( \d{3})+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), 'N'),  # Strict format num
            (r'\b\d+(\.\d+)?\s*(万亿|万|亿)'.decode('utf-8'), 'N'),  # Arbitrary format num
        ]

        Zh_Reg_List = [(re.compile(r[0].decode('utf-8'), re.IGNORECASE), r[1]) for r in Zh_Reg_List]
        return self.slot_tag(line, Zh_Reg_List)


class Separate_Chinese_Char(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Separate Chinese characters with each other and other characters', self)

    def run(self, line):
        if not line:
            return None

        sentence = line.strip()
        sen_phrases = sentence.split(" ")
        new_phrases = []
        for phrase in sen_phrases:
            if not len(phrase):
                continue

            if len(phrase) == 1:
                new_phrases.append(phrase)
                continue

            new_phrase = ''
            for c in phrase:
                if common.is_chinese(c) or common.is_chinese_punctuation(c):
                    if new_phrase:
                        new_phrases.append(new_phrase)
                        new_phrase = ''

                    new_phrases.append(c)
                else:
                    new_phrase += c

            if new_phrase:
                new_phrases.append(new_phrase)

        return " ".join(new_phrases)


class Recover_Separated_Chinese_Char(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Recover separated Chinese characters from rule Separate_Chinese_Char', self)

    def run(self, line):
        if not line:
            return None

        sentence = line.strip()
        sen_phrases = sentence.split(" ")
        new_sentence = ''
        last_is_chinese = True
        for phrase in sen_phrases:
            if not len(phrase):
                continue

            if len(phrase) > 1:
                if not last_is_chinese:
                    new_sentence += ' '

                new_sentence += phrase
                last_is_chinese = False
                continue

            if common.is_chinese(phrase) or common.is_chinese_punctuation(phrase):
                new_sentence += phrase
                last_is_chinese = True
            else:
                if not last_is_chinese:
                    new_sentence += ' '

                new_sentence += phrase
                last_is_chinese = False

        return new_sentence


class Seg_Chinese_Only_In_Sentence(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Segment Chinese sentence, the English sub-strings will not be impacted', self)

    def run(self, line):
        if not line:
            return None

        line = line.strip()
        sentence, en_frags = self._match_frags(line, re.compile(u'[!-~]+'))  # ascii printable characters (except the space \x20)
        seg_list = jieba.cut(sentence, cut_all=False)
        sentence = " ".join(seg_list)

        try:
            en_idx = 0
            rp_idx = sentence.find('E')
            while rp_idx >= 0:
                sentence = sentence[:rp_idx] + en_frags[en_idx] + sentence[rp_idx + 1:]
                rp_idx = sentence.find('E', rp_idx + len(en_frags[en_idx]))
                en_idx += 1
        except:
            print line

        result = re.sub(r"\s+", " ", sentence)
        result = result.strip()

        return result

    def _match_frags(self, line, reg):
        start = 0
        frags = []
        en_frags = []
        for match in reg.finditer(line):
            frags.append(line[start: match.span()[0]])

            matched_str = line[match.span()[0]: match.span()[1]]
            frags.append('E')
            en_frags.append(matched_str)

            start = match.span()[1]

        last_frag_text = line[start:]
        if last_frag_text:
            frags.append(last_frag_text)

        return ''.join(frags), en_frags


class Seg_Chinese_Only(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: Segment Chinese sentences, the English sub-string will not be impacted', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        with codecs.open(file, 'r', 'utf-8') as in_f:
            with codecs.open(self.output, 'w', 'utf-8') as out_f:
                cnt = 0
                for line in in_f:
                    line = line.strip()
                    sentence, en_frags = self._match_frags(line, re.compile(u'[!-~]+'))  # ascii printable characters (except the space \x20)
                    seg_list = jieba.cut(sentence, cut_all=False)
                    sentence = " ".join(seg_list)

                    try:
                        en_idx = 0
                        rp_idx = sentence.find('E')
                        while rp_idx >= 0:
                            sentence = sentence[:rp_idx] + en_frags[en_idx] + sentence[rp_idx + 1:]
                            rp_idx = sentence.find('E', rp_idx + len(en_frags[en_idx]))
                            en_idx += 1
                    except:
                        print line

                    result = re.sub(r"\s+", " ", sentence)
                    result = result.strip()

                    out_f.write(result + '\n')
                    cnt += 1
                    if cnt % 100000 == 0:
                        print "processed %d lines" % cnt

        return [self.output]

    def _match_frags(self, line, reg):
        start = 0
        frags = []
        en_frags = []
        for match in reg.finditer(line):
            frags.append(line[start: match.span()[0]])

            matched_str = line[match.span()[0]: match.span()[1]]
            frags.append('E')
            en_frags.append(matched_str)

            start = match.span()[1]

        last_frag_text = line[start:]
        if last_frag_text:
            frags.append(last_frag_text)

        return ''.join(frags), en_frags


class Remove_Space(Rule_Line):
    def __init__(self):
        re_s = []
        re_s.append((r"([a-zA-Z0-9\.])\s+([a-zA-Z0-9])", re.IGNORECASE, "\\1==KEEP==\\2"))
        re_s.append((r" +", re.IGNORECASE, ""))
        re_s.append((r"==KEEP==", re.IGNORECASE, " "))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove spaces', self)


class Norm_Name(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r"(\w)\?(\w)", f, "\\1 \\2"))
        re_s.append((r"•", f, " "))
        re_s.append((r"·", f, " "))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Normalize Chinese names (e.g. 内尔森?坦努尔, 内尔森•坦努尔)', self)


class Remove_Translator_Note(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r"\([^\)]+译者注\)", f, ""))
        re_s.append((r"（[^）]+译者注）", f, ""))
        re_s.append((r"^.*\t译者.*", f, ""))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove tranalator note', self)


class Remove_Pic_Note(Rule_Line):
    def __init__(self):
        re_s = [(r"^.*[^试]图.*", re.IGNORECASE, "")]
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove picture note (e.g. Reuters图为1月，工作人员在湖北武汉兴建一条新地铁线)', self)


class Remove_Line_Less_Char(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Remove line with too less Chinese characters', self)

    def run(self, line):
        if not line:
            return None
        cnt = 0
        l = line
        for c in l:
           if not common.is_chinese(c):
               cnt += 1
        ratio = float(cnt) / float(len(l))
        if ratio > 0.7:
            # print '%d / %d' % (cnt, len(l))
            return None
        return line


class Segment_Jieba_Then_Char(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Jieba segment then break to Chinese characters, please only apply to Chinese sentence', self)
        self.sp = common.Remove_Redundant_Spaces()

    def run(self, line):
        if not line: return None
        zh_sentence = line.strip()
        zh_seg_list = jieba.cut(zh_sentence, cut_all=False)
        zh_sentence = " ".join(zh_seg_list)
        zh_sentence = self.sp.run(zh_sentence)
        zh_sentence = zh_sentence.lower()
        zh_sentence = zh_sentence.replace("< s >", "<s>")
        zh_sentence = zh_sentence.replace("< url >", "<URL>")
        zh_sentence = zh_sentence.replace("_ unk", "_unk")
        zh_sentence = zh_sentence.replace("_ pad", "_pad")

        chars = []
        sentence = zh_sentence.strip()
        sen_phrases = sentence.split(" ")
        for phrase in sen_phrases:
            if not len(phrase): continue
            if not common.is_chinese(phrase[0]):
                chars.append(phrase)
            else:
                for c in phrase:
                    chars.append(c)

        l = " ".join(chars)

        if not l: return None
        return l


class Split_Not_ChineseCharacter(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r'([!-~]+)', f, ' \\1 '))  # consecutive ascii printable characters

        super(self.__class__, self).__init__(re_s)
        self.set_desc("Split the NotChineseCharacter with white space", self)


class Remove_Chinese_Number_Unit_After_Number_Entity(Rule_Line):
    def __init__(self,**kwargs):
        self.number_tag = "N"
        if "number_tag" in kwargs:
            self.number_tag = kwargs["number_tag"]

        re_s = []
        f = re.IGNORECASE
        re_s.append((self.number_tag + r'\s*万亿'.decode('utf-8'), f, self.number_tag))
        re_s.append((self.number_tag + r'\s*万'.decode('utf-8'), f, self.number_tag))
        re_s.append((self.number_tag + r'\s*亿'.decode('utf-8'), f, self.number_tag))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove Chinese Number Unit', self)


class Remove_Chinese_Single_Quotation(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r'‘s', f, r"'s"))
        re_s.append((r'’s', f, r"'s"))
        re_s.append((r's‘', f, r"s'"))
        re_s.append((r"s’", f, r"s'"))
        re_s.append((r"‘", f, r""))
        re_s.append((r"’", f, r""))
        super(self.__class__, self).__init__(re_s)

        self.set_desc(self,"Remove Chinese_Single_Quotation")


class Replace_Words_Per_Dict(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('According to a dictionary, replace words in one line', self)
        if 'dictfile' in kwargs:
            dictfile = kwargs['dictfile']
            self.entities = dict()
            with open(dictfile) as f:
                lines = f.readlines()
                for l in lines:
                    l = l.rstrip()
                    self.entities[l.lower()] = l
        else:
            print 'dictfile is required but it is null'
            raise Exception

    def run(self, line):
        if not line: return None
        words = line.rstrip().split()
        new_words = []
        for w in words:
            if w in self.entities:
                new_words.append(self.entities[w])
            else:
                new_words.append(w)
        l = " ".join(new_words)
        if not l: return None
        return l


class Replace_Lower_Char_To_Upper_Word_Line(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc("Replace_Lower_Char_To_Upper_Word",self)
        if "upperCharWord" in kwargs:
            self.upperCharWordDict = {}
            for list in kwargs["upperCharWord"]:
                with open(list) as f:
                    lines = f.readlines()
                    for l in lines:
                        self.upperCharWordDict[ l.strip('\n').lower() ] = l.strip('\n')
        else:
            print "Word list file does not exist,please specify the word list files"
            raise Exception

    def find_Upper_Char_Word_By_Word_List(self, word):
        if word not in self.upperCharWordDict:
            return word
        else:
            return self.upperCharWordDict[word]

    def find_Upper_Char_Word_By_Source(self, word,line):
        start = line.lower().find(word)
        if start < 0:
            return None
        else:
            end = start + len(word)
            return line[start:end]

    def find_Upper_Char_Word(self, word,line):
        replaced_word = self.find_Upper_Char_Word_By_Source(word,line)
        if replaced_word == None:
            replaced_word = self.find_Upper_Char_Word_By_Word_List(word)
        return replaced_word

    def run(self, line):
        if not line: return None
        lines = line.split('\t')
        result_line = lines[0]
        if len(lines) == 1:
            result = re.findall(r'\b[A-Za-z0-9]+[A-Za-z0-9\'.:_\-&]\b', result_line)
            for word in result:
                if word != self.find_Upper_Char_Word_By_Word_List(word):
                    result_line = result_line.replace(word, self.find_Upper_Char_Word_By_Word_List(word))
            return result_line
        elif len(lines) == 2:
            result = re.findall(r'\b[A-Za-z0-9]+[A-Za-z0-9\'.:_\-&]\b', result_line)
            for word in result:
                if word != self.find_Upper_Char_Word(word, lines[1]):
                    result_line = result_line.replace(word, self.find_Upper_Char_Word(word, lines[1]))
            return result_line
        elif len(lines) > 2:
            #TODO deal with the translated line or the source line contain the character '\t'
            return line
        else:
            print "invalid input line format."
            return None


class Replace_Lower_Char_To_Upper_Word(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc("Replace_Lower_Char_To_Upper_Word",self)
        if "upperCharWord" in kwargs:
            self.upperCharWordDict = {}
            for list in kwargs["upperCharWord"]:
                with open(list) as f:
                    lines = f.readlines()
                    for l in lines:
                        self.upperCharWordDict[ l.strip('\n').lower() ] = l.strip('\n')
        else:
            print "Word list file does not exist,please specify the word list files"
            raise Exception

        if "source_text" in kwargs:
            self.source_text = kwargs['source_text']
            with codecs.open(self.source_text,'r','utf-8') as f:
               self.source = f.readlines()
        self.line_index = -1

    def find_Upper_Char_Word_By_Word_List(self, word):
        if word not in self.upperCharWordDict:
            return word
        else:
            return self.upperCharWordDict[word]

    def find_Upper_Char_Word_By_Source(self, word):
        line = self.source[self.line_index]
        start = line.lower().find(word)
        if start < 0:
            return None
        else:
            end = start + len(word)
            return line[start:end]

    def find_Upper_Char_Word(self, word):
        replaced_word = self.find_Upper_Char_Word_By_Source(word)
        if word == replaced_word or replaced_word == None:
            replaced_word = self.find_Upper_Char_Word_By_Word_List(word)
        return replaced_word

    def run(self, line):
        self.line_index += 1
        if not line: return None
        result = re.findall(ur'\b[A-Za-z0-9]+[A-Za-z0-9\'.:_\-&]\b', line)
        for word in result:
            if word != self.find_Upper_Char_Word(word):
                line = line.replace(word, self.find_Upper_Char_Word(word))
        return line


class Generate_Entity_Word_Dict(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc("Generate the entity words dict", self)
        if 'word_entity' in kwargs:
            self.word_entity = kwargs['word_entity']
        else:
            print "English word entity is not specify,please specify the word entity file"
            raise Exception
        if "baidu_word_entity" in kwargs:
            self.baidu_entity = kwargs['baidu_word_entity']
        else:
            print "Baidu word entity is not specify,please specify the word entity file"
            raise Exception
        if 'google_word_entity' in kwargs:
            self.google_entity = kwargs['google_word_entity']
        else:
            print "Google word entity is not specify,please specify the word entity file"
            raise Exception

    def run(self, input):
        with codecs.open(self.word_entity, 'r','utf-8') as word_entity:
            with codecs.open(self.baidu_entity, 'r','utf-8') as baidu_entity:
                with codecs.open(self.google_entity, 'r','utf-8') as google_entity:
                    with codecs.open(self.output, 'w','utf-8') as output:
                        while True:
                            word_line = word_entity.readline()
                            baidu_line = baidu_entity.readline()
                            google_line = google_entity.readline()
                            if word_line == '' or baidu_line == '' or google_line == '':
                                 return [self.output]
                            if baidu_line.strip('\n') == google_line.strip('\n') and word_line.strip('\n') != baidu_line.strip('\n'):
                                 output.write(word_line.strip('\n') + '\t' + baidu_line)


class Segment_ZH_Doc_To_Sentences(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from article file, segment content to sentences', self)

    def run(self, files):
        file = files[0]
        self.file_exist(file)
        with codecs.open(file, "r", "utf-8") as in_file:
            with codecs.open(self.output, "w", "utf-8") as tgt_file:
                line_counter = 0
                lines = in_file.readlines()
                for line in lines:
                    line_counter += 1
                    if line_counter % 10000 == 0:
                        print line_counter

                    line = line.strip()

                    mul_separators = ['……”'.decode('utf8'), '。”'.decode('utf8'), '？”'.decode('utf8'),
                                      '！”'.decode('utf8')]
                    for sep in mul_separators:
                        line = line.replace(sep, sep + '|||')

                    sub_lines = line.split('|||')

                    results = []

                    single_separators = ['。'.decode('utf8'), '？'.decode('utf8'), '！'.decode('utf8')]
                    for sub_line in sub_lines:
                        for sep in single_separators:
                            sub_line = sub_line.replace(sep, sep + '|||')

                        if '“'.decode('utf8') in sub_line and '”'.decode('utf8') in sub_line:
                            sub_line = self.match_frags(sub_line, re.compile(r'“[^”]+”'.decode('utf8')))

                        results.extend(sub_line.split('|||'))

                    for result in results:
                        if len(result):
                            tgt_file.write(result.strip() + '\n')

        return [self.output]

    def match_frags(self, line, reg):
        start = 0
        frags = []
        for match in reg.finditer(line):
            frags.append(line[start: match.span()[0]])

            matched_str = line[match.span()[0]: match.span()[1]]
            frags.append(matched_str.replace('|||', ''))

            start = match.span()[1]

        last_frag_text = line[start:]
        if last_frag_text:
            frags.append(last_frag_text)

        return ''.join(frags)


class Find_Word_Entity(Rule_Line):
    def __init__(self,**kwargs):
        super(self.__class__, self).__init__()
        self.set_desc("Find the match word entity", self)
        self.word_dict = {}
        self.source_text = ''
        self.replaced_word = {}

        if 'word_dict' in kwargs:
            with codecs.open(kwargs['word_dict'], 'r', 'utf-8') as dict_fils:
                for line in dict_fils.readlines():
                    words = line.split('\t')
                    self.word_dict[words[0].strip()] = words[1].strip('\n').strip()
        else:
            print "the word dict file is not specify,please specify the word dict file"
            raise Exception

    def find_Word_Entity(self, word):
        if word not in self.word_dict:
            return word
        else:
            return self.word_dict[word]

    def run(self,line):
        if not line:
            return None
        result = re.findall(ur'\b[A-Za-z0-9]+[A-Za-z0-9\'.:_\-&]\b', line.decode('utf-8'))
        for word in result:
            if word.strip(' ') != self.find_Word_Entity(word.strip(' ')):
                line = line.replace(word.strip(' '), self.find_Word_Entity(word.strip(' ')))
        return line


class Correct_En_Word_Case(Rule):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc("Correct_En_Word_Case",self)
        self.pattern = re.compile(r'\b([A-Za-z0-9]+)\b')

    def run(self, line, raw_line):
        '''
        ISSUE: 
        如果有一个单词同时在原句中出现了多次大小写不同的方式，则无法进行矫正。
        比如说， Xx is XX。 翻译是 xx是xx，则无法进行矫正。
        '''
        if not line: return None
        
        raw_line_lower = raw_line.lower()
        raw_line_size = len(raw_line)

        match_result = self.pattern.search(line)
        ret_line = ''
        last_start_index = 0
        while match_result:
            matched_txt = line[match_result.start():match_result.end()]
            matched_txt_len = len(matched_txt)
            ret_line += line[last_start_index:match_result.start()]
            raw_line_index = raw_line_lower.find(matched_txt)
            while raw_line_index > -1:
                if raw_line_index > 0 \
                    and raw_line_lower[raw_line_index - 1] <= 'z' \
                    and raw_line_lower[raw_line_index - 1] >= 'a' :
                    raw_line_index = raw_line_lower.find(matched_txt, raw_line_index + matched_txt_len)
                    continue

                if raw_line_index < raw_line_size - matched_txt_len \
                    and raw_line_lower[raw_line_index + matched_txt_len] <= 'z' \
                    and raw_line_lower[raw_line_index + matched_txt_len] >= 'a' and raw_line_lower[raw_line_index + matched_txt_len]!='s':
                    raw_line_index = raw_line_lower.find(matched_txt, raw_line_index + matched_txt_len)
                    continue

                if raw_line_index < raw_line_size - matched_txt_len and raw_line_lower[raw_line_index + matched_txt_len] =='s':
                    if raw_line_index<raw_line_size-matched_txt_len-1 and (raw_line_lower[raw_line_index + matched_txt_len+1] <= 'z' \
                    and raw_line_lower[raw_line_index + matched_txt_len+1] >= 'a' ):
                        raw_line_index = raw_line_lower.find(matched_txt, raw_line_index + matched_txt_len+1)
                        continue
                ret_line += raw_line[raw_line_index:(raw_line_index + matched_txt_len)]
                break

            if raw_line_index < 0:
                ret_line += matched_txt

            last_start_index = match_result.end()
            match_result = self.pattern.search(line, last_start_index)
            
        ret_line += line[last_start_index:]
        return ret_line


class Align_Correct_En_Word_Case(Rule):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc("Align_Correct_En_Word_Case", self)
        self.pattern = re.compile(r'\b([A-Za-z0-9]+)\b')

    def run(self, align_enabled, line, raw_line):
        '''
        ISSUE:
        如果有一个单词同时在原句中出现了多次大小写不同的方式，则无法进行矫正。
        比如说， Xx is XX。 翻译是 xx是xx，则无法进行矫正。
        '''
        if not align_enabled or not line: return None

        sentence = ' '.join(line)

        raw_line_lower = raw_line.lower()
        raw_line_size = len(raw_line)

        match_result = self.pattern.search(sentence)
        ret_line = ''
        last_start_index = 0
        while match_result:
            matched_txt = sentence[match_result.start():match_result.end()]
            matched_txt_len = len(matched_txt)
            ret_line += sentence[last_start_index:match_result.start()]
            raw_line_index = raw_line_lower.find(matched_txt)
            while raw_line_index > -1:
                if raw_line_index > 0 \
                        and raw_line_lower[raw_line_index - 1] <= 'z' \
                        and raw_line_lower[raw_line_index - 1] >= 'a':
                    raw_line_index = raw_line_lower.find(matched_txt, raw_line_index + matched_txt_len)
                    continue

                if raw_line_index < raw_line_size - matched_txt_len \
                    and raw_line_lower[raw_line_index + matched_txt_len] <= 'z' \
                    and raw_line_lower[raw_line_index + matched_txt_len] >= 'a' and raw_line_lower[raw_line_index + matched_txt_len]!='s':
                    raw_line_index = raw_line_lower.find(matched_txt, raw_line_index + matched_txt_len)
                    continue

                if raw_line_index < raw_line_size - matched_txt_len and raw_line_lower[raw_line_index + matched_txt_len] =='s':
                    if raw_line_index<raw_line_size-matched_txt_len-1 and (raw_line_lower[raw_line_index + matched_txt_len+1] <= 'z' \
                    and raw_line_lower[raw_line_index + matched_txt_len+1] >= 'a' ):
                        raw_line_index = raw_line_lower.find(matched_txt, raw_line_index + matched_txt_len+1)
                        continue

                ret_line += raw_line[raw_line_index:(raw_line_index + matched_txt_len)]
                break

            if raw_line_index < 0:
                ret_line += matched_txt

            last_start_index = match_result.end()
            match_result = self.pattern.search(sentence, last_start_index)

        ret_line += sentence[last_start_index:]
        ret_sentence_array = ret_line.split(' ')
        return ret_sentence_array
