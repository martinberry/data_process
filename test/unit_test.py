from .. import rule_common as rc
from nltk.tokenize.moses import MosesTokenizer
import unittest

import contextlib
import sys
import os
from subprocess import Popen, PIPE
import difflib


class DummyFile(object):
    def write(self, x): pass


@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile()
    yield
    sys.stdout = save_stdout


class TestPackageSubstitution(unittest.TestCase):

    def setUp(self):
        self.data_path_file = '../test_data/en.txt'
        self.data_line = '7 On 23 September 2002, the Civil Appeals Chamber of the Supreme' \
                         ' Court rejected an application for amparo made by the author, who ' \
                         'claimed he had not been identified as the person sought for extradition.'
        self.tgt_origin_data = ['\xe4\xbd\xbf\xe7\x94\xa8', '\xe5\x9c\xa8', 'ph@@', 'me',
                          '/', 'd@@', 'mac', '\xef\xbc\x88', '5.4', 'ml', '\xef\xbc\x8c',
                          'v', '/', 'v', '=', '3', '/', '1', '\xef\xbc\x89', '\xe4\xb8\xad',
                          '\xe7\x9a\x84', '3', '\xe4\xb8\xaa', 'n-', '\xe7\xa2\x98', '\xe8\x8b\xaf@@',
                          '\xe4\xb9\x99@@', '\xe9\x85\xae', '\xef\xbc\x88', '98.4', 'mg', '\xef\xbc\x8c',
                          '0.400', 'mmol', '\xef\xbc\x89', '\xe8\xbf\x9b\xe8\xa1\x8c', '\xe4\xb8\x80\xe8\x88\xac',
                          '\xe6\x96\xb9\xe6\xb3\x95', 'd', ';', '\xe7\xac\xac\xe4\xb8\x80\xe6\xad\xa5',
                          '\xef\xbc\x9a', '100', '\xe4\xb8\xaa', 'c', '\xef\xbc\x8c', '1', 'h', ';',
                          '\xe7\xac\xac\xe4\xba\x8c\xe6\xad\xa5', '\xef\xbc\x9a', '100', '\xe4\xb8\xaa',
                          'c', '\xef\xbc\x8c', '2', 'h', ';', '\xe5\x90\x8e\xe5\xa4\x84\xe7\x90\x86',
                          '\xe5\x92\x8c', '\xe8\x89\xb2\xe8\xb0\xb1', '\xe7\xba\xaf\xe5\x8c\x96', '\xef\xbc\x88',
                          '\xe5\xb7\xb1\xe7\x83\xb7', '\xef\xbc\x89', '\xe5\xbe\x97\xe5\x88\xb0',
                          '\xe6\xa0\x87\xe9\xa2\x98', '\xe5\x8c\x96\xe5\x90\x88\xe7\x89\xa9',
                          '\xe6\x97\xa0\xe8\x89\xb2', '\xe6\xb2\xb9', '\xef\xbc\x88', '55.2', 'mg',
                          '\xef\xbc\x8c', '46', '\xef\xbc\x85', '\xef\xbc\x89', '\xe3\x80\x82']
        self.src_origin_data = ['general', 'procedure', 'd', 'was', 'followed', 'using', '3', '\xe2\x80\xb2',
                           '<->', 'iodo@@', 'acet@@', 'ophen@@', 'one', '(', '<N:OTguNA==>', 'mg', ',',
                           '<N:MC40MDA=>', 'mmol', ')', 'in', 'ph@@', 'me', '/', 'd@@', 'mac', '(', '<N:NS40>',
                           'ml', ',', 'v', '/', 'v', '=', '3', '/', '1', ')', ';', 'first', 'step', ':',
                           '100', '\xc2\xb0', 'c', ',', '1', 'h', ';', 'second', 'step', ':', '100', '\xc2\xb0',
                           'c', ',', '2', 'h', ';', 'workup', 'and', 'chromatographic', 'purification', '(',
                           'hexane', ')', 'yielded', 'the', 'title', 'compound', 'as', 'a', 'colorless', 'oil',
                           '(', '<N:NTUuMg==>', 'mg', ',', '46', '%', ')', '.']

        self.min_data_path = 'test_data/tokenizer_test_data/minified_en.txt'
        self.perl_path = '../tokenizer/tokenizer.perl'

        try:
            os.remove('GTV2_test_result.html')
        except OSError:
            pass

    def test_Align_Sentence_Detokenizer(self):
        asd_package = rc.Align_Sentence_Detokenizer(mode='package')
        asd_script = rc.Align_Sentence_Detokenizer(mode='script')
        with nostdout():
            self.assertEqual(
                asd_package.run(align_enabled=True, tgt_origin=self.tgt_origin_data, src_origin=self.src_origin_data),
                asd_script.run(align_enabled=True, tgt_origin=self.tgt_origin_data, src_origin=self.src_origin_data)
            )

    def test_General_Tokenizer_v2(self):
        """
        This test will generate a html file named GTV2_test_result within current directory
        """
        gtv2_package = rc.General_Tokenizer_v2(mode='package')
        gtv2_script = rc.General_Tokenizer_v2(mode='script')
        with nostdout():
            package_file_path = gtv2_package.run([self.min_data_path])
            script_file_path = gtv2_script.run([self.min_data_path])
        with open(package_file_path[0]) as m:
            package_lines = m.readlines()
        with open(script_file_path[0]) as s:
            script_lines = s.readlines()

        file_diff_handler = difflib.HtmlDiff()
        html = file_diff_handler.make_file(package_lines, script_lines, fromdesc='Package Result', todesc='Script Result', context=True)
        with open('GTV2_test_result.html', 'w') as h:
            h.writelines(html)
        os.remove(package_file_path[0])
        os.remove(script_file_path[0])

    def test_General_Sentence_Tokenizer(self):
        gst_package = rc.General_Sentence_Tokenizer(mode='package')
        gst_script = rc.General_Sentence_Tokenizer(mode='script')
        with nostdout():
            package_holder = gst_package.run(self.data_line)
            script_holder = gst_script.run(self.data_line)
        sys.stdout.writelines(difflib.context_diff(package_holder, script_holder, fromfile='package_gst', tofile='script_gst'))
        self.assertEqual(package_holder, script_holder)

    def test_General_Sentence_Detokenizer(self):
        gsd_package = rc.General_Sentence_Detokenizer(mode='package')
        gsd_script = rc.General_Sentence_Detokenizer(mode='script')
        with nostdout():
            package_holder = gsd_package.run(self.data_line)
            script_holder = gsd_script.run(self.data_line)
        sys.stdout.writelines(difflib.context_diff(package_holder, script_holder, fromfile='package_gsd', tofile='script_gsd'))
        self.assertEqual(package_holder, script_holder)

    def test_Diff_btw_perl_package(self):
        # this test special case that will fail:
        # for any multi-dot ending, tokenizer will add space in between
        with open(self.min_data_path) as f:
            line = f.readline()
        tokenizer_cmd = [self.perl_path, "-l", 'en', "-q", "-"]
        tokenizer_perl = Popen(tokenizer_cmd, stdin=PIPE, stdout=PIPE)
        perl_sentence, _ = tokenizer_perl.communicate(line)

        package_sentence = MosesTokenizer().tokenize(line, return_str=True)

        self.assertEqual(perl_sentence, package_sentence.encode('utf8'))

if __name__ == '__main__':
    unittest.main()
