#encoding=utf-8
'''
Bifrost module, which is for pre & post text replacing.
'''

import codecs
import os
import threading
import time

import pygtrie

MAX_INSTANCE = 2

def is_entity_tag(txt):
    '''
    Test if the txt is an entity tag.
    TODO: Finish the entity tag testing logic.
    '''
    return False

def entity_tag_with_id(entity_tag, idstr):
    '''
    Add id with entity tag, for unique purpose.
    '''
    return entity_tag + "_" + idstr

class Bifrost(object):
    '''
    This class is for pre & post text replacing.
    '''

    def __init__(self, rule_config_path):
        self.pre_trie = pygtrie.StringTrie(separator=u" ")
        self.post_trie = pygtrie.StringTrie(separator=u" ")
        with codecs.open(rule_config_path, 'r', 'utf-8') as rule_config_file:
            for line in rule_config_file:
                rule_definition_list = line.strip(u'\n').split(u'\t')
                rule_id = rule_definition_list[0]
                if rule_definition_list[1] and rule_definition_list[2]:
                    pre_replacing = rule_definition_list[2]
                    if is_entity_tag(pre_replacing):
                        self.pre_trie[rule_definition_list[1]] =\
                            entity_tag_with_id(pre_replacing, rule_id)
                    else:
                        self.pre_trie[rule_definition_list[1]] = pre_replacing

                if rule_definition_list[3] and rule_definition_list[4]:
                    post_to_be_replaced = rule_definition_list[3]
                    if is_entity_tag(post_to_be_replaced):
                        self.post_trie[entity_tag_with_id(post_to_be_replaced, rule_id)] =\
                            rule_definition_list[4]
                    else:
                        self.post_trie[rule_definition_list[3]] = rule_definition_list[4]

    def pre_process(self, line):
        '''
        Text replacing with raw input.
        '''
        line_len = len(line)
        i = 0
        output_line = u''
        while i < line_len:
            if line[i] != u' ':
                longest_prefix = self.pre_trie.longest_prefix(line[i:])
                if longest_prefix[0]:
                    #Match, replacing. longest_prefix[0] is the key, longest_prefix[1] is the value.
                    output_line += longest_prefix[1]
                    i += len(longest_prefix[0])
                else:
                    #Not match, seek to next word.
                    while i < line_len and line[i] != u' ':
                        output_line += line[i]
                        i += 1
            else:
                output_line += line[i]
                i += 1
        return output_line

    def post_process(self, line):
        '''
        Text replacing with translated result.
        '''
        try:
            line = line.decode('utf-8')
        except:
            pass

        line_len = len(line)
        i = 0
        output_line = u''
        while i < line_len:
            if line[i] != u' ':
                longest_prefix = self.post_trie.longest_prefix(line[i:])
                if longest_prefix[0]:
                    #Match, replacing. longest_prefix[0] is the key, longest_prefix[1] is the value.

                    output_line += longest_prefix[1]
                    i += len(longest_prefix[0])
                else:
                    #Not match, seek to next word.
                    while i < line_len and line[i] != u' ':
                        output_line += line[i]
                        i += 1
            else:
                output_line += line[i]
                i += 1
        return output_line

class BifrostAutoReLoader(object):
    '''
    Auto Reloader for Bifrost. It will detect the file changes
    every 30 seconds.
    '''
    def __init__(self, rule_config_path):
        self.rule_config_path = rule_config_path
        self.bifrost_list = []
        self.bifrost_list.append(Bifrost(rule_config_path))
        self.bifrost_index = 0
        self.bifrost_list.append(None)
        self.thread = threading.Thread(target=self.monitor)
        self.thread.start()

    def pre_process(self, line):
        '''
        Proxy to pre_process of atcual Bifrost instance.
        '''
        stime = time.time()
        ret = self.bifrost_list[self.bifrost_index].pre_process(line)
        print "bifrost pre_process time:", (time.time() - stime)
        return ret

    def post_process(self, line):
        '''
        Proxy to post_process of atcual Bifrost instance.
        '''
        stime = time.time()
        ret = self.bifrost_list[self.bifrost_index].post_process(line)
        print "bifrost post_process time:", (time.time() - stime)
        return ret

    def monitor(self):
        '''
        Minotor the file changes and reload the data.
        '''
        last_stat = os.stat(self.rule_config_path)
        last_mtime = int(last_stat.st_mtime)
        while True:
            time.sleep(30)
            current_stat = os.stat(self.rule_config_path)
            current_mtime = int(current_stat.st_mtime)
            if current_mtime != last_mtime:
                print "now:", int(time.time()), ",last_mtime:", \
                    last_mtime, ",current_mtime:", current_mtime
                print "reload bifrost:", self.rule_config_path
                new_bifrost = Bifrost(self.rule_config_path)
                new_index = (self.bifrost_index + 1) % MAX_INSTANCE
                self.bifrost_list[new_index] = new_bifrost
                self.bifrost_index = new_index
                last_mtime = current_mtime
                print "reload finished"
