
"""
Regression test by comparing parse results to stored gold profiles

Usage: gtest (R|regression) [--skeletons=DIR] [--gold=DIR]
                            (--list-profiles | <test-pattern> ...)

Arguments (RELPATH: {skeletons}):
  <test-pattern>        path or glob-pattern to a test skeleton

Options (RELPATH: {grammar-dir}):
  --skeletons=DIR       skeleton dir [default: :tsdb/skeletons/]
  --gold=DIR            gold profile dir [default: :tsdb/gold/]
  -l, --list-profiles   don't test, just list testable profiles

Examples:
    gtest -G ~/mygram R --list-profiles
    gtest -G ~/jacy R :mrs
    gtest -G ~/jacy R --skeletons=:tsdb/skeletons/tanaka/ :\\*
"""

import os
from functools import partial
from os.path import (
    abspath, relpath, basename, join as pjoin, exists
)

from gtest.util import (
    prepare_working_directory, prepare_compiled_grammar,
    debug, info, warning, error, red, green, yellow,
    check_exist, make_keypath,
    mkprof, run_art
)
from gtest.skeletons import (find_profiles, prepare_profile_keypaths)

from delphin import itsdb
from delphin.mrs import simplemrs
from delphin.mrs.compare import compare_bags


def run(args):
    args['--skeletons'] = make_keypath(args['--skeletons'], args['--grammar-dir'])
    args['--gold'] = make_keypath(args['--gold'], args['--grammar-dir'])

    profile_match = partial(
        skel_has_gold,
        skel_dir=abspath(args['--skeletons'].path),
        gold_dir=abspath(args['--gold'].path)
    )
    prepare_profile_keypaths(args, args['--skeletons'].path, profile_match)

    if args['--list-profiles']:
        print('\n'.join(map(lambda p: '{}\t{}'.format(p.key, p.path),
                            args['<test-pattern>'])))
    else:
        prepare(args)  # note: args may change
        regression_test(args)


def prepare(args):
    prepare_working_directory(args)
    with open(pjoin(args['--working-dir'], 'ace.log'), 'w') as ace_log:
        prepare_compiled_grammar(args, ace_log=ace_log)


def regression_test(args):
    for skel in args['<test-pattern>']:
        name = skel.key
        if name.startswith(':'):
            name = name[1:]

        info('Regression testing profile: {}'.format(skel.key))

        dest = pjoin(args['--working-dir'], basename(skel.path))
        logf = pjoin(args['--working-dir'], 'run-{}.log'.format(name))

        gold = gold_path(skel.path, args['--skeletons'].path, args['--gold'].path)

        pass_msg = '{}\t{}'.format(green('pass'), skel.key)
        fail_msg = '{}\t{}; See {}'.format(red('fail'), skel.key, logf)
        skip_msg = '{}\t{}; See {}'.format(yellow('skip'), skel.key, logf)

        if not (check_exist(skel.path) and check_exist(gold)):
            print(skip_msg)
            continue
        
        with open(logf, 'w') as logfile:
            mkprof(skel.path, dest, log=logfile)
            run_art(
                args['--compiled-grammar'].path,
                dest,
                options=args['--art-opts'],
                ace_preprocessor=args['--preprocessor'],
                ace_options=args['--ace-opts'],
                log=logfile
            )
            success = compare_mrs(dest, gold, log=logfile)
            print(pass_msg if success else fail_msg)


def gold_path(skel_path, skel_dir, gold_dir):
    """
    Calculate the gold profile path based on the skeleton path.
    """
    return pjoin(gold_dir, relpath(abspath(skel_path), skel_dir))

def skel_has_gold(skel_path, skel_dir, gold_dir):
    """
    Return True if the skeleton has a corollary in the gold directory.
    """
    return exists(gold_path(skel_path, skel_dir, gold_dir))

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
