# -*- coding: utf-8 -*-
from rule import *
import rule_common as common
import re
import nltk
import codecs
import sys
import base64


class Remove_Bullet(Rule_Line):
    def __init__(self):
        re_s = [(r"^((\d+|[xiv]+|[a-f－・•￭■□♦◦●○◊►√∗*＊②③]])\s?\.|\(\s?(\d+|[xiv]+|[a-f])\)\s?\.?|((\d+|[a-z]+)\.)+(\d+|[a-z]+)\.?)", re.IGNORECASE, "")]
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove bullets', self)

class Remove_Bullet_v2(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((ur'^((\d+|[xiv]+|[a-f])\.\s|\(?(\d+|[xiv]+|[a-f])\)|((\d+|[a-z]+)\.)+(\d+|[a-z]+)\.?\s)', f, ''))
        re_s.append((ur'^[－・•￭■□♦◦●○◊►√∗*＊①②③④⑤⑥⑦⑧⑨⑩ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇]', f, ''))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove English bullets', self)


class Remove_Punctuation(Rule_Line):
    def __init__(self):
        re_s = [(r"\"|—|“|”|《|》", re.IGNORECASE, " ")]
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove punctuations', self)

class Remove_Punctuation_v2(Rule_Line):
    def __init__(self):
        re_s = [(r"\"| - | — |“|”|《|》",re.IGNORECASE," ")]
        super(self.__class__,self).__init__(re_s)
        self.set_desc("Remove punctuations V2",self)

class Replace_Chinese_Single_Quotation(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r'’', f, "'"))
        re_s.append((r'“', f, '"'))
        re_s.append((r'”', f, '"'))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Replace Chinese single quotation to English Single quotation', self)


class Replace_Chinese_Punctuation(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((ur'‘', f, "'"))
        re_s.append((ur'’', f, "'"))
        re_s.append((ur'“', f, '"'))
        re_s.append((ur'”', f, '"'))
        re_s.append((ur'【', f, '['))
        re_s.append((ur'】', f, ']'))
        re_s.append((ur'（', f, '('))
        re_s.append((ur'）', f, ')'))
        re_s.append((ur'，', f, ','))
        re_s.append((ur'。', f, '.'))
        re_s.append((ur'？', f, '?'))
        re_s.append((ur'！', f, '!'))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Replace Chinese punctuations to the corresponding English ones', self)


class Dedupe_Repeated_Punctuation(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r',{2,}', f, ","))
        re_s.append((r'\.{2,}', f, "."))
        re_s.append((r'\?{2,}', f, "?"))
        re_s.append((r'!{2,}', f, '!'))
        re_s.append((r';{2,}', f, ';'))
        re_s.append((r':{2,}', f, ':'))
        re_s.append((r'"{2,}', f, '"'))
        re_s.append((r'\'{2,}', f, '\''))
        re_s.append((r'\({2,}', f, '('))
        re_s.append((r'\){2,}', f, ')'))
        re_s.append((r'-{2,}', f, '-'))    # Hyphen
        re_s.append((r'–{2,}', f, '–'))  # En dash
        re_s.append((r'—{2,}', f, '—'))  # Em dash
        re_s.append((r'_{2,}', f, '_'))    # Underscore
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Dedupe the repeated English punctuations', self)


class Separate_Currency_Number(Rule_Line):
    def __init__(self):
        re_s = []
        f = re.IGNORECASE
        re_s.append((r'\b(?P<curr>rmb|cny|y|jpy|won|kpw|krw|hkd|mop|ntd|rbs|rs|rbl|rub|eur|euro|usd|chf|cad|aud|sgd|myr|idr|nzd|vnd|thb|php|dkk|sek|zar|brl)(?P<number>\d+(,\d+)*(\.\d+)? ?(m|million|bn|billion|trillion|tn)?)\b',
                    f,
                    r'\g<curr> \g<number>'))
        re_s.append((r'\$(?P<number>\d+(,\d+)*(\.\d+)? ?(m|million|bn|billion|trillion|tn)?)\b',
                    f,
                    r'$ \g<number>'))
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Separate the Currency Number', self)


