
import sys
import os
from os.path import (
    abspath, relpath, basename, join as pjoin, exists, isdir, getsize
)

import logging
import tempfile
import subprocess
from contextlib import contextmanager
from collections import namedtuple

from gtest.exceptions import GTestError

from delphin.interfaces import ace


#
# LOGGING
#

def logtee(s, loglevel, logfile):
    logging.log(loglevel, s)
    print(s, file=logfile or sys.stderr)

def debug(s, logfile): logtee(s, logging.DEBUG, logfile)
def info(s, logfile): logtee(s, logging.INFO, logfile)
def warning(s, logfile): logtee(s, logging.WARNING, logfile)
def error(s, logfile): logtee(s, logging.ERROR, logfile)

def red(s): return '\x1b[31m{}\x1b[0m'.format(s)
def green(s): return '\x1b[32m{}\x1b[0m'.format(s)


#
# BASIC DIRECTORIES AND FILES
#

# thanks: http://stackoverflow.com/questions/6194499/python-os-system-pushd
@contextmanager
def pushd(path):
    prev_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(prev_dir)


def temp_dir():
    tmp = tempfile.mkdtemp()
    debug('Temporary directory created at {}'.format(tmp), None)
    return tmp


def check_exist(path):
    if exists(path):
        return True
    warning('Path does not exist: {}'.format(abspath(path)), None)
    return False


# KeyPath.key is the pattern given, KeyPath.path is the resolved path
KeyPath = namedtuple('PathKey', ('key', 'path'))


def make_keypath(key, relpath):
    if key.startswith(':'):
        return KeyPath(key, pjoin(relpath, key[1:]))
    else:
        return KeyPath(key, key)


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

#
# Prepare for test run
#

def prepare(args):
    prepare_working_directory(args)
    prepare_compiled_grammar(args)


def prepare_working_directory(args):
    qualifier = ''
    if args.working_dir:
        if not isdir(args.working_dir):
            try:
                os.mkdir(args.working_dir)
                qualifier = 'newly created '
            except OSError:
                error(
                    'Could not create working directory: {}'
                    .format(args.working_dir),
                    None
                )
                raise
        else:
            qualifier = 'existing '
    else:
        args.working_dir = temp_dir()
        qualifier = 'temporary '
    info(
        'Using {}working directory: {}'.format(qualifier, args.working_dir),
        None
    )


def prepare_compiled_grammar(args):
    if not args.working_dir or not isdir(args.working_dir):
        raise GTestError(
            'Cannot compile grammar without a working directory.'
        )
    args.ace_config = make_keypath(args.ace_config, args.grammar_dir)
    if args.compiled_grammar:
        args.compiled_grammar = make_keypath(args.compiled_grammar,
                                             args.grammar_dir)
        if not check_exist(args.compiled_grammar.path):
            raise GTestError(
                'Compiled grammar not found: {}'
                .format(args.compiled_grammar.path)
            )
    else:
        compiled_grammar = pjoin(args.working_dir, 'gram.dat')
        ace_compile(args.ace_config.path, compiled_grammar)
        args.compiled_grammar = compiled_grammar
    info('Using grammar image: {}'.format(args.compiled_grammar), None)


#
# COMPILING AND GETTING GRAMMAR IMAGES
#

def get_grammar(args, tmp):
    if args.compiled_grammar:
        grm = args.compiled_grammar.path
    else:
        grm = pjoin(tmp, 'gram.dat')
        with open(pjoin(tmp, 'ace.log'), 'w') as ace_log:
            ace_compile(args.ace_config, grm, log=ace_log)
    return grm


def ace_compile(cfg_path, out_path, log=None):
    debug('Compiling grammar at {}'.format(abspath(cfg_path)), log)
    ace.compile(cfg_path, out_path, log=log)
    debug('Compiled grammar written to {}'.format(abspath(out_path)), log)


#
# PARSING
#

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