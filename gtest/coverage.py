
from collections import OrderedDict
from functools import partial
from os.path import join as pjoin, basename

from gtest.util import (
    prepare_working_directory, prepare_compiled_grammar,
    debug, info, warning, error, red, green, yellow,
    check_exist, make_keypath, dir_is_profile,
    mkprof, run_art
)

from gtest.skeletons import (find_profiles, prepare_profile_keypaths)

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
        if name.startswith(':'):
            name = name[1:]

        info('Coverage testing profile: {}'.format(skel.key))

        dest = pjoin(args.working_dir, basename(skel.path))
        logf = pjoin(args.working_dir, 'run-{}.log'.format(name))

        if not (check_exist(skel.path)):
            print(skip_msg)
            continue

        with open(logf, 'w') as logfile:
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
            print_coverage_summary(name, cov)


def parsing_coverage(prof_path):
    # todo: consider i-wf
    cov = OrderedDict([
        ('items', 0), # items with i-wf = 1
        ('*items', 0), # items with i-wf = 0
        ('?items', 0), # items with i-wf = 2
        ('has_parse', 0),
        ('*has_parse', 0),
        ('readings', 0),
        ('*readings', 0)
    ])
    prof = itsdb.ItsdbProfile(prof_path)
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


template2 = '  {:12s}: {:4d}/{:<4d} ({:6.4f}) : {:4d}/{:<4d} ({:6.4f})'
template2s = '  {:12s}: {:4d}/{:<4d} ({:6s}) : {:4d}/{:<4d} ({:6s})'
template3 = '  {:12s}: {:4d}/{:<4d} ({:6.4f}) : {:4d}/{:<4d} ({:6.4f}) : {:4d}/{:<4d} ({:6.4f}))'

def print_coverage_summary(name, cov):
    # todo: fix i-wf calculations for parsing
    item_total = cov['items'] + cov['*items'] + cov['?items']
    print('{} ({} items):'.format(name, item_total))
    if item_total == 0:
        print('  No items.')
        return
    print('              : grammatical        : ungrammatical      : ignored ')
    print(template3.format(
        'items',
        cov['items'], item_total, float(cov['items']) / item_total,
        cov['*items'], item_total, float(cov['*items']) / item_total,
        cov['?items'], item_total, float(cov['?items']) / item_total
    ))
    val1 = val2 = 0
    if cov['items']:
        val1 = float(cov['has_parse']) / cov['items']
    if cov['*items']:
        val2 = float(cov['*has_parse']) / cov['*items']
    #if cov['*items']:

    print(template2s.format(
        'parses',
        cov['has_parse'], cov['items'],
        color('{:6.4f}', val1, PARSE_OK, PARSE_GOOD),
        cov['*has_parse'], cov['*items'],
        color('{:6.4f}', val2, PARSE_OK, PARSE_GOOD, invert=True)
    ))
    val1 = val2 = 0
    if cov['has_parse']:
        val1 = float(cov['readings']) / cov['has_parse']
    if cov['*has_parse']:
        val2 = float(cov['*readings']) / cov['*has_parse']
    print(template2.format(
        'readings',
        cov['readings'], cov['has_parse'], val1,
        cov['*readings'], cov['*has_parse'], val2
    ))
    #print('  realizations:')
    print()


def color(fmt, x, ok_thresh, good_thresh, invert=False):
    s = fmt.format(x)
    if invert:
        x = 1 - x
    if x >= ok_thresh:
        if x >= good_thresh:
            return green(s)
        else:
            return yellow(s)
    else:
        return red(s)
