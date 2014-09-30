#!/usr/bin/env python2

from __future__ import print_function
import sys
import os
from os.path import abspath, join as pjoin, exists
import subprocess
import tempfile
import logging
from contextlib import contextmanager
#from delphin.mrs import simplemrs

# thanks: http://stackoverflow.com/questions/6194499/python-os-system-pushd
@contextmanager
def pushd(path):
    prev_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(prev_dir)

def temp_dir():
    tmp = tempfile.mkdtemp()
    logging.debug('Temporary directory created at {}'.format(tmp))
    return tmp

def check_exist(path):
    if exists(path):
        return True
    logging.warning('Path does not exist: {}'.format(abspath(path)))
    return False

def ace_compile(cfg_path, out_path, log=None):
    logging.debug('Compiling grammar at {}'.format(abspath(cfg_path)))
    try:
        subprocess.check_call(
            ['ace', '-g', cfg_path, '-G', out_path],
            stdout=log, stderr=log, close_fds=True
        )
    except (subprocess.CalledProcessError, OSError):
        logging.error(
            'Failed to compile grammar with ACE. See {}'
            .format(abspath(log.name) if log is not None else '<stderr>')
        )
        raise
    logging.debug('Compiled grammar written to {}'.format(abspath(out_path)))

def mkprof(skel_dir, dest_dir, log=None):
    logging.debug('Preparing profile: {}'.format(abspath(skel_dir)))
    try:
        subprocess.check_call(
            ['mkprof', '-s', skel_dir, dest_dir],
            stdout=log, stderr=log, close_fds=True
        )
    except (subprocess.CalledProcessError, OSError):
        logging.error(
            'Failed to prepare profile with mkprof. See {}'
            .format(abspath(log.name) if log is not None else '<stderr>')
        )
        raise
    logging.debug('Completed running mkprof. Output at {}'.format(dest_dir))

def run_art(grm, dest_dir, log=None):
    logging.debug('Parsing profile: {}'.format(abspath(dest_dir)))
    try:
        subprocess.check_call(
            ['art', '-a', 'ace -g {}'.format(grm), dest_dir],
            stdout=log, stderr=log, close_fds=True
        )
    except (subprocess.CalledProcessError, OSError):
        logging.error(
            'Failed to parse profile with art. See {}'
            .format(abspath(log.name) if log is not None else '<stderr>')
        )
        raise
    finally:
        log.close()
    logging.debug('Completed running art. Output at {}'.format(dest_dir))

def regr_test(args):
    tmp = temp_dir()
    with pushd(args.grammar_dir):
        if args.compiled_grammar:
            grm = args.compiled_grammar
        else:
            grm = pjoin(tmp, 'gram.dat')
            with open(pjoin(tmp, 'ace.log'), 'w') as ace_log:
                ace_compile(args.ace_config, grm, log=ace_log)
        logging.debug('Using grammar image at {}'.format(abspath(grm)))

        for prof in args.profiles:
            logging.info('Regression testing profile: {}'.format(prof))
            skel = pjoin(args.skel_dir, prof)
            gold = pjoin(args.gold_dir, prof)
            dest = pjoin(tmp, prof)
            if not (check_exist(skel) and check_exist(gold)):
                logging.error('Skipping profile {}'.format(prof))
                continue
            with open(pjoin(tmp, '{}.log'.format(prof)), 'w') as logfile:
                mkprof(skel, dest, log=logfile)
                run_art(grm, dest, log=logfile)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Test DELPH-IN grammars from the commandline'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count', dest='verbosity', default=2,
        help='Increase the verbosity (can be repeated: -vvv).'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_const', const=0, dest='verbosity',
        help='Set verbosity to the quietest level.'
    )
    #parser.add_argument('-R', '--recursive', action='store_true')
    parser.add_argument(
        '-G', '--grammar-dir',
        default='.', metavar='DIR',
        help='The root directory of a grammar (default ./).'
    )
    parser.add_argument(
        '-A', '--ace-config',
        default='ace/config.tdl', metavar='PATH',
        help='The location of the ACE config file relative to gram-dir '
             '(default: ace/config.tdl).'
    )
    parser.add_argument(
        '-C', '--compiled-grammar',
        help='A pre-compiled grammar image; if unset, the grammar will be '
             'compiled to a temporary location.'
    )
    subparsers = parser.add_subparsers(help='sub-command help')

    regr = subparsers.add_parser(
        'R', help='regression test'
    )
    regr.add_argument(
        'profiles',
        nargs='+',
        help='One or more profile directories to test.'
    )
    regr.add_argument(
        '-s', '--skel-dir',
        default='tsdb/skeletons', metavar='DIR',
        help='The directory with [incr tsdb()] skeletons, relative to '
             'gram-dir (default: tsdb/skeletons/).'
    )
    regr.add_argument(
        '-g', '--gold-dir',
        default='tsdb/gold', metavar='DIR',
        help='The directory with [incr tsdb()] gold profiles, relative '
             'to gram-dir (default: tsdb/gold/).'
    )
    regr.set_defaults(func=regr_test)

    args = parser.parse_args()
    logging.basicConfig(level=50-(args.verbosity*10))

    args.func(args)