
"""
Regression test by comparing parse results to stored gold profiles

Usage: gtest regression [--profiles=DIR] [--gold=DIR] [--static]
                        [--list-profiles]
                        [<test-pattern> ...]

Arguments (RELPATH: --profiles):
  <test-pattern>        path or glob-pattern to a test skeleton or profile;
                        only patterns matching both a skeleton/profile AND a
                        gold profile will be allowed

Options (RELPATH: --grammar-dir):
  --profiles=DIR        profile or skeleton dir [default: :tsdb/skeletons/]
  --gold=DIR            gold profile dir [default: :tsdb/gold/]
  -s, --static          don't parse; do static analysis of parsed profiles
  -l, --list-profiles   don't test, just list testable profiles

Examples:
    gtest -G ~/mygram regression --list-profiles
    gtest -G ~/jacy regression :mrs
    gtest -G ~/jacy regression --profiles=:tsdb/skeletons/tanaka/ :\\*
    gtest regression --static --profiles=:tsdb/current
"""

from functools import partial
from os.path import (
    abspath, relpath, join as pjoin, exists
)

from gtest.util import (
    prepare_working_directory, prepare_compiled_grammar,
    debug, info, warning, error, red, green, yellow,
    make_keypath, dir_is_profile
)
from gtest.skeletons import (
    prepare_profile_keypaths,
    test_iterator
)

from delphin import itsdb
from delphin.mrs import simplemrs
from delphin.mrs.compare import compare_bags


def run(args):
    args['--profiles'] = make_keypath(args['--profiles'],args['--grammar-dir'])
    args['--gold'] = make_keypath(args['--gold'], args['--grammar-dir'])

    profile_match = partial(
        test_has_gold,
        test_dir=abspath(args['--profiles'].path),
        gold_dir=abspath(args['--gold'].path),
        skeleton=(not args['--static'])
    )
    prepare_profile_keypaths(args, args['--profiles'].path, profile_match)

    if args['--list-profiles']:
        print('\n'.join(map(lambda p: '{}\t{}'.format(p.key, p.path),
                            args['<test-pattern>'])))
    else:
        prepare(args)  # note: args may change
        regression_test(args)


def prepare(args):
    prepare_working_directory(args)
    if not args['--static']:
        with open(pjoin(args['--working-dir'], 'ace.log'), 'w') as ace_log:
            prepare_compiled_grammar(args, ace_log=ace_log)


def regression_test(args):
    for test in test_iterator(args):
        info('Regression testing profile: {}'.format(test.name))

        pass_msg = '{}\t{}'.format(green('pass'), test.name)
        fail_msg = '{}\t{}; See {}'.format(red('fail'), test.name, test.log)
        skip_msg = '{}\t{}; See {}'.format(yellow('skip'), test.name, test.log)

        gold = gold_path(
            test.path,
            args['--profiles'].path,
            args['--gold'].path
        )

        # if not (check_exist(test.path) and check_exist(gold)):
        #     print(skip_msg)
        #     continue
        with open(test.log, 'a') as logfile:
            success = compare_mrs(test.destination, gold, log=logfile)
            print(pass_msg if success else fail_msg)


def gold_path(test_path, test_dir, gold_dir):
    """
    Calculate the gold profile path based on the testsuite path.
    """
    return pjoin(gold_dir, relpath(abspath(test_path), test_dir))

def test_has_gold(test_path, test_dir, gold_dir, skeleton):
    """
    Return True if the testsuite has a corollary in the gold directory.
    """
    gold = gold_path(test_path, test_dir, gold_dir)
    return (
        exists(gold) and
        dir_is_profile(test_path, skeleton=skeleton) and
        dir_is_profile(gold, skeleton=False)
    )

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
