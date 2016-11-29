#!/usr/bin/env python3

"""
gTest - command-line grammar testing

Usage:
  gtest (--help|--version)
  gtest [-v|-vv|-vvv] [options] <command> [<args>...]

Note: When paths begin with a colon (e.g. :ace/config.tdl), they are
      joined to the pertinent RELPATH; generally this is {grammar-dir}/,
      but for skeleton-based tests it is {skeletons}/.

Commands:
  R, regression               compare parsed outputs to gold profiles
  C, coverage                 evaluate parser coverage
  M, semantics                validate semantics in parser outputs

General Options:
  -v, --verbose               increase logging verbosity
  -q, --quiet                 disable logging
  -c WHEN, --color WHEN       use ANSI color codes [default: auto]
  -G DIR, --grammar-dir DIR   grammar directory [default: ./]
  -W DIR, --working-dir DIR   testing directory (temporary if unset)

Grammar Options (RELPATH: {grammar-dir}):
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

__version__ = '0.2.0'

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


    argv = [args['<command>']] + args['<args>']

    test = None
    if args['<command>'] in ('R', 'regression'):
        import gtest.regression as test
    elif args['<command>'] in ('C', 'coverage'):
        import gtest.coverage as test
    elif args['<command>'] in ('M', 'semantics'):
        import gtest.semantics as test
    # other commands here
    # elif args['<command>'] in ('X', 'xylophone'):
    #     import gtest.xylophone as test
    if test is None:
        raise Exception('Invalid test: {}'.format(args['<command>']))

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
