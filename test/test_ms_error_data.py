import unittest
import sys
import os
import codecs

reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rule_common
from rule_common import Filter_Sentence_With_Illegal_Chars

rule_class = Filter_Sentence_With_Illegal_Chars()


class TestMSErrorData(unittest.TestCase):
    def test_error_data(self):
        with open('test_data/error_data.txt') as input_file:
            for line in input_file:
                self.assertEqual(rule_class.check_chars(line), False,
                                 "rule for filter illegal chars is not correct!")
        with codecs.open('test_data/normal_data.txt', encoding='utf8') as input_file:
            for line in input_file:
                self.assertEqual(rule_class.check_chars(line), True,
                                 "rule for filter illegal chars is not correct!")

if __name__ == '__main__':
    unittest.main()
