
from functools import partial

from gtest.util import (
    prepare_working_directory, prepare_compiled_grammar,
    debug, info, warning, error, red, green, yellow,
    check_exist, make_keypath,
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
            pc = parsing_coverage(dest)
            print(format_coverage_summary(pc))

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
                gc = generation_coverage(g_dest, pc)
                print(format_coverage_summary(gc))


def parsing_coverage(prof):
    pass


def generation_coverage(prof, pc):
    pass


def format_coverage_summary(coverage):
    pass
