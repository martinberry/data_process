#!/usr/bin/python3

import unittest
import subprocess

import Common

baidu_out = 'test_data/test_out_baidu.txt'
google_out = 'test_data/test_out_google.txt'
bing_out = 'test_data/test_out_bing.txt'
file_in = 'test_data/test.txt'
youdao_out = 'test_data/test_out_youdao.txt'
lines_in = 200
auto_file_out = 'test_data/auto_test.txt'
auto_lines_out = 10

ip_pool = 'http://192.168.1.142:3001/api/pop'


class TestScrapeApi(unittest.TestCase):

    def test_common_script(self):
        self.assertEqual(Common.count_lines_of_file(file_in),  lines_in, "count_lines_of_file is not working as expected")

    def test_bing_NMT_api_normal(self):
        subprocess.run(['./TranslateWithBingNMTApi.py', '-s', file_in, '-t', bing_nmt_out, '-sl', 'en', '-tl', 'zh-CHS', '-tpn', '10', '-ip', ip_pool, '-r', 'True'])
        self.assertEqual(Common.count_lines_of_file(bing_nmt_out), lines_in, "bing's ouput is not correct")

    def test_bing_api_normal(self):
        subprocess.run(['./TranslateWithBingApi.py', '-s', file_in, '-t', bing_out, '-sl', 'en', '-tl', 'zh-Hans','-tpn', '10', '-ip', ip_pool])
        self.assertEqual(Common.count_lines_of_file(bing_out), lines_in, "bing's ouput is not correct")

    def test_youdao_api_normal(self):
        subprocess.run(['./TranslateWithYoudaoApi.py', '-s', file_in, '-t', youdao_out, '-sl', 'en', '-tl', 'zh-Hans', '-tpn', '10', '-ip', ip_pool])
        self.assertEqual(Common.count_lines_of_file(youdao_out), lines_in, "youdao's ouput is not correct")

    def test_baidu_api_normal(self):
        subprocess.run(['./TranslateWithBaiduApi.py', '-s', file_in, '-t', baidu_out, '-sl', 'en', '-tl', 'zh'])
        self.assertEqual(Common.count_lines_of_file(baidu_out),  lines_in, "baidu's ouput is not correct")

    def test_google_api_normal(self):
        subprocess.run(['./TranslateWithGoogleApi.py', '-s', file_in, '-t', google_out, '-sl', 'en-US', '-tl', 'zh-CN', '-p', '192.168.1.140:1181'])
        self.assertEqual(Common.count_lines_of_file(google_out),  lines_in, "google's ouput is not correct")

    def test_baidu_api_auto(self):
        f = open(auto_file_out, 'w')
        subprocess.run(['head', '-n', str(auto_lines_out), file_in], stdout=f)
        f.close()
        self.assertEqual(Common.count_lines_of_file(auto_file_out),  auto_lines_out, "head's output is not correct")
        subprocess.run(['./TranslateWithBaiduApi.py', '-s', file_in, '-t', auto_file_out, '-sl', 'en', '-tl', 'zh'])
        self.assertEqual(Common.count_lines_of_file(auto_file_out),  lines_in, "auto: baidu's ouput is not correct")

    def test_google_api_auto(self):
        f = open(auto_file_out, 'w')
        subprocess.run(['head', '-n', str(auto_lines_out), file_in], stdout=f)
        f.close()
        self.assertEqual(Common.count_lines_of_file(auto_file_out),  auto_lines_out, "head's output is not correct")
        subprocess.run(['./TranslateWithGoogleApi.py', '-s', file_in, '-t', auto_file_out, '-sl', 'en-US', '-tl', 'zh-CN', '-p', '192.168.1.140:1181'])
        self.assertEqual(Common.count_lines_of_file(auto_file_out),  lines_in, "auto: google's ouput is not correct")

    def test_baidu_api_truc(self):
        f = open(auto_file_out, 'w')
        subprocess.run(['head', '-n', str(auto_lines_out), file_in], stdout=f)
        f.close()
        self.assertEqual(Common.count_lines_of_file(auto_file_out),  auto_lines_out, "head's output is not correct")
        subprocess.run(['./TranslateWithBaiduApi.py', '-s', file_in, '-t', auto_file_out, '-sl', 'en', '-tl', 'zh'])
        self.assertEqual(Common.count_lines_of_file(auto_file_out),  lines_in, "truc: baidu's ouput is not correct")

    def test_google_api_truc(self):
        f = open(auto_file_out, 'w')
        subprocess.run(['head', '-n', str(auto_lines_out), file_in], stdout=f)
        f.close()
        self.assertEqual(Common.count_lines_of_file(auto_file_out),  auto_lines_out, "head's output is not correct")
        subprocess.run(['./TranslateWithGoogleApi.py', '-s', file_in, '-t', auto_file_out, '-sl', 'en-US', '-tl', 'zh-CN', '-p', '192.168.1.140:1181'])
        self.assertEqual(Common.count_lines_of_file(auto_file_out),  lines_in, "truc: google's ouput is not correct")

if __name__ == '__main__':
    unittest.main()

