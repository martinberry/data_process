#!/usr/bin/python3
# coding: utf-8

import http.client
import argparse
import time
import datetime
import sys
import urllib.parse
import json
import Common
import multiprocessing
import urllib.request
import logging

ip_pool = 'http://192.168.1.142:3001/api/pop'
per_size_in_byte = 3000

target_site = "translator.microsoft.com"
target_path = "/neural/api/translator/translate"
source_language = "auto"
target_language = "zh"
offset_lines = 0

timeout_seconds = 60
http_action = "POST"

max_retries_count = 50
log_format=logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler = logging.FileHandler('TranslateWithYoudaoApi.' + str(int(time.time())) + ".log")
handler.setFormatter(log_format)
log = logging.getLogger("TranslateWithYoudaoApi")
log.addHandler(handler)
log.setLevel(logging.INFO)

query_queue = multiprocessing.Queue(666)
output_queue = multiprocessing.Queue()


def setup_http_conn(proxy):
    if proxy:
        print("proxy connection:" + str(proxy))
        https_conn = http.client.HTTPSConnection(proxy[0], proxy[1], timeout=timeout_seconds)
        https_conn.set_tunnel(target_site)
        return https_conn
    else:
        print("no proxy connection")
        https_conn = http.client.HTTPSConnection(target_site, timeout=timeout_seconds)
        return https_conn


def setup_headers():
    headers = {"Content-Type": "application/json"}
    headers["Referer"] = "https://translator.microsoft.com/neural/"
    headers["Accept-Language"] = "en-US,en;q=0.8"
    headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
    headers['X-Requested-With'] = "XMLHttpRequest"
    headers['Origin'] = "https://translator.microsoft.com"
    headers["User-Agent"] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:53.0) Gecko/20100101 Firefox/53.0"
    headers["Cookie"] = "MC1=GUID=d98c9b80f59f4b418b38f70ab9f5ea76&HASH=809b&LV=201705&V=4&LU=1496209069640; A=I&I=AxUFAAAAAACJCQAAIMEQb7hA787NZsCtfCZ4QQ!!&V=4; MUID=2A1A5FEF72356AD924D9557C76356C2D; dnn.lang_to=zh-Hans; ARRAffinity=3839e7781796d1128076ae2aea5824846ff1ecf9033be5ee784255f345a7ce4e; MicrosoftApplicationsTelemetryDeviceId=d06f55fc-7c8e-2058-d6c3-fa9c8bfb0510; MicrosoftApplicationsTelemetryFirstLaunchTime=1496735056380"
    return headers


def construct_body(data):
    return json.dumps({"Text": data,
                       "SourceLanguage": source_language,
                       "TargetLanguage": target_language})


def get_response(data, proxy):
    https_conn = setup_http_conn(proxy)
    https_conn.request(http_action, target_path, construct_body(data), setup_headers())
    ret = https_conn.getresponse()
    print(ret.status, ret.reason)
    result = ret.read()
    https_conn.close()
    return ret.status, result.decode("utf-8")


def parse_response(response):
    ret = json.loads(response)
    lines = []
    for rec in ret["resultSMT"].strip().split('(ppp)'):
        lines.append(rec)
    return lines


def get_proxy():
    if not ip_pool:
        return None

    with urllib.request.urlopen(ip_pool) as f:
        ret = f.read().decode('utf-8')
        json_ret = json.loads(ret)
        ipport = json_ret["Proxies"][0].split(':')
        return ipport[0], int(ipport[1])


def call_translation_api(lines, proxy):
    retries_count = 0
    while retries_count < max_retries_count:
        try:
            data = "(ppp)".join([line_parts[0] for line_parts in lines])
            ret = get_response(data, proxy)
            if ret[0] == 200:
                translated_lines = parse_response(ret[1])
                out_lines_number = len(translated_lines)
                nlines = len(lines)
                if out_lines_number < nlines:
                    print("out_lines_number < nlines: %d < %d" % (out_lines_number, nlines))
                    translated_lines.extend([""] * (nlines - out_lines_number))
                olines = []
                for i in range(nlines):
                    if lines[i][1]:
                        olines.append("%s\t%s\t%s" % (lines[i][0], lines[i][1], translated_lines[i]))
                    else:
                        olines.append("%s\t%s" % (lines[i][0], translated_lines[i]))
                output_queue.put(olines)
                time.sleep(1)
                break
            else:
                print("error")
                proxy = get_proxy()
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exit with Ctrl + c")
            raise
        except Exception as e:
            print("Unexpected error:", sys.exc_info()[0])
            proxy = get_proxy()
            time.sleep(1)
            log.error("unexpected error:")
            log.error(e)
        retries_count += 1
    if retries_count >= max_retries_count:
        log.error("Fail to download:")
        log.error("---------------------------")
        log.error("\tlines:")
        log.error(lines)
        log.error("---------------------------")
    return proxy


