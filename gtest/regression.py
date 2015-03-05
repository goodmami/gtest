import os
from functools import partial
from glob import glob
from fnmatch import fnmatch
from os.path import (
    abspath, relpath, basename, join as pjoin, exists
)


from gtest.util import (
    prepare,
    debug, info, warning, error,
    pushd, temp_dir, check_exist, make_keypath
)
from gtest.skeletons import list_profiles

from delphin import itsdb
from delphin.mrs import simplemrs
from delphin.mrs.compare import compare_bags


def run(args):
    args.skel_dir = make_keypath(args.skel_dir, args.grammar_dir)
    args.gold_dir = make_keypath(args.gold_dir, args.grammar_dir)

    if args.list_profiles:
        profile_match = partial(
            skel_has_gold,
            skel_dir=abspath(args.skel_dir.path),
            gold_dir=abspath(args.gold_dir.path)
        )
        list_profiles(args.skel_dir.path, profile_match, skeleton=True)
    else:
        prepare(args)  # note: args may change
        regression_test(args)

def regression(args):
    with pushd(args.grammar_dir):
        grm = get_grammar(args, tmp)
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


def skel_has_gold(skel_path, skel_dir, gold_dir):
    """
    Return True if the skel_path has a corollary in the gold directory.
    """
    gold_path = pjoin(gold_dir, relpath(abspath(skel_path), skel_dir))
    return exists(gold_path)

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
                print('{}\t{}:{}'.format(name, relskel, relgold))
