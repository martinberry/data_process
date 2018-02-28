# -*- coding: utf-8 -*-
from rule import *
import rule_engine
import os
import traceback
import sys
reload(sys)
sys.setdefaultencoding('utf8')


class Generator_Loop_File_List(object):
    def __init__(self, files):
        if not os.path.exists(files[0]):
            print 'file %s does not exist' % files[0]
            raise Exception
        self.flist = open(files[0]).readlines()

    def generate(self):
        for f in self.flist:
            f = f.strip()
            if not os.path.exists(f):
                print 'file %s does not exist, bypass' % f
                continue
            yield f


class Run_Schema(Rule_File):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.set_desc('File: run schema per generator', self)
        if 'schema' in kwargs: self.schema = kwargs['schema']
        else:
            print 'schema field is required, check your shcema'
            raise Exception
        if 'generator' in kwargs:
            self.generator = kwargs['generator']
        else:
            print 'generator field is required, check your shcema'
            raise Exception
        self.engine = rule_engine.RuleEngine(self.schema, ".")
        self.rerun = 0
        if 'rerun' in kwargs: self.rerun = kwargs['rerun']

    def run(self, files):
        succ_f = self.output + 'succ'
        fail_f = self.output + 'fail'
        cnt = 0

        generator = eval(self.generator)(files)

        with open(succ_f, 'w') as sf:
            with open(fail_f, 'w') as ff:

                for f in generator.generate():
                    cnt += 1
                    workdir = os.path.basename(f)
                    self.engine.set_workdir(workdir)
                    # print "run schema %s on file %s" % (self.schema, f)
                    try:
                        self.engine.run([f])
                        sf.write("%s\t%s\n" % (f, os.path.abspath(workdir)))
                    except Exception:
                        traceback.print_exc()
                        ff.write("%s\t%s\n" % (f, os.path.abspath(workdir)))
                        exit(1)
                    if cnt % 5 == 0:
                        print "^^^^^^^^^^ finished %d files ^^^^^^^^^^^^^" % cnt

        print "Done: ^^^^^^^^^^ finished total %d files ^^^^^^^^^^^^^" % cnt
        return [succ_f, fail_f]