
import re
from functools import partial
from os.path import (join as pjoin, basename, normpath, sep)
from subprocess import CalledProcessError

from gtest.util import (
    prepare_working_directory, prepare_compiled_grammar,
    debug, info, warning, error, red, green, yellow,
    check_exist, make_keypath, dir_is_profile,
    mkprof, run_art
)

from gtest.skeletons import (
    find_profiles, prepare_profile_keypaths,
    print_profile_header
)

from delphin import itsdb

# thresholds
PARSE_GOOD = 0.8
PARSE_OK = 0.5
GENERATE_GOOD = 0.8
GENERATE_OK = 0.5

def run(args):
    args.skel_dir = make_keypath(args.skel_dir, args.grammar_dir)

    profile_match = partial(dir_is_profile, skeleton=True)
    prepare_profile_keypaths(args, args.skel_dir.path, profile_match)

    if args.list_profiles:
        print('\n'.join(map(lambda p: '{}\t{}'.format(p.key, p.path),
                            args.profiles)))
    else:
        prepare(args)  # note: args may change
        coverage_test(args)


def prepare(args):
    prepare_working_directory(args)
    with open(pjoin(args.working_dir, 'ace.log'), 'w') as ace_log:
        prepare_compiled_grammar(args, ace_log=ace_log)


def coverage_test(args):
    for skel in args.profiles:
        name = skel.key
        logf = pjoin(
            args.working_dir,
            'run-{}.log'.format(
                '_'.join(normpath(re.sub(r'^:', '', name)).split(sep))
            )
        )
        
        print_profile_header(name, skel.path)

        with open(logf, 'w') as logfile:
            try:
                cov = test_coverage(skel, args, logfile)
                print_coverage_summary(name, cov)
            except CalledProcessError:
                print('  There was an error processing the testsuite.')
                print('  See {}'.format(logf))
            

def test_coverage(skel, args, logfile):
    info('Coverage testing profile: {}'.format(skel.key))

    cov = {}
    dest = pjoin(args.working_dir, basename(skel.path))

    if not (check_exist(skel.path)):
        print('  Skeleton was not found: {}'.format(skel.path))
        return

    mkprof(skel.path, dest, log=logfile)
    run_art(
        args.compiled_grammar.path,
        dest,
        log=logfile)
    cov = parsing_coverage(dest)

    if args.generate:
        g_dest = pjoin(args.working_dir, basename(skel.path) + '.g')
        mkprof(skel.path, g_dest, log=logfile)
        run_art(
            args.compiled_grammar.path,
            g_dest,
            options=['-e', dest],
            ace_options=['-e'],
            log=logfile
        )
        cov = generation_coverage(g_dest, cov)
    return cov

def parsing_coverage(prof_path):
    # todo: consider i-wf
    cov =dict([
        ('items', 0), # items with i-wf = 1
        ('*items', 0), # items with i-wf = 0
        ('?items', 0), # items with i-wf = 2
        ('has_parse', 0),
        ('*has_parse', 0),
        ('readings', 0),
        ('*readings', 0)
    ])
    prof = itsdb.ItsdbProfile(prof_path, index=False)
    for row in prof.join('item', 'parse'):
        wf = int(row['item:i-wf'])
        readings = int(row['parse:readings'])
        if wf == 0:
            cov['*items'] += 1
            if readings > 0:
                cov['*has_parse'] += 1
            cov['*readings'] += readings
        elif wf == 1:
            cov['items'] += 1
            if readings > 0:
                cov['has_parse'] += 1
            cov['readings'] += readings
        else:
            cov['?items'] += 1
    return cov


def generation_coverage(prof_path, pc):
    cov = dict(pc)
    return cov


template2 = '  {:12s}: {:5d}/{:<5d} ({: <6.4f})     : {:5d}/{:<5d} ({: <6.4f})'
template2s = '  {:12s}: {:5d}/{:<5d} {} : {:5d}/{:<5d} {}'

def print_coverage_summary(name, cov):
    # todo: fix i-wf calculations for parsing
    item_total = cov['items'] + cov['*items'] + cov['?items']
    
    if item_total == 0:
        print('  No items.')
        return
    
    print('              :       grammatical        :       ungrammatical')
    print(template2.format(
        'items',
        cov['items'], item_total, float(cov['items']) / item_total,
        cov['*items'], item_total, float(cov['*items']) / item_total
    ))

    s1 = s2 = '(------)    '
    if cov['items']:
        v1 = float(cov['has_parse']) / cov['items']
        s1 = pad(
            '({s}){pad}',
            '{: <6.4f}'.format(v1),
            10,
            color=choose_color(v1, PARSE_OK, PARSE_GOOD),
        )
    if cov['*items']:
        v2 = float(cov['*has_parse']) / cov['*items']
        s2 = pad(
            '({s}){pad}',
            '{: <6.4f}'.format(v2),
            10,
            color=choose_color(v2, PARSE_OK, PARSE_GOOD, invert=True),
        )
    print(template2s.format(
        'parses',
        cov['has_parse'], cov['items'], s1,
        cov['*has_parse'], cov['*items'], s2
    ))

    s1 = s2 = '(------)    '
    if cov['has_parse']:
        v1 = float(cov['readings']) / cov['has_parse']
        s1 = pad(
            '({s}){pad}',
            '{: <.4f}'.format(v1),
            10
        )
    if cov['*has_parse']:
        v2 = float(cov['*readings']) / cov['*has_parse']
        s2 = pad(
            '({s}){pad}',
            '{: <.4f}'.format(v2),
            10
        )
    print(template2s.format(
        'readings',
        cov['readings'], cov['has_parse'], s1,
        cov['*readings'], cov['*has_parse'], s2
    ))
    #print('  realizations:')
    print()


def pad(fmt, s, length, color=None):
    pad = length - len(s)
    if color is not None:
        s = color(s)
    return fmt.format(s=s, pad=' '*pad)


def choose_color(x, ok_thresh, good_thresh, invert=False):
    if invert:
        x = 1 - x
    if x >= ok_thresh:
        if x >= good_thresh:
            return green
        else:
            return yellow
    else:
        return red
