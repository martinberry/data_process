# -*- coding: utf-8 -*-
import re
import subprocess
import os
import uuid


class Rule(object):
    def __init__(self):
        self.desc = ""

    def set_desc(self, desc, o):
        self.desc = "%s - %s" % (desc, o.__class__)
        print self.desc

    def printme(self):
        print self.desc

    def run(self, input):
        raise NotImplementedError


class Rule_Line(Rule):
    def __init__(self, regex_strs=None):
        self.regex = []
        if regex_strs:
            self.regex.extend([(re.compile(s.decode('utf-8'), f), r) for s, f, r in regex_strs])
        super(Rule_Line, self).__init__()
        # print self.regex

    def run(self, line):
        # self.printme()
        if not line: return None
        l = line
        for s, r in self.regex:
            try:
                l = s.sub(r, l)
            except Exception:
                pass
        if not l:
            return None
        return l


class Rule_File(Rule):
    def __init__(self):
        super(Rule_File, self).__init__()
        self.output = self.get_temp_file_name()

    @staticmethod
    def get_temp_file_name():
        return "temp_%s" % str(uuid.uuid4().hex)

    def file_exist(self, file):
        if not os.path.exists(file):
            print 'file %s does not exist' % file
            raise Exception

    def run(self, input):
        raise NotImplementedError


class Rule_File_Shell(Rule_File):
    def __init__(self):
        super(Rule_File_Shell, self).__init__()

    def execute_cmd(self, cmd):
        # check_all will raise exception CalledProcessError if cmd return code is not 0
        self.printme()
        print 'Execute: %s' % cmd
        subprocess.check_call(cmd, shell=True)


class Context_Rule(Rule):
    '''
    Context_Rule is a wrapper of existing Rule. It hiddens the parameters of Rule's run function
    and only expose one context variable. See schema_lib_tech_zh_post_gpu_context.json as example
    on how to use it.
    '''
    CONTEXT_VARIABLE_PREFIX = '$$'

    def __init__(self, rule, params, outputs):
        '''
        rule:
            The internal rule.
        params:
            The params for rule's run function. It's a dictionary, the key is the name of param,
            the value is the value or context variable for the param. Context variable will be
            updated with real value in the context.
        outputs:
            The name of output of rule's run function. It's a list, so that the run function
            can return multiple results. The output of run function will be save as values of
            those names as key in the context.
        '''
        super(Rule, self).__init__()
        self.rule = rule
        self.params = params
        self.desc = "Context_Rule wrapped:\n" + rule.desc
        self.outputs = outputs

    def replace_context_symbol_with_value(self, kwparams, run_context):
        '''
        Get parameter value from run_context if it's a context variable, whose string is
        start with CONTEXT_VARIABLE_PREFIX.
        For example, the original kwparams = {"p1":"v1", "p2": "$$v2"}, then
        the output update_params = {"p1", "v1", "p2": "context value for v2"}. "$$v2" starts
        with "$$", which is the context variable, so its value needs to read from context.abs
        While "v1" doesn't starts with "$$", we need to keep this value to return.
        '''
        update_params = {}
        for kwvalue in kwparams.items():
            if kwvalue[1] and kwvalue[1].startswith(Context_Rule.CONTEXT_VARIABLE_PREFIX):
                update_params[kwvalue[0]] =\
                    run_context[kwvalue[1][len(Context_Rule.CONTEXT_VARIABLE_PREFIX):]]
            else:
                update_params[kwvalue[0]] = kwvalue[1]
        return update_params

    def run(self, run_context):
        params = self.replace_context_symbol_with_value(self.params, run_context)

        ret = self.rule.run(**params)
        if ret and self.outputs:
            if len(self.outputs) > 1:
                for i in range(len(self.outputs)):
                    run_context[self.outputs[i]] = ret[i]
            else:
                run_context[self.outputs[0]] = ret
