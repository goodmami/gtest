
"""
Validate semantic outputs from a grammar

Usage: gtest (M|semantics) [--profiles=DIR] [--static]
                           [--list-profiles]
                           [<test-pattern> ...]

Arguments (RELPATH: {skeletons}):
  <test-pattern>        path or glob-pattern to a test skeleton or profile

Options (RELPATH: {grammar-dir}):
  --profiles=DIR        profile or skeleton dir [default: :tsdb/skeletons/]
  -s, --static          don't parse; do static analysis of parsed profiles
  -l, --list-profiles   don't test, just list testable profiles

Examples:
    gtest -G ~/mygram M --list-profiles
    gtest -G ~/mygram M :abc
    gtest -G ~/mygram M --profiles=:tsdb/gold --static
"""

from __future__ import print_function

from functools import partial
from os.path import join as pjoin

from delphin import itsdb
from delphin.mrs import simplemrs, path as mp
from delphin._exceptions import XmrsError

from gtest.util import (
    prepare_working_directory, prepare_compiled_grammar,
    debug, info, warning, error, red, green, yellow,
    make_keypath, dir_is_profile,
)

from gtest.skeletons import (
    prepare_profile_keypaths,
    print_profile_header,
    test_iterator
)

def run(args):
    args['--profiles'] = make_keypath(args['--profiles'],args['--grammar-dir'])
    profile_match = partial(dir_is_profile, skeleton=(not args['--static']))
    prepare_profile_keypaths(args, args['--profiles'].path, profile_match)

    if args['--list-profiles']:
        print('\n'.join(map(lambda p: '{}\t{}'.format(p.key, p.path),
                            args['<test-pattern>'])))
    else:
        prepare(args)  # note: args may change
        semantics_test(args)


def prepare(args):
    prepare_working_directory(args)
    if not args['--static']:
        with open(pjoin(args['--working-dir'], 'ace.log'), 'w') as ace_log:
            prepare_compiled_grammar(args, ace_log=ace_log)


def semantics_test(args):
    for test in test_iterator(args):
        info('Semantic testing profile: {}'.format(test.name))

        print_profile_header(test.name, test.destination)
        res = semantic_test_result(test.destination)
        print_result_summary(test.name, res)


def semantic_test_result(prof_path):
    # todo: consider i-wf
    res =dict([
        ('i-ids', set()),
        ('result', 0), #
        ('no-mrs', 0), #
        ('bad-mrs', 0), #
        ('disconnected', 0), # connected MRS
        ('ill-formed', 0), # well-formed MRS
        ('non-headed', 0),
        ('error', 0)
        # ('scope', 0), # MRSs that scope well
        # ('headed', 0) # fully headed MRSs (can be tree-ified)
    ])
    prof = itsdb.ItsdbProfile(prof_path, index=False)

    for row in prof.join('parse', 'result'):
        iid, rid = row['parse:i-id'], row['result:result-id']
        mrs = row['result:mrs']

        res['i-ids'].add(iid)
        res['result'] += 1

        faults = []
        if mrs:
            try:
                m = simplemrs.loads_one(mrs)
                if not m.is_well_formed():
                    faults.append('ill-formed')
                if not m.is_connected():
                    faults.append('disconnected')
                headed_nids = [n for _, n, _ in mp.walk(m) if n != 0]
                if set(headed_nids) != set(m.nodeids()):
                    faults.append('non-headed')
            except XmrsError:
                faults.append('bad-mrs')
            except:
                faults.append('error')
        else:
            faults.append('no-mrs')
        if faults:
            info('{iid}-{rid}\t{faults}'
                 .format(iid=iid, rid=rid, faults=' '.join(faults)))
            if 'error' in faults:
                debug(mrs)
            for fault in faults:
                res[fault] += 1
        else:
            debug('{iid}-{rid}'.format(iid=iid, rid=rid))
    return res

template1 = '  {:12s}: {:5d}/{:<5d} ({: >6.4f}{})'
template2 = '  {:12s}: {:5d}/{:<5d} ({: >6.2%}{})'

def print_result_summary(name, res):
    i = len(res['i-ids'])
    if not i: return

    r = res['result']
    print(template1.format('results', r, i, r/float(i), ' per item'))
    if not r: return

    m = res['no-mrs']
    print(template2.format('No MRS', m, r, m/float(r), ' of results'))
    m = r - m  # number with MRSs instead of number without
    if not m: return

    x = res['bad-mrs']
    print(template2.format('Bad MRS', x, m, x/float(m), ''))
    x = res['ill-formed']
    print(template2.format('Ill-formed', x, m, x/float(m), ''))
    x = res['disconnected']
    print(template2.format('Disconnected', x, m, x/float(m), ''))
    x = res['non-headed']
    print(template2.format('Non-headed', x, m, x/float(m), ''))
