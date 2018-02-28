#!/usr/bin/python3

import http.client
import argparse
import datetime
from string import Template
import time
import random
import sys
import Common
from html.parser import HTMLParser

html_parser = HTMLParser()
proxy_used = ["192.168.1.142", 1181]

target_site = "translate.googleusercontent.com"
target_path = "/translate_f"
source_lanauage = "auto"
target_language = "zh-CN"
offset_lines = 0

per_size_in_byte = 38000
per_size_in_byte_min = 28000

http_action = "POST"

timeout_seconds = 60

body_template = Template("""-----------------------------13075323991116307510518023263
Content-Disposition: form-data; name="sl"

$source_lang
-----------------------------13075323991116307510518023263
Content-Disposition: form-data; name="tl"

$target_lang
-----------------------------13075323991116307510518023263
Content-Disposition: form-data; name="js"

y
-----------------------------13075323991116307510518023263
Content-Disposition: form-data; name="prev"

_t
-----------------------------13075323991116307510518023263
Content-Disposition: form-data; name="hl"

en
-----------------------------13075323991116307510518023263
Content-Disposition: form-data; name="ie"

UTF-8
-----------------------------13075323991116307510518023263
Content-Disposition: form-data; name="text"


-----------------------------13075323991116307510518023263
Content-Disposition: form-data; name="file"; filename="test.txt"
Content-Type: text/plain


$data
-----------------------------13075323991116307510518023263
Content-Disposition: form-data; name="edit-text"


-----------------------------13075323991116307510518023263--
""")

def setup_https_conn(proxy):
    if proxy:
        print("proxy connection:" + str(proxy))
        https_conn = http.client.HTTPSConnection(proxy[0], proxy[1], timeout = timeout_seconds)
        https_conn.set_tunnel(target_site)
        return https_conn
    else:
        print("no proxy connection")
        https_conn = http.client.HTTPSConnection(target_site, timeout = timeout_seconds)
        return https_conn

def setup_headers():
    headers = {"Content-Type": "multipart/form-data; boundary=---------------------------13075323991116307510518023263"}
    headers["Referer"] = "https://translate.google.com/"
    headers["Accept-Language"] = "en-US,en;q=0.5"
    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    headers["User-Agent"] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0"
    return headers

def construct_body(data):
    return body_template.substitute(data=data, source_lang=source_lanauage, target_lang=target_language).encode() #encode in utf-8
    

def get_response(data, proxy):
    https_conn = setup_https_conn(proxy)
    https_conn.request(http_action, target_path, construct_body(data), setup_headers())
    ret = https_conn.getresponse()
    print(ret.status, ret.reason)
    result = ret.read()
    content = result.decode("utf-8").replace("<pre>\n", "").replace("</pre>", "")
    final_result = None
    try:
        final_result = html_parser.unescape(content)
    except expression as identifier:
        final_result = content
    https_conn.close()
    return (ret.status, final_result)

def is_too_much_same_characters(source, target):
    
    si = len(source) - 1
    ti = len(target) - 1
    threshold = 30

    while threshold > 0 and si >= 0 and ti >= 0:
        if source[si] != target[ti]:
            return False
        threshold -= 1
        si -= 1
        ti -= 1
    return True

def output_content_to_file(lines, target_file, proxy):
    global per_size_in_byte

    nlines = len(lines)
    if nlines == 4960:
        print(lines)
    content = "".join(lines)
    first_finished = False
    second_finished = False
    while True:
        try:
            ret = get_response(content, proxy)
            if ret[0] == 200:
                # count as no translation due to too much text. split into two parts to translate.
                if is_too_much_same_characters(content, ret[1]) and len(lines) > 60:
                    print("split into two parts")
                    if not first_finished:
                        output_content_to_file(lines[:int(nlines/2)], target_file, proxy)
                    first_finished = True
                    if not second_finished:
                        output_content_to_file(lines[int(nlines/2):], target_file, proxy)
                    second_finished = True

                    per_size_in_byte = max(per_size_in_byte_min, int(per_size_in_byte / 1.1))
                    print("update per_size_in_byte: ", per_size_in_byte)
                else:
                    target_file.write(ret[1])
                    out_lines_number = ret[1].count('\n')
                    if out_lines_number < nlines:
                        print("More space line: " + str(nlines) + " " + str(out_lines_number))

                        target_file.write('\n' * (nlines - out_lines_number))
                break
            else:
                print("error")
                time.sleep(5)
        except KeyboardInterrupt:
            print("Exit with Ctrl + c")
            raise
        except:
            print("Unexpected error:", sys.exc_info()[0])
            print("sleep 30 secs")
            time.sleep(30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source_file", required=True, help="Required, specify the source file path.")
    parser.add_argument("-t", "--target_file", required=True, help="Required, specify the target file path.")
    parser.add_argument("-sl", "--source_language", default="auto", help="specify the source language. The default value is \"auto\". But it's suggested to use specified language code to avoid receive forbidden(403) status")
    parser.add_argument("-tl", "--target_language", default="zh-CN", help="specify the target language. The default value is \"zh-CN\".")
    parser.add_argument("-p", "--proxy", help="Optional, specify the proxy in hostname:port way.")
    parsed_args = parser.parse_args()
    print(parsed_args)

    source_file_name = parsed_args.source_file
    target_file_name = parsed_args.target_file
    source_lanauage = parsed_args.source_language
    target_language = parsed_args.target_language
    if parsed_args.proxy:
        ps = parsed_args.proxy.split(":")
        if len(ps) == 2:
            proxy_used[0] = ps[0]
            proxy_used[1] = int(ps[1])
        else:
            print("Proxy is not in correct format.")
            sys.exit(-1)
    else:
        proxy_used = None

    source_lines = Common.count_lines_of_file(source_file_name)
    if parsed_args.offset_lines:
        if parsed_args.offset_lines == 'auto':
            print('Auto update the offset_lines')
            offset_lines = Common.count_lines_of_file(target_file_name)
            print('auto offset_lines=' + str(offset_lines))
        else:
            offset_lines = int(parsed_args.offset_lines)

    target_file = open(target_file_name, "a+")
    if offset_lines == 0:
        print('Truncate target file due to the offset_lines = 0')
        target_file.truncate(0)
        target_file.seek(0)

    source_file = open(source_file_name, "r")
    lines = []
    processed_lines = 0
    save_offset_lines = 0
    lines_size_in_bytes = 0
    start_time = time.time()
    for line in source_file:
        if offset_lines > 0:
            offset_lines -= 1
            continue
        lines_size_in_bytes += sys.getsizeof(line)
        lines.append(line)
        if lines_size_in_bytes >= per_size_in_byte:
            output_content_to_file(lines, target_file, proxy_used)
            
            time.sleep(random.randint(3, 6))
            processed_lines += len(lines)
            speed = (processed_lines - save_offset_lines) / (time.time() - start_time)
            print("processed_lines: " + str(processed_lines))
            print("speed: " + str(speed) + " lines/sec")
            print("remaining time: " + str(datetime.timedelta(seconds=(source_lines - processed_lines)/speed)))
            lines = []
            lines_size_in_bytes = 0
    if len(lines) > 0:
        output_content_to_file(lines, target_file, proxy_used)
        processed_lines += len(lines)
        print("processed_lines: " + str(processed_lines))
    
    source_file.close()
    target_file.close()
        
