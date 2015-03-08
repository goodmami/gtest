
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
    cov = OrderedDict([
        ('items', 0),
        ('has_parse', 0),
        ('readings', 0),
    ])
    prof = itsdb.ItsdbProfile(prof_path)
    for row in prof.read_table('parse'):
        cov['items'] += 1
        readings = int(row['readings'])
        if readings > 0:
            cov['has_parse'] += 1
            cov['readings'] += readings
    return cov


def generation_coverage(prof_path, pc):
    cov = dict(pc)
    return cov


def print_coverage_summary(name, coverage):
    print('{}:'.format(name))
    div = 0
    if coverage['items']:
        div = float(coverage['has_parse']) / coverage['items']
    print('  parses  : {}/{} ({})'.format(
        coverage['has_parse'], coverage['items'],
        color('{:0.4g}', div, PARSE_OK, PARSE_GOOD)
    ))
    div = 0
    if coverage['has_parse']:
        div = float(coverage['readings']) / coverage['has_parse']
    print('  readings: {}/{} ({:0.4g} per parsed item)'.format(
        coverage['readings'], coverage['has_parse'], div
    ))


def color(fmt, x, ok_thresh, good_thresh):
    s = fmt.format(x)
    if x >= ok_thresh:
        if x >= good_thresh:
            return green(s)
        else:
            return yellow(s)
    else:
        return red(s)
