
import os
from os.path import exists
from glob import glob

from gtest.util import (
    debug, info, warning, error,
    dir_is_profile, make_keypath, resolve_profile_key
)

from delphin import itsdb

# Methods related to tests that read [incr tsdb()] skeletons

def find_profiles(basedir, profile_match, skeleton=True):
    profs = []
    for (dirpath, dirnames, filenames) in os.walk(basedir):
        if not dir_is_profile(dirpath, skeleton=skeleton):
            continue
        if profile_match(dirpath):
            profs.append(dirpath)
        dirnames.sort()  # this affects traversal order
    return profs


def prepare_profile_keypaths(args, basedir, profile_match, skeleton=True):
    profs = []

    if not args.profiles:
        profs = [
            make_keypath(p, basedir)
            for p in find_profiles(basedir, profile_match, skeleton=skeleton)
        ]

    else:
        for k in args.profiles:
            p = resolve_profile_key(k, basedir)
            paths = glob(p)
            _profs = []
            for path in glob(p):
                if exists(path):
                    if not dir_is_profile(path, skeleton=True):
                        debug('Found path is not a skeleton: {}'.format(path))
                    elif profile_match(path):
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

    args.profiles = profs

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