def translate_content():
    query = query_queue.get()
    proxy = get_proxy()

    while query:
        proxy = call_translation_api(query, proxy)
        query = query_queue.get()


def output_result(target_file):
    output = output_queue.get()
    while output:
        for line in output:
            target_file.write(line)
            target_file.write('\n')
            target_file.flush()
        output = output_queue.get()


def add_line_parts(lines, line_parts):
    if len(line_parts) == 2:
        lines.append((line_parts[0], line_parts[1].strip()))
    else:
        if line_parts[0].endswith('\n'):
            lines.append((line_parts[0][:-1], None))
        else:
            lines.append((line_parts[0][:-1], None))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source_file", required=True, help="Required, specify the source file path.")
    parser.add_argument("-t", "--target_file", required=True, help="Required, specify the target file path.")
    parser.add_argument("-sl", "--source_language", default="en",
                        help="specify the source language. The default value is \"en\".")
    parser.add_argument("-tl", "--target_language", default="zh",
                        help="specify the target language. The default value is \"zh\".")
    parser.add_argument("-tpn", "--translate_processes_num", default="1",
                        help="specify the number of translate processes. The default value is 1.")
    parser.add_argument("-ip", "--ip_pool", default='', help='Optional, specify the ip pool address')
    parsed_args = parser.parse_args()
    print(parsed_args)

    source_file_name = parsed_args.source_file
    target_file_name = parsed_args.target_file
    source_language = parsed_args.source_language
    target_language = parsed_args.target_language
    translate_processes_num = int(parsed_args.translate_processes_num)
    ip_pool = parsed_args.ip_pool

    source_lines = Common.count_lines_of_file(source_file_name)
    ignore_lines = []
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

    try:
        output_process = multiprocessing.Process(target=output_result, args=(target_file,))
        output_process.start()
        translate_process_list = [multiprocessing.Process(target=translate_content, args=()) for _ in
                                  range(translate_processes_num)]
        for tp in translate_process_list:
            tp.start()

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
            line_parts = line.split('\t', maxsplit=1)

            line_size_in_bytes = sys.getsizeof(line_parts[0]) + 1

            # if a line is too large, ignore it
            if line_size_in_bytes > per_size_in_byte:
                ignore_lines.append(line)
                continue

            lines_size_in_bytes += line_size_in_bytes
            add_line_parts(lines, line_parts)
            if lines_size_in_bytes >= per_size_in_byte:
                query_queue.put(lines)
                processed_lines += len(lines)
                speed = (processed_lines - save_offset_lines) / (time.time() - start_time)
                print("processed_lines: " + str(processed_lines))
                print("speed: " + str(speed) + " lines/sec")
                print("remaining time: " + str(datetime.timedelta(seconds=(source_lines - processed_lines) / speed)))
                lines = []
                lines_size_in_bytes = 0
        if len(lines) > 0:
            query_queue.put(lines)
            processed_lines += len(lines)
            print("processed_lines: " + str(processed_lines))

        source_file.close()
        for tp in translate_process_list:
            query_queue.put(None)

        for tp in translate_process_list:
            tp.join()

        output_queue.put(None)
        output_process.join()

        print("total time: %r" % (time.time() - start_time))
        print("total processed lines: %r" % (processed_lines - save_offset_lines))

    except (KeyboardInterrupt, SystemExit):
        output_process.terminate()
    target_file.close()

    log.warning("\nThese lines can't be translated and are ignored because they are too large in source file %s!" % source_file_name)
    log.warning('\n'.join(ignore_lines))

