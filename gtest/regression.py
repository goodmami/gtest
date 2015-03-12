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
    args.skel_dir = make_keypath(args.skel_dir, args.grammar_dir)
    args.gold_dir = make_keypath(args.gold_dir, args.grammar_dir)

    profile_match = partial(
        skel_has_gold,
        skel_dir=abspath(args.skel_dir.path),
        gold_dir=abspath(args.gold_dir.path)
    )
    prepare_profile_keypaths(args, args.skel_dir.path, profile_match)

    if args.list_profiles:
        print('\n'.join(map(lambda p: '{}\t{}'.format(p.key, p.path),
                            args.profiles)))
    else:
        prepare(args)  # note: args may change
        regression_test(args)


def prepare(args):
    prepare_working_directory(args)
    with open(pjoin(args.working_dir, 'ace.log'), 'w') as ace_log:
        prepare_compiled_grammar(args, ace_log=ace_log)


def regression_test(args):
    for skel in args.profiles:
        name = skel.key
        if name.startswith(':'):
            name = name[1:]

        info('Regression testing profile: {}'.format(skel.key))

        dest = pjoin(args.working_dir, basename(skel.path))
        logf = pjoin(args.working_dir, 'run-{}.log'.format(name))

        gold = gold_path(skel.path, args.skel_dir.path, args.gold_dir.path)

        pass_msg = '{}\t{}'.format(green('pass'), skel.key)
        fail_msg = '{}\t{}; See {}'.format(red('fail'), skel.key, logf)
        skip_msg = '{}\t{}; See {}'.format(yellow('skip'), skel.key, logf)

        if not (check_exist(skel.path) and check_exist(gold)):
            print(skip_msg)
            continue
        
        with open(logf, 'w') as logfile:
            mkprof(skel.path, dest, log=logfile)
            run_art(
                args.compiled_grammar.path,
                dest,
                options=args.art_opts,
                ace_preprocessor=args.preprocessor,
                ace_options=args.ace_opts,
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
