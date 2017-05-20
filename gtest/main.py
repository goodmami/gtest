#!/usr/bin/env python3

"""
gTest - command-line grammar testing

Usage:
  gtest (--help|--version)
  gtest [-v...|-q] [options] <command> [<args>...]

Note: When paths begin with a colon (e.g. :ace/config.tdl), they are
      joined to the pertinent RELPATH; generally this is the value of
      --grammar-dir, but when selecting tests it is --profiles.

Commands:
  r, regression               compare parsed outputs to gold profiles
  c, coverage                 evaluate parser coverage
  m, semantics                validate semantics in parser outputs

General Options:
  -v, --verbose               increase stdout/stderr verbosity
  -q, --quiet                 don't print to stdout/stderr
  -c WHEN, --color WHEN       use ANSI color codes [default: auto]
  -G DIR, --grammar-dir DIR   grammar directory [default: ./]
  -W DIR, --working-dir DIR   testing directory (temporary if unset)

Grammar Options (RELPATH: --grammar-dir):
  -A PATH, --ace-config PATH  config file for ACE [default: :ace/config.tdl]
  -C PATH, --compiled-grammar PATH
                              grammar binary; if set, don't compile

ACE options:
  -Y, --yy-mode               enable yy-mode
  -P PRE, --preprocessor PRE  preprocess input with PRE before it gets to ACE
  --ace-opts OPTS             additional option string for ACE (e.g. '-n5')
"""

import sys
import os
import shlex
import logging

from docopt import docopt

from gtest.__about__ import __version__
import gtest.regression
import gtest.coverage
import gtest.semantics
# NEWMOD: import new test modules here

COMMANDS = {
    'r': gtest.regression,
    'regression': gtest.regression,
    'c': gtest.coverage,
    'coverage': gtest.coverage,
    'm': gtest.semantics,
    'semantics': gtest.semantics,
    # NEWMOD: add command names and aliases here
}

def main():
    args = docopt(
        __doc__,
        version='gtest {}'.format(__version__),
        options_first=True
    )
    try:
        args = _validate_args(args)
    except ValueError as ex:
        exit(ex)

    logging.basicConfig(level=50 - ((args['--verbose'] + 2) * 10))

    cmd = args['<command>'].lower()
    if cmd not in COMMANDS:
        raise Exception('Invalid test command: {}'.format(cmd))        
    test = COMMANDS[cmd]
    

    argv = []
    test = None
    if args['<command>'].lower() in ('r', 'regression'):
        import gtest.regression as test
        argv.append('regression')
    elif args['<command>'].lower() in ('c', 'coverage'):
        import gtest.coverage as test
        argv.append('coverage')
    elif args['<command>'].lower() in ('m', 'semantics'):
        import gtest.semantics as test
        argv.append('semantics')
    # other commands here
    # elif args['<command>'] in ('X', 'xylophone'):
    #     import gtest.xylophone as test
    if test is None:
        raise Exception('Invalid test: {}'.format(args['<command>']))

    argv.extend(args['<args>'])

    cmdargs = docopt(test.__doc__, argv=argv)
    args.update(cmdargs)
    test.run(args)

def _validate_args(args):
    args = dict(args)  # make a copy

    if args['--quiet']:
        args['--verbose'] = 0

    if args['--color'] not in ('auto', 'always', 'never'):
        raise ValueError('--color value must be one of: auto, always, never')
    elif (args['--color'] == 'never' or
          (args['--color'] == 'auto' and not sys.stdout.isatty())):
        import gtest.util
        gtest.util.color = gtest.util.nocolor

    if args['--grammar-dir'] and not os.path.isdir(args['--grammar-dir']):
        raise ValueError('--grammar-dir, if set, must point to a directory')

    if args['--working-dir'] and not os.path.isdir(args['--working-dir']):
        raise ValueError('--working-dir, if set, must point to a directory')

    # if art_opts is user-configurable in the future, use
    # shlex.split(args['--art-opts'] or '')
    args['--art-opts'] = []
    args['--ace-opts'] = shlex.split(args['--ace-opts'] or '')
    if args['--yy-mode']:
        args['--ace-opts'].append('-y')
        args['--art-opts'].append('-Y')

    return args

if __name__ == '__main__':
    main()
