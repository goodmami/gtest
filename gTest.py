#!/usr/bin/env python3

#from __future__ import print_function
import sys
import shlex
import logging

from gtest import (regression, coverage, semantics)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        prog='gTest',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=
'Test DELPH-IN grammars from the commandline.\n\n'
'Paths in arguments may often be prefixed with a colon, making it relative\n'
'to a pertinent directory (explained by RELPATH in each argument below).',
        epilog='examples:\n'
            '  regression-test the mrs profile:\n'
            '    gTest -G ~/zhong/cmn/zhs R :mrs\n'
            '  regression-test all profiles with the robust settings:\n'
            '    gTest -G ~/zhong/cmn/zhs -A :ace/config-robust.tdl R\n'
            '  test coverage of the mrs profile with a pre-compiled grammar:\n'
            '    gTest -G ~/jacy -C :jacy.dat C :mrs\n'
            '  test coverage using YY mode and a preprocessor:\n'
            '    gTest -G ~/zhong/cmn/zhs -YP \'python ~/zhong/cmn/zhs/utils/cmn2yy.py\' C'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count', dest='verbosity', default=1,
        help='increase the verbosity (can be repeated: -vvv)'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_const', const=0, dest='verbosity',
        help='set verbosity to the quietest level'
    )
    parser.add_argument(
        '--color',
        choices=('auto', 'always', 'never'),
        default='auto',
        help='show results in color when set to "always" or "auto" in '
            'a tty (default: auto)'
    )
    #parser.add_argument('-R', '--recursive', action='store_true')
    parser.add_argument(
        '-G', '--grammar-dir',
        default='.', metavar='DIR',
        help='root directory of a grammar (default ./)'
    )
    parser.add_argument(
       '-W', '--working-dir',
       metavar='DIR',
       help='directory to store artifacts of the testing process (parsed '
           'profiles, compiled grammars, etc); if unset, a temp directory '
           'will be created'
    )
    parser.add_argument(
        '-A', '--ace-config',
        default=':ace/config.tdl', metavar='[PATH|:RELPATH]',
        help='location of the ACE config file (RELPATH: {grammar-dir}; '
            'default: :ace/config.tdl)'
    )
    parser.add_argument(
        '-C', '--compiled-grammar',
        metavar='[PATH|:RELPATH]',
        help='location of a pre-compiled grammar image (RELPATH: '
            '{grammar-dir}); if unset, the grammar will be compiled to a '
            'temporary location'
    )
    parser.add_argument(
        '-Y', '--yy-mode',
        action='store_true',
        help='enable yy-mode'
    )
    parser.add_argument(
        '-P', '--preprocessor',
        default='', metavar='PREPROC',
        help='pipe input through PREPROC before it gets to ACE'
    )
    parser.add_argument(
        '--ace-opts',
        default='', metavar='OPTS',
        help='additional options to give to ACE, given as a string '
            '(e.g. \'-n5 -Tq\')'
    )
    # currently there's no good case for this, since necessary ones can
    # be guessed (e.g. -e) or given from other gTest options (-Y)
    # If enabled later, remove args.art_opts = [] below
    # parser.add_argument(
    #     '--art-opts',
    #     action='append', metavar='OPTS',
    #     help='additional options to give to art, given as a string'
    # )


    skel_parser = argparse.ArgumentParser(
        add_help=False
    )
    skel_parser.add_argument(
        dest='profiles',
        nargs='*',
        help='Zero or more profiles to test (RELPATH: {skel-dir}). Paths '
            'may include globbing asterisks, although colon-prefixed '
            'relative paths must escape the asterisks to avoid shell '
            'expansion (e.g. :prof\*). If no profiles are given, all '
            'findable profiles (via the --list-profiles option) will '
            'be used.'
    )
    skel_parser.add_argument(
        '-l', '--list-profiles',
        action='store_true',
        help='list testable profiles that are findable with the current '
             'settings'
    )
    skel_parser.add_argument(
        '--skel-dir',
        default=':tsdb/skeletons', metavar='[DIR|:RELPATH]',
        help='directory with [incr tsdb()] skeletons (RELPATH: '
            '{grammar-dir}; default: :tsdb/skeletons/)'
    )

    ##
    ## New commands go below
    ##

    subparsers = parser.add_subparsers(help='sub-command help')

    # Regression tests

    regr = subparsers.add_parser(
        'R',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[skel_parser],
        help='regression test',
        description='Run regression tests that compare the semantics of the current '
            'grammar with a gold profile. Gold profiles are found using the '
            'skeleton profile\'s basename: {gold-dir/}basename(profile).',
        epilog='examples:\n'
            '  gTest -G ~/mygram R --list-profiles\n'
            '  gTest -G ~/mygram R :\*\n'
            '  gTest -G ~/mygram -C ~/mygram.dat R ~/mygram/tsdb/skeletons/*'
    )
    regr.add_argument(
        '--gold-dir',
        default=':tsdb/gold', metavar='[DIR|:RELPATH]',
        help='directory with [incr tsdb()] gold profiles (RELPATH: '
            '{grammar-dir}; default: :tsdb/gold/)'
    )
    regr.set_defaults(test=regression)

    # Coverage tests

    covr = subparsers.add_parser(
        'C',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[skel_parser],
        help='parsing coverage',
        epilog='examples:\n'
            '  gTest -G ~/mygram C --list-profiles\n'
            '  gTest -G ~/mygram C :abc'
    )
    # covr.add_argument(
    #     '--generate',
    #     action='store_true',
    #     help='also test generation coverage'
    # )
    covr.set_defaults(test=coverage)

    # Semantic (MRS) tests

    sem = subparsers.add_parser(
        'M',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[skel_parser],
        help='semantic validity',
        epilog='examples:\n'
            '  gTest -G ~/mygram M --list-profiles\n'
            '  gTest -G ~/mygram M :abc'
    )
    # covr.add_argument(
    #     '--generate',
    #     action='store_true',
    #     help='also test generation coverage'
    # )
    sem.set_defaults(test=semantics)


    args = parser.parse_args()
    logging.basicConfig(level=50-(args.verbosity*10))

    # basic manipulations

    # if art_opts is user-configurable in the future, use
    # shlex.split(args.art_opts)
    args.art_opts = []
    args.ace_opts = shlex.split(args.ace_opts)
    if args.yy_mode:
        args.ace_opts.append('-y')
        args.art_opts.append('-Y')

    if args.color == 'never' or (args.color == 'auto' and not
                                 sys.stdout.isatty()):
        import gtest.util
        gtest.util.color = gtest.util.nocolor

    args.test.run(args)