class Remove_Between_QuesMark(Rule_Line):
    def __init__(self):
        re_s = [(r"(\w)\?(\w)", re.IGNORECASE, "\\1\\2")]
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove question mark between word (e.g. use?sanctions)', self)


class Remove_Line_With_No_Punct_Ending(Rule_Line):
    def __init__(self):
        self.pattern = re.compile(r'^.*[,.;:"?!]$')
        super(self.__class__, self).__init__()
        self.set_desc('Remove line with no punctation ending', self)

    def run(self, line):
        if line and self.pattern.match(line):
            return line
        else:
            return None


class Remove_Line_Less_Char(Rule_Line):
    def __init__(self):
        re_s = [(r"[a-zA-Z ,!?]", re.IGNORECASE, "")]
        super(self.__class__, self).__init__(re_s)
        self.set_desc('Remove line with too less English characters', self)

    def run(self, line):
        l = super(self.__class__, self).run(line)
        if l:
            ratio = float(len(l)) / float(len(line))
            if ratio > 0.5:
                return None
        return line


class Capitalize(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Capitalize line', self)

    def run(self, line):
        if line:
            line = line[0].upper() + line[1:]
            return line

        return None


class Slot_Tag_Number(Rule_Line):
    '''
    Basic rule for number slot tagging in training data generation.
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Slot_Tag', self)
        self.number_tag = "N"
        if "number_tag" in kwargs: self.number_tag = kwargs["number_tag"]

    def match_frags(self, frag, reg):
        if frag[1]:
            line = frag[0]
            start = 0
            frags = []
            for match in reg[0].finditer(line):
                frags.append((line[start: match.span()[0]], True))

                if reg[1] == self.number_tag:
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
        En_Reg_List = [
            (r'\b\d{1,3}(,\d{3})+(\.\d+)?( ?(m|million|bn|billion|trillion|tn))?\b', self.number_tag),  # Strict format number
            (r'\b\d{1,3}( \d{3})+(\.\d+)?( ?(m|million|bn|billion|trillion|tn))?\b', self.number_tag),  # Strict format number
            (r'\b\d+(\.\d+)?( ?(m|million|bn|billion|trillion|tn))?\b', self.number_tag)  # Arbitrary format number
        ]
        En_Reg_List = [(re.compile(r[0].decode('utf-8'), re.IGNORECASE), r[1]) for r in En_Reg_List]

        return self.slot_tag(line,En_Reg_List)


class Slot_Tag_Number_v2(Rule_Line):
    '''
    Number slot tagging in training data generation.
    Integers under 1000 won't be tagged.
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Slot_Tag', self)
        self.number_tag = "N"
        if "number_tag" in kwargs: self.number_tag = kwargs["number_tag"]

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
        En_Reg_List = [
            (r'\b\d{1,3}(,\d{3})+(\.\d+)?( ?(m|million|bn|billion|trillion|tn))?\b', self.number_tag),  # Strict format
            (r'\b\d{1,3}( \d{3})+(\.\d+)?( ?(m|million|bn|billion|trillion|tn))?\b', self.number_tag),  # Strict format
            (r'\b\d+(\.\d+)?( ?(m|million|bn|billion|trillion|tn))?\b', self.number_tag)  # Arbitrary format
        ]

        En_Reg_List = [(re.compile(r[0].decode('utf-8'), re.IGNORECASE), r[1]) for r in En_Reg_List]

        return self.slot_tag(line, En_Reg_List)


class Slot_Tag_Number_v3(Rule_Line):
    '''
    Number slot tagging in decoding.
    Integers under 1000 won't be tagged.
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Slot_Tag', self)
        self.number_tag = "N"
        if "number_tag" in kwargs: self.number_tag = kwargs["number_tag"]

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

        return ' '.join(texts)

    def run(self, line):
        En_Reg_List = [
            (r'<([A-Za-z]+)>[^<]+</\1>', 'E'),  # Already slotted entities to avoid changing
            (r'\b\d{1,3}(,\d{3})+(\.\d+)?( ?(m|million|bn|billion|trillion|tn))?\b', 'N'),  # Strict format number
            (r'\b\d{1,3}( \d{3})+(\.\d+)?( ?(m|million|bn|billion|trillion|tn))?\b', 'N'),  # Strict format number
            (r'\b\d+(\.\d+)?( ?(m|million|bn|billion|trillion|tn))?\b', 'N')  # Arbitrary format number
        ]
        En_Reg_List = [(re.compile(r[0].decode('utf-8'), re.IGNORECASE), r[1]) for r in En_Reg_List]

        return self.slot_tag(line, En_Reg_List)


class Slot_Tag_Number_v4(Rule_Line):
    '''
    Number slot tagging in training data generation.
    Only numbers with m/bn/tn/million/billion/trillion will be tagged.
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Slot_Tag', self)
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
        En_Reg_List = [
            (r'\b\d{1,3}(,\d{3})+(\.\d+)? ?(m|million|bn|billion|trillion|tn)\b', self.number_tag),  # Strict format
            (r'\b\d{1,3}( \d{3})+(\.\d+)? ?(m|million|bn|billion|trillion|tn)\b', self.number_tag),  # Strict format
            (r'\b\d+(\.\d+)? ?(m|million|bn|billion|trillion|tn)\b', self.number_tag)  # Arbitrary format
        ]

        En_Reg_List = [(re.compile(r[0].decode('utf-8'), re.IGNORECASE), r[1]) for r in En_Reg_List]

        return self.slot_tag(line, En_Reg_List)


class Slot_Tag_Number_v5(Rule_Line):
    '''
    Number slot tagging in decoding.
    Only numbers with m/bn/tn/million/billion/trillion will be tagged.
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Slot_Tag', self)
        self.number_tag = "N"
        if "number_tag" in kwargs: self.number_tag = kwargs["number_tag"]

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

        return ' '.join(texts)

    def run(self, line):
        En_Reg_List = [
            (r'<([A-Za-z]+)>[^<]+</\1>', 'E'),  # Already slotted entities to avoid changing
            (r'\b\d{1,3}(,\d{3})+(\.\d+)? ?(m|million|bn|billion|trillion|tn)\b', 'N'),  # Strict format
            (r'\b\d{1,3}( \d{3})+(\.\d+)? ?(m|million|bn|billion|trillion|tn)\b', 'N'),  # Strict format
            (r'\b\d+(\.\d+)? ?(m|million|bn|billion|trillion|tn)\b', 'N')  # Arbitrary format
        ]
        En_Reg_List = [(re.compile(r[0].decode('utf-8'), re.IGNORECASE), r[1]) for r in En_Reg_List]

        return self.slot_tag(line, En_Reg_List)


class Slot_Tag_Notrans(Rule_Line):
    '''
    Notrans section slot tagging in decoding.
    Only match patterns will be tagged.
    '''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Slot_Tag_Notrans', self)
        self.number_tag = "NOTRANS"
        if "notrans_tag" in kwargs: self.number_tag = kwargs["notrans_tag"]

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

        return ' '.join(texts)

    def run(self, line):
        Pattern_List = [
            (ur'<([A-Za-z]+)>[^<]+</\1>', 'E'),  # Already slotted entities to avoid changing
            (ur'http[:：]//[a-zA-Z0-9\-_~\*\'@&=\+\$/\?#\.]+[a-zA-Z0-9/#]', 'N'),
            (ur'(www\.[A-Za-z0-9\-_~\*\'@&=\+\$/\?#\.]+[a-zA-Z0-9/#])', 'N'),
            (ur'(([A-Za-z0-9\.-]+\.[A-Za-z0-9-]+|[A-Za-z]+)@[A-Za-z0-9\.-]+[A-Za-z])', 'N')
        ]
        Pattern_List = [(re.compile(r[0].decode('utf-8')), r[1]) for r in Pattern_List]

        return self.slot_tag(line, Pattern_List)


class Remove_Contain_Chinese(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc('Remove English lines that contain Chinese character', self)

    def run(self, line):
        # super(self.__class__, self).printme()
        if not line or common.contains_chinese(line):
            return None
        return line


class Split_Compound_Word(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Split compound words', self)

        self.connector_tag = "-"
        if "connector_tag" in kwargs:
            self.connector_tag = kwargs["connector_tag"]

    def run(self, line):
        if not line:
            return None

        if '-' in line:
            words = line.split()
            new_words = []
            for w in words:
                if len(w) > 1 and '-' in w:
                    sub_ws = w.split('-')
                    for i, sub_w in enumerate(sub_ws):
                        if i > 0:
                            new_words.append(self.connector_tag)

                        if sub_w:
                            new_words.append(sub_w)
                else:
                    new_words.append(w)

            line = ' '.join(new_words)

        return line


class Restore_Compound_Word(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('Split compound words', self)

        self.connector_tag = "-"
        if "connector_tag" in kwargs:
            self.connector_tag = kwargs["connector_tag"]

    def run(self, line):
        if not line:
            return None

        if self.connector_tag in line:
            line = line.replace(' %s ' % self.connector_tag, '-')

        return line


class Remove_Not_Contain_Number_Or_Aphabet(Rule_Line):
    def __init__(self):
        super(self.__class__,self).__init__()
        self.set_desc("Remove English line contains do not contains number or alphabet.",self)

    def run(self,line):
        if not common.contains_number_alphabet(line):
            return None
        return line


class Segment_EN_lines_To_Sentences(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from data of lines, segment content to sentences', self)
        self.splitter = nltk.data.load(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'nltk', 'english.pickle'
                         )
        )

    def run(self, line):
        if not line: return None
        sens = self.splitter.tokenize(line.decode('utf-8').strip())
        ret = []
        for s in sens:
            ret.append("%s" % s)

        return [ret]


class Segment_EN_lines_To_Sentences_v2(Rule_Line):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from data of lines, segment content to sentences. return sentences in separate lines.', self)
        self.splitter = nltk.data.load(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'nltk', 'english.pickle'
                         )
        )

    def run(self, line):
        if not line: return None
        sens = self.splitter.tokenize(line.decode('utf-8').strip())
        ret = []
        for s in sens:
            ret.append("%s" % s)

        return '\n\n'.join(ret)


class Segment_EN_Doc_To_Sentences(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: from article file, segment content to sentences', self)
        self.splitter = nltk.data.load(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'nltk', 'english.pickle'
                         )
        )

    def run(self, files):
        file = files[0]
        self.file_exist(file)

        text = open(file, 'r').read()
        paragraphs = text.split("\n")
        # with codecs.open(self.output, 'w', 'utf-8') as f:
        with codecs.open(self.output, 'w', 'utf-8') as f:
            for p in paragraphs:
                sens = self.splitter.tokenize(p.decode('utf-8').strip())
                for s in sens:
                    f.write("%s\n" % s)
                f.write("\n")

        return [self.output]


class Catch_Contain_Upper_Character_Word(Rule_Line):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.set_desc(self, "Catch the upper word in sentence")

    def is_contain_upper_character(self, param):
        for char in param:
            if char >= 'A' and char <= 'Z':
                return True
        return False

    def remove_surround_punctuation(self, word):
        result = re.search(r'[a-zA-Z][\S]*[a-zA-Z]', word)
        if result == None:
            return ''
        else:
            return result.group(0)


    def run(self, line):
        if not line: pass
        is_first_word = True
        result = ''
        last_word = ''
        for word in re.findall(ur"\b[A-Za-z0-9]+[A-Za-z0-9\'.:_\-&]\b",line):
            word = self.remove_surround_punctuation(word)
            if word != '':
                if is_first_word:
                    if self.is_contain_upper_character(word[1:]):
                        last_word += ' ' + word
                        is_first_word = False
                    else:
                        result += last_word
                        last_word = ''
                        is_first_word = False
                else:
                    if self.is_contain_upper_character(word):
                        last_word += ' ' + word
                    else:
                        result += last_word + '\n'
                        last_word = ''
        result += last_word
        return result


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
                        and raw_line_lower[raw_line_index + matched_txt_len] >= 'a':
                    raw_line_index = raw_line_lower.find(matched_txt, raw_line_index + matched_txt_len)
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

        