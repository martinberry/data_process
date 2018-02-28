# -*- coding: utf-8 -*-
#!/usr/bin/python
import argparse
import os
import time
import uuid
import codecs

import rule_engine


def parse_args():
    parser = argparse.ArgumentParser("translation process")
    parser.add_argument("-i", "--infiles", nargs="*", required=False,
                        help="input train data files, could take multiple files as input, and will override 'inputs' field of first step in schema json file")
    parser.add_argument("-s", "--schema", required=True, help="schema file, self explained in example schema file")
    parser.add_argument("-w", "--workdir", required=False, help="working dir. if not existing, will create new one. if not specified, will create a foler with random name")
    return parser.parse_args()


args = parse_args()


def main():
    # check file existing
    infiles = None
    if args.infiles: infiles = args.infiles

    # check schema file
    schema_file = args.schema
    if not os.path.exists(schema_file):
        print ('file %s does not exist' % schema_file)
        raise Exception

    if args.workdir:
        workdir = args.workdir
        if not os.path.exists(args.workdir):
            print ('create working dir %s' % workdir)
            os.mkdir(workdir)
    else:
        workdir = "work_%s" % str(uuid.uuid4().hex)
        print ('not specified working dir, create one with random name: %s' % workdir)
        os.mkdir(workdir)

    st = time.time()
    with rule_engine.RuleEngine(schema_file, workdir) as engine:
        engine.run(infiles)

    print ('[All done!]')
    print ('[Results were saved to: %s]' % workdir)
    print (["Total time: %.2f" % (time.time()-st)])


if __name__ == "__main__":
    main()
