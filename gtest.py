#!/usr/bin/env python3

from __future__ import print_function
import sys
import os
from os.path import abspath, join as pjoin, exists
import subprocess
import tempfile
import logging
from contextlib import contextmanager
from delphin import itsdb
from delphin.mrs import simplemrs
from delphin.mrs.compare import compare_bags

# thanks: http://stackoverflow.com/questions/6194499/python-os-system-pushd
@contextmanager
def pushd(path):
    prev_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(prev_dir)

def logtee(s, loglevel, logfile):
    logging.log(loglevel, s)
    print(s, file=logfile or sys.stderr)

def debug(s, logfile): logtee(s, logging.DEBUG, logfile)
def info(s, logfile): logtee(s, logging.INFO, logfile)
def warning(s, logfile): logtee(s, logging.WARNING, logfile)
def error(s, logfile): logtee(s, logging.ERROR, logfile)

def red(s): return '\x1b[31m{}\x1b[0m'.format(s)
def green(s): return '\x1b[32m{}\x1b[0m'.format(s)

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
    debug('Compiling grammar at {}'.format(abspath(cfg_path)), log)
    try:
        subprocess.check_call(
            ['ace', '-g', cfg_path, '-G', out_path],
            stdout=log, stderr=log, close_fds=True
        )
    except (subprocess.CalledProcessError, OSError):
        error(
            'Failed to compile grammar with ACE. See {}'
            .format(abspath(log.name) if log is not None else '<stderr>'),
            log
        )
        raise
    debug('Compiled grammar written to {}'.format(abspath(out_path)), log)

def mkprof(skel_dir, dest_dir, log=None):
    debug('Preparing profile: {}'.format(abspath(skel_dir)), log)
    try:
        subprocess.check_call(
            ['mkprof', '-s', skel_dir, dest_dir],
            stdout=log, stderr=log, close_fds=True
        )
    except (subprocess.CalledProcessError, OSError):
        error(
            'Failed to prepare profile with mkprof. See {}'
            .format(abspath(log.name) if log is not None else '<stderr>'),
            log
        )
        raise
    debug('Completed running mkprof. Output at {}'.format(dest_dir), log)

def run_art(grm, dest_dir, log=None):
    debug('Parsing profile: {}'.format(abspath(dest_dir)), log)
    try:
        subprocess.check_call(
            ['art', '-a', 'ace -g {}'.format(grm), dest_dir],
            stdout=log, stderr=log, close_fds=True
        )
    except (subprocess.CalledProcessError, OSError):
        error(
            'Failed to parse profile with art. See {}'
            .format(abspath(log.name) if log is not None else '<stderr>'),
            log
        )
        raise
    debug('Completed running art. Output at {}'.format(dest_dir), log)

def compare_mrs(dest_dir, gold_dir, log=None):
    debug('Comparing output ({}) to gold ({})'.format(dest_dir, gold_dir), log)
    test_profile = itsdb.ItsdbProfile(dest_dir)
    gold_profile = itsdb.ItsdbProfile(gold_dir)
    matched_rows = itsdb.match_rows(
        test_profile.read_table('result'),
        gold_profile.read_table('result'),
        'parse-id'
    )
    success = True
    for (key, testrows, goldrows) in matched_rows:
        (test_unique, shared, gold_unique) = compare_bags(
            [simplemrs.loads_one(row['mrs']) for row in testrows],
            [simplemrs.loads_one(row['mrs']) for row in goldrows]
        )
        if test_unique or gold_unique:
            success = False
        info('{}\t<{},{},{}>'.format(key, test_unique, shared, gold_unique),
              log)
    debug('Completed comparison. Test {}.'
          .format('succeeded' if success else 'failed'),
          log)
    return success


def regr_test(args):
    tmp = temp_dir()
    pass_msg = green('pass')
    fail_msg = red('fail')
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
                success = compare_mrs(dest, gold, log=logfile)
                print('{}\t{}'.format(pass_msg if success else fail_msg, prof))


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
