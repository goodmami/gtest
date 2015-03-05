#!/usr/bin/env python3

#from __future__ import print_function
import sys
import logging

from gtest import (regression, coverage)

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
            '  gTest -G ~/mygram R :mrs  # regression-test the mrs profile\n'
            '  gTest -G ~/mygram C :mrs  # test coverage of the mrs profile\n'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count', dest='verbosity', default=2,
        help='increase the verbosity (can be repeated: -vvv).'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_const', const=0, dest='verbosity',
        help='set verbosity to the quietest level.'
    )
    #parser.add_argument('-R', '--recursive', action='store_true')
    parser.add_argument(
        '-G', '--grammar-dir',
        default='.', metavar='DIR',
        help='root directory of a grammar (default ./).'
    )
    parser.add_argument(
        '-A', '--ace-config',
        default=':ace/config.tdl', metavar='[PATH|:RELPATH]',
        help='location of the ACE config file (RELPATH: {grammar-dir}; '
            'default: :ace/config.tdl).'
    )
    parser.add_argument(
        '-C', '--compiled-grammar',
        metavar='[PATH|:RELPATH]',
        help='location of a pre-compiled grammar image (RELPATH: '
            '{grammar-dir}); if unset, the grammar will be compiled to a '
            'temporary location'
    )
    parser.add_argument(
       '-W', '--working-dir',
       metavar='DIR',
       help='directory to store artifacts of the testing process (parsed '
           'profiles, compiled grammars, etc); if unset, a temp directory '
           'will be created'
    )

    skel_parser = argparse.ArgumentParser(add_help=False)
    skel_parser.add_argument(
        dest='profiles',
        nargs='*',
        default=[':*'],
        help='One or more profiles to test (RELPATH: {skel-dir}). Paths '
            'may include globbing asterisks, although colon-prefixed '
            'relative paths must escape the asterisks to avoid shell '
            'expansion (e.g. :prof\*).'
    )
    skel_parser.add_argument(
        '-l', '--list-profiles',
        nargs='?', metavar='profile', const=True,
        help='List testable profiles that are findable with the current '
             'settings. If `profile` is given, it is a profile name---as '
             'in the `profiles` argument---that must match.'
    )
    skel_parser.add_argument(
        '-s', '--skel-dir',
        default=':tsdb/skeletons', metavar='[DIR|:RELPATH]',
        help='directory with [incr tsdb()] skeletons (RELPATH: '
            '{grammar-dir}; default: :tsdb/skeletons/).'
    )

    ##
    ## New commands go below
    ##

    subparsers = parser.add_subparsers(help='sub-command help')

    # Regression tests

    regr = subparsers.add_parser(
        'R',
        parents=[skel_parser],
        help='regression test',
        description='Run regression tests that compare the semantics of the current '
            'grammar with a gold profile. Gold profiles are found using the '
            'skeleton profile\'s basename: {gold-dir/}basename(profile).',
        epilog='examples:\n'
            '  gTest -G ~/mygram R --list-profiles\n'
            '  gTest -G ~/mygram R :\*\n'
            '  gTest -G ~/mygram -C ~/mygram.dat R ~/mygram/tsdb/skeletons/*\n'
            '  gTest -A ~/bin/ace -G ~/mygram R -s tsdb/skels :xyz :abc\*\n'
    )
    regr.add_argument(
        '-g', '--gold-dir',
        default=':tsdb/gold', metavar='DIR',
        help='directory with [incr tsdb()] gold profiles (RELPATH: '
            '{grammar-dir}; default: :tsdb/gold/).'
    )
    regr.set_defaults(test=regression)

    # Coverage tests

    covr = subparsers.add_parser(
        'C',
        parents=[skel_parser],
        help='coverage',
        epilog='examples:\n'
            '  gTest -G ~/mygram C --list-profiles\n'
            '  gTest -G ~/mygram C :abc'
    )
    covr.set_defaults(test=coverage)

    args = parser.parse_args()
    logging.basicConfig(level=50-(args.verbosity*10))

    args.test.run(args)
