# coding: utf-8

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

import rule_engine

import time

import Common

file_in = 'test_data/align_test_data/input.txt'
test_out = 'test_data/align_test_data/output_test.txt'
file_out = 'test_data/align_test_data/output.txt'


class bifrost_simulate:
    def post_process(self, line):
        return line.replace("CENTEr", "中间")

    def pre_process(self, line):
        return line.replace("good", "nice")


class TestAlignment(unittest.TestCase):
    def test_align_context_file_rule(self):
        tgt_src = []
        lines = []
        with open(file_in, 'r') as filein:
            count = 0
            whole_time = 0
            for line in filein:
                context = {}
                data = line.split('<.>')
                print data
                context['line'] = data[1]
                context['raw_line'] = data[0]

                context['align_enabled'] = True

                context['tgt_array'] = data[1].split(' ')
                context['src_array'] = data[2].split(' ')
                context['tgt_src_mapping'] = [int(item) for item in data[3].split(' ')]

                rule_engine_context = {}
                rule_engine_context["bifrost"] = bifrost_simulate()

                engine = rule_engine.RuleEngine("../schema_lib_medical_zh_post_align_gpu_context.json", None, mode='lib',
                                                rule_engine_context=rule_engine_context)
                start_time = time.time()
                engine.execute(context)
                end_time = time.time()
                print context
                whole_time += end_time - start_time
                count += 1
                with open(file_out, 'a+') as fileout:
                    fileout.write(data[0])
                    fileout.write('\n')
                    fileout.write(context['line'])
                    fileout.write('\n')
                    fileout.write(data[1])
                    fileout.write('\n')

                    tgt_origin = []
                    for item in context['tgt_origin']:
                        tgt_origin.append(item.decode('utf8'))
                    fileout.write(' '.join(tgt_origin))
                    fileout.write('\n')

                    src_origin = []
                    for item in context['src_origin']:
                        src_origin.append(item.decode('utf8'))
                    fileout.write(' '.join(src_origin))
                    fileout.write('\n')

                    mapping = [str(item) for item in context['mapping']]
                    fileout.write(' '.join(mapping))
                    fileout.write('\n')

                    target = context['target']
                    fileout.write(' '.join(target))
                    fileout.write('\n')

                    source = context['source']
                    fileout.write(' '.join(source))
                    fileout.write('\n')

                    fileout.write('\n')
                    fileout.write('\n')
                    mapping_array = context['mapping']
                    tgt_src.append(' '.join([target[i] + ":" + source[mapping_array[i]] for i in range(len(target))
                                             if mapping_array[i] < len(source)]))
                    lines.append(context['line'])
            print "average process time = %.2f" % (whole_time / count)
        self.assertEqual(Common.count_lines_of_file(file_in), Common.count_blocks_of_file(file_out),
                         'Align function is not correct!')

        test = open(test_out, 'r')
        test_data = test.readlines()

        for i in range(len(tgt_src)):
            self.assertEqual(test_data[2 * i].strip(), lines[i].strip(), 'Translate result is not correct!')
            self.assertEqual(test_data[2 * i + 1].strip(), tgt_src[i].strip(), 'Align result is not correct!')


if __name__ == '__main__':
    unittest.main()
