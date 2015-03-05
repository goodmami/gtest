
import os
from gtest.util import dir_is_profile

# Methods related to tests that read [incr tsdb()] skeletons

def list_profiles(basedir, profile_match, skeleton=True):
    profs = []
    for (dirpath, dirnames, filenames) in os.walk(basedir):
        if not dir_is_profile(dirpath, skeleton=skeleton):
            continue
       	if profile_match(dirpath):
            profs.append(dirpath)
        dirnames.sort()  # this affects traversal order
    print('\n'.join(profs))

def find_skeletons(skel_dir):
    abs_skel_dir = abspath(skel_dir)
    skels = []
    for (dirpath, dirnames, filenames) in os.walk(args.skel_dir):
        if dir_is_profile(dirpath, skeleton=True):
            skels.append(dirpath)
        dirnames.sort()  # this affects traversal order
    return skels

def get_skel_and_gold_paths(prof, skel_dir, gold_dir):
    skel_dir = abspath(skel_dir)
    skel_pattern = abspath(normalize_profile_pattern(prof, skel_dir))
    for skel_path in glob(skel_pattern):
        gold_path = abspath(pjoin(gold_dir, relpath(skel_path, skel_dir)))
        yield (skel_path, gold_path)

def profile_key(path, rel_dir):
    return ':{}'.format(relpath(path, rel_dir))

def profile_path(key, rel_dir):
    assert key.startswith(':')
    return pjoin(rel_dir, key[1:])

def find_testable_profiles(profs, skel_dir, gold_dir):
    abs_skel_dir = abspath(skel_dir)
    for prof in profs:
        for skel, gold in get_skel_and_gold_paths(prof, skel_dir, gold_dir):
            if not dir_is_profile(skel, skeleton=True):
                logging.info('Directory is not a skeleton (skipping test): {}'
                             .format(skel))
                continue
            if not dir_is_profile(gold):
                logging.info('Could not find gold profile for skeleton '
                             '(skipping test): {}'.format(skel))
                continue
            name = profile_key(skel, abs_skel_dir)
            yield (name, skel, gold)

