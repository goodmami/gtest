#!/usr/bin/env python3

from __future__ import print_function
import sys
import os
from os.path import (
    abspath, relpath, basename, join as pjoin, exists, getsize
)
import subprocess
import tempfile
from glob import glob
from fnmatch import fnmatch
import logging
from contextlib import contextmanager

from delphin import itsdb
from delphin.interfaces import ace
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

def dir_is_profile(path, skeleton=False):
    if skeleton:
        files = ['item', 'relations']
    else:
        # this should be enough
        files = ['item', 'relations', 'parse', 'result']
    try:
        return all(getsize(pjoin(path, f)) > 0 for f in files)
    except OSError:
        return False

def normalize_profile_path(prof, path):
    if prof.startswith(':'):
        prof = pjoin(path, prof[1:])
    else:
        prof = prof
    return prof

def get_skel_and_gold_paths(prof, skel_dir, gold_dir):
    skel_dir = abspath(skel_dir)
    skel_pattern = abspath(normalize_profile_path(prof, skel_dir))
    for skel_path in glob(skel_pattern):
        gold_path = abspath(pjoin(gold_dir, relpath(skel_path, skel_dir)))
        yield (skel_path, gold_path)

def get_profile_name(path, rel_dir):
    return ':{}'.format(relpath(path, rel_dir))

def find_testable_profiles(profs, skel_dir, gold_dir):
    abs_skel_dir = abspath(skel_dir)
    for prof in profs:
        for skel, gold in get_skel_and_gold_paths(prof, skel_dir, gold_dir):
            if not dir_is_profile(skel, skeleton=True):
                logging.info('Directory is not a skeleton (skipping test): {}'
                             .format(skel))
                continue
            if not dir_is_profile(gold):
                logging.info('Could not find gold profile for skeleton '
                             '(skipping test): {}'.format(skel))
                continue
            name = get_profile_name(skel, abs_skel_dir)
            yield (name, skel, gold)


def ace_compile(cfg_path, out_path, log=None):
    debug('Compiling grammar at {}'.format(abspath(cfg_path)), log)
    ace.compile(cfg_path, out_path, log=log)
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
    if args.list_profiles:
        regr_list_profiles(args)
        return
    tmp = temp_dir()
    with pushd(args.grammar_dir):
        if args.compiled_grammar:
            grm = args.compiled_grammar
        else:
            grm = pjoin(tmp, 'gram.dat')
            with open(pjoin(tmp, 'ace.log'), 'w') as ace_log:
                ace_compile(args.ace_config, grm, log=ace_log)
        logging.debug('Using grammar image at {}'.format(abspath(grm)))

        profs = find_testable_profiles(
            args.profiles, args.skel_dir, args.gold_dir
        )
        for (name, skel, gold) in profs:
            logging.info('Regression testing profile: {}'.format(name))
            dest = pjoin(tmp, basename(skel))
            logf = pjoin(tmp, 'run-{}.log'.format(name))
            pass_msg = '{}\t{}'.format(green('pass'), name)
            fail_msg = '{}\t{}; See {}'.format(red('fail'), name, logf)
            if not (check_exist(skel) and check_exist(gold)):
                logging.error('Skipping profile {}'.format(name))
                continue
            with open(logf, 'w') as logfile:
                mkprof(skel, dest, log=logfile)
                run_art(grm, dest, log=logfile)
                success = compare_mrs(dest, gold, log=logfile)
                print(pass_msg if success else fail_msg)


def regr_list_profiles(args):
    # if not True, it's a test pattern
    pattern = '*'
    if args.list_profiles is not True:
        pattern = args.list_profiles
    abs_gram_path = abspath(args.grammar_dir)
    with pushd(args.grammar_dir):
        skels = []
        for (dirpath, dirnames, filenames) in os.walk(args.skel_dir):
            if dir_is_profile(dirpath, skeleton=True):
                skels.append(dirpath)
            dirnames.sort()  # this affects traversal order
        profs = find_testable_profiles(skels, args.skel_dir, args.gold_dir)
        for (name, skel, gold) in profs:
            relskel = relpath(skel, abs_gram_path)
            relgold = relpath(gold, abs_gram_path)
            if fnmatch(name, pattern) or fnmatch(relskel, pattern):
                print('{}\t{}:{}'.format(name, relgold, relskel))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        prog='gtest',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Test DELPH-IN grammars from the commandline',
        epilog='examples:\n'
            '  gtest -G ~/mygram R --list-profiles\n'
            '  gtest -G ~/mygram R :\*\n'
            '  gtest -G ~/mygram -C ~/mygram.dat R ~/mygram/tsdb/skeletons/*\n'
            '  gtest -A ~/bin/ace -G ~/mygram R -s tsdb/skels :xyz :abc\*\n'
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
        metavar='PATH',
        help='A pre-compiled grammar image; if unset, the grammar will be '
             'compiled to a temporary location.'
    )
    subparsers = parser.add_subparsers(help='sub-command help')

    regr = subparsers.add_parser(
        'R', help='regression test'
    )
    regr.add_argument(
        'profiles',
        nargs='*',
        default=[':*'],
        help='One or more profiles to test. Each profile can be a filesystem '
             'path, or a colon-prefixed profile name (e.g. :prof1) found at '
             '{skel-dir/}profile. The path or name is used for the skeleton, '
             'then the gold profile is found at {gold-dir/}basename(profile). '
             'Globbing asterisks may be used, but for profile names they might '
             'need to be escaped to avoid shell expansion.'
    )
    regr.add_argument(
        '-s', '--skel-dir',
        default='tsdb/skeletons', metavar='DIR',
        help='The directory with [incr tsdb()] skeletons, relative to '
             'gram-dir (default: {grammar-dir/}tsdb/skeletons/).'
    )
    regr.add_argument(
        '-g', '--gold-dir',
        default='tsdb/gold', metavar='DIR',
        help='The directory with [incr tsdb()] gold profiles, relative '
             'to gram-dir (default: {grammar-dir/}tsdb/gold/).'
    )
    regr.add_argument(
        '-l', '--list-profiles',
        nargs='?', const=True,
        help="Don't run the tests, but list testable profiles (those findable "
             "in both {skel-dir} and {gold-dir}."
    )
    regr.set_defaults(func=regr_test)

    args = parser.parse_args()
    logging.basicConfig(level=50-(args.verbosity*10))

    args.func(args)
