# -*- coding: utf-8 -*-
import codecs
import json
import pprint
import signal
import os
import glob
import uuid
import shutil
import rule_common, rule_zh, rule_en, rule_super, rule
from rule import Context_Rule

debug = 0


class Step(object):
    def __init__(self, step):
        if 'disable' in step:
            self.disable = step['disable']
        else:
            self.disable = 0
        self.name = step['name']
        self.type = step['type']
        self.rules = []
        for rule in step['rules']:
            self.rules.append(eval(rule[0])(**rule[1]))

    def run(self):
        raise NotImplementedError

class SoleLine(Step):
    def __init__(self, step):
        super(SoleLine, self).__init__(step)

    def run(self):
        raise NotImplementedError

    def process(self, line=None):
        if not line: return None
        for rule in self.rules:
            # print rule.printme()
            line = rule.run(line)
            # print line
        return line


class FileStepBase(Step):
    def __init__(self, step):
        super(FileStepBase, self).__init__(step)

        if 'inputs' not in step:
            print 'no inputs in step %s, check schema' % self.name
            raise Exception
        self.inputs = step['inputs']

        if 'outputs' not in step:
            print 'no outputs in step %s, check schema' % self.name
            raise Exception
        self.outputs = step['outputs']

    def run(self):
        raise NotImplementedError

    def gen_temp_file_name(self):
        return "temp_%s" % str(uuid.uuid4().hex)


class FileLinesStep(FileStepBase):
    def __init__(self, step):
        super(FileLinesStep, self).__init__(step)

        if 'replace_empty_line' not in step:
            print 'no replace_empty_line in line type step %s, check schema' % self.name
            raise Exception
        self.replace_empty_line = step['replace_empty_line']

        if len(self.inputs) != 1:
            print 'need exact 1 input file in line type step %s, check schema' % self.name
            raise Exception

        if len(self.outputs) != 2:
            print 'need exact 2 output files in line type step %s, check schema' % self.name
            raise Exception

    def run(self):
        input = self.inputs[0]
        with codecs.open(input, 'r', 'utf-8') as d_f:
            with codecs.open(self.outputs[0], "w", "utf-8") as o_f:
                with codecs.open(self.outputs[1], "w", "utf-8") as r_f:
                    cnt = 0
                    line = d_f.readline()
                    while line:
                        cnt += 1
                        if cnt % 100000 == 0:
                            print "processed %d lines" % cnt
                        line = line.strip("\r\n")
                        orig_line = line

                        if not line:
                            if self.replace_empty_line:
                                o_f.write("%s\n" % self.replace_empty_line)
                            r_f.write("%d\t%s\n" % (cnt, orig_line))
                            line = d_f.readline()
                            continue

                        for rule in self.rules:
                            line = rule.run(line)
                        if not line:
                            if self.replace_empty_line:
                                o_f.write("%s\n" % self.replace_empty_line)
                            r_f.write("%d\t%s\n" % (cnt, orig_line))
                            line = d_f.readline()
                            continue

                        o_f.write("%s\n" % line)

                        line = d_f.readline()
        return self.outputs


class FileStep(FileStepBase):
    def __init__(self, step):
        super(FileStep, self).__init__(step)
        self.temp_outputs = []
    def run(self):

        inputs = self.inputs
        outputs = []
        for rule in self.rules:
            print rule
            outputs = rule.run(inputs)
            inputs = outputs
            self.temp_outputs.extend(outputs)
        if len(outputs) != len(self.outputs):
            print outputs
            print self.outputs
            print 'inconsistant outputs length in step %s, check schema' % self.name
            raise Exception

        for i, o in enumerate(outputs):
            shutil.move(o, self.outputs[i])
        return outputs


class ContextStep(object):
    def __init__(self, step, context):
        if 'disable' in step:
            self.disable = step['disable']
        else:
            self.disable = 0
        self.name = step['name']
        self.type = step['type']
        self.rules = []
        self.temp_outputs=[]
        for rule in step['rules']:
            init_args = rule["init_args"]
            if context:
                update_args = {}
                for arg_key_value in init_args.items():
                    if arg_key_value[1] and\
                        arg_key_value[1].startswith(Context_Rule.CONTEXT_VARIABLE_PREFIX):

                        update_args[arg_key_value[0]] =\
                            context[arg_key_value[1][len(Context_Rule.CONTEXT_VARIABLE_PREFIX):]]
                    else:
                        update_args[arg_key_value[0]] = arg_key_value[1]
                init_args = update_args
            self.rules.append(
                Context_Rule(
                    eval(rule['name'])(**init_args),
                    rule['run_params'],
                    rule['run_outputs']))

    def execute(self, context):
        for rule in self.rules:
            rule.run(context)


