
import os
from os.path import (exists, basename, normpath, join as pjoin, sep)
from collections import namedtuple
from subprocess import CalledProcessError
from glob import glob

from gtest.util import (
    directory_sort_key,
    debug, info, warning, error,
    dir_is_profile, make_keypath, resolve_profile_key,
    mkprof, run_art
)

from delphin import itsdb


ItsdbTest = namedtuple('ItsdbTest', ('name', 'path', 'destination', 'log'))


# Methods related to tests that read [incr tsdb()] skeletons

def find_profiles(basedir, profile_match):
    """
    Return profiles under *basedir* matching *profile_match*.
    """
    profs = []
    for (dirpath, dirnames, filenames) in os.walk(basedir):
        if profile_match(dirpath):
            profs.append(dirpath)
        # # sorting dirnames affects traversal order
        # dirnames.sort(key=directory_sort_key)
    return sorted(profs, key=directory_sort_key)


def prepare_profile_keypaths(args, basedir, profile_match):
    """
    Expand the paths of all test items.
    """

    profs = []

    if not args['<test-pattern>']:
        profs = [
            make_keypath(p, basedir)
            for p in find_profiles(basedir, profile_match)
        ]

    else:
        for k in args['<test-pattern>']:
            p = resolve_profile_key(k, basedir)
            paths = sorted(glob(p), key=directory_sort_key)
            _profs = []
            for path in glob(p):
                if exists(path):
                    if profile_match(path):
                        _profs.append(make_keypath(path, basedir))
                    else:
                        debug('Profile found by "{}" not valid for the '
                              'current task: {}'.format(k, path))
                else:
                    warning('Found path doesn\'t exist (it may be a broken '
                            'symlink): {}'.format(path))
            if _profs:
                profs.extend(_profs)
            else:
                warning('No profiles found for "{}"; skipping.'.format(k))

    args['<test-pattern>'] = profs


def test_iterator(args):
    """
    Iterate over test profiles, parsing them if necessary.
    """
    for test in args['<test-pattern>']:
        logf = pjoin(
            args['--working-dir'],
            'run-{}.log'.format(
                '_'.join(normpath(test.key.replace(':', '', 1)).split(sep))
            )
        )

        if args['--static']:
            debug('Using stored profile: {}'.format(test.path))
            dest = test.path
        else:
            debug('Parsing skeleton: {}'.format(test.path))
            dest = pjoin(args['--working-dir'], basename(test.path))
            with open(logf, 'w') as logfile:
                try:
                    mkprof(test.path, dest, log=logfile)
                    run_art(
                        args['--compiled-grammar'].path,
                        dest,
                        options=args['--art-opts'],
                        ace_preprocessor=args['--preprocessor'],
                        ace_options=args['--ace-opts'],
                        log=logfile
                    )
                except CalledProcessError:
                    print('  There was an error processing the testsuite.')
                    print('  See {}'.format(logf))

        yield ItsdbTest(test.key, test.path, dest, logf)


def print_profile_header(name, skel):
    prof = itsdb.ItsdbProfile(skel, index=False)
    wf0_items = 0
    wf1_items = 0
    wf2_items = 0
    for i, row in enumerate(prof.read_table('item')):
        try:
            wf = int(row['i-wf'])
        except ValueError:
            wf = -1
        if wf == 0:
            wf0_items += 1
        elif wf == 1:
            wf1_items += 1
        elif wf == 2:
            wf2_items += 1
        else:
            warning(
                'Invalid i-wf value ({}) in line {} of {}'
                .format(row['i-wf'], i + 1, skel)
            )
    print('{} ({} items; {} ignored):'.format(
        name, wf0_items + wf1_items + wf2_items, wf2_items
    ))