class RuleEngine(object):
    def __init__(self, schema_f, workdir, mode='file', rule_engine_context=None):
        self.mode = mode
        self.workdir = ''
        if mode == 'file':
            self.set_workdir(workdir)
            # copy schema file to working dir, just for backup purpose
            # shutil.copyfile(schema_f, os.path.join(workdir, os.path.basename(schema_f)))
        self.rule_engine_context = rule_engine_context
        schema_dict = self.load_schema(schema_f)
        self.init_schema(schema_dict)
        self.sig = signal.SIGINT
        self.released = False
        self.interrupted = False
        self.released = False
        self.original_handler = signal.getsignal(self.sig)

    def set_workdir(self, dir):
        if not os.path.exists(dir):
            print 'create working dir %s' % dir
            os.mkdir(dir)
        self.workdir = dir

    def __enter__(self):
        self.interrupted = False
        self.released = False
        self.original_handler = signal.getsignal(self.sig)

        def handler(signum, frame):
            self.release()
            self.interrupted = True

        signal.signal(self.sig, handler)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        pass

    def remove_file(self, f):
        try: os.remove(f)
        except: pass

    def release(self):
        if debug: return True

        if self.released:
            return False

        print "=====> cleaning unused step output files and temporary files"

        final_outputs = set(self.schema['final_outputs'])
        inputs = []
        if 'inputs' in self.schema:
            inputs = self.schema['inputs']
        for step in self.schema['steps']:
            print 'cleaning execute plan step %s' % step
            for o in step.outputs:
                if o not in final_outputs and o not in inputs:
                    self.remove_file(o)

        for step in self.schema['steps']:
            if hasattr(step,'temp_outputs'):
                map(self.remove_file,step.temp_outputs)

        signal.signal(self.sig, self.original_handler)
        self.released = True
        return True

    def create_step(self, step):
        t = step['type']
        if t == 'line': return FileLinesStep(step)
        elif t == 'file': return FileStep(step)
        elif t == 'sole_line': return SoleLine(step)
        elif t == 'context': return ContextStep(step, self.rule_engine_context)
        else:
            print 'invalid type %s of step %s, check schema' % (t, step['name'])
            raise Exception

    def init_schema(self, schema_dict):
        self.schema = schema_dict.copy()
        print '=====> initialize execute plan'
        self.schema['steps'] = [self.create_step(step) for step in self.schema['steps']]
        if debug: pprint.pprint(self.schema)
        if self.mode == 'file':
            if 'final_outputs' not in self.schema:
                print 'lack or invalid "final_outputs" field, check schema'
                raise Exception
            if 'inputs' in self.schema:
                for f in self.schema['inputs']:
                    if not os.path.exists(f):
                        print "file %s in inputs does not exists, check schema" % f
                        raise Exception

    def load_schema(self, schema_f):
        with open(schema_f) as f:
            schema = json.load(f)
        if debug: pprint.pprint(schema)
        return schema

    def first_inputs(self, inputs):
        if inputs and len(inputs) > 0:
            if 'inputs' in self.schema:
                print 'will override schema inputs from --infiles %s' % str(inputs)
                self.schema['inputs'] = inputs
                for f in self.schema['inputs']:
                    shutil.copyfile(f, os.path.join(self.workdir, os.path.basename(f)))
            else:
                print 'will override first step inputs from --infiles %s' % str(inputs)
                self.schema['steps'][0].inputs = inputs
                self.schema['steps'][0].inputs = [os.path.abspath(f) for f in self.schema['steps'][0].inputs]
        else:
            for f in self.schema['inputs']:
                shutil.copyfile(f, os.path.join(self.workdir, os.path.basename(f)))

    def check_need_rerun(self):
        startover = 1
        if 'startover' in self.schema: startover = self.schema['startover']
        if startover: return 1
        else:
            for f in self.schema['final_outputs']:
                if not os.path.exists(f):
                    # print "still need to rerun since %s does not exist in %s, although requested not rerun" % (f, os.getcwd())
                    return 1
            return 0

    def run(self, inputs):
        if self.mode != 'file':
            print 'RuleEngine run() only apply to file mode, check your code'
            raise Exception

        self.first_inputs(inputs)
        # will change to working dir
        cur_dir = os.getcwd()
        os.chdir(self.workdir)

        if not self.check_need_rerun():
            os.chdir(cur_dir)
            print '====> skip run as startover field is set and all files in final_ouputs are there'
            return

        self.released = False
        steps = self.schema['steps']
        try:
            for step in steps:
                print "=====> run step %s" % step.name
                if step.disable:
                    print 'step %s is disabled' % step.name
                    continue
                step.run()
        finally:
            self.release()
            os.chdir(cur_dir)

    def process(self, inputs, verbose=False):
        if self.mode != 'lib':
            print 'RuleEngine process() only apply to lib mode, check your code'
            raise Exception

        steps = self.schema['steps']
        for step in steps:
            if verbose: print "=====> run step %s" % step.name
            if step.disable:
                print 'step %s is disabled' % step.name
                continue
            inputs = step.process(inputs)
        return inputs

    def execute(self, run_context, verbose=False):
        '''
        This function is used for Context_Rule. see Context_Rule for more details.
        '''
        steps = self.schema['steps']
        if verbose:
            print "Before execution:\n", run_context
        for step in steps:
            if step.disable:
                print 'step %s is disabled' % step.name
                continue
            step.execute(run_context)

            if verbose:
                print "After %s execution:\n" % step.name, run_context