

def covr_test(args):
    args.skel_dir = make_keypath(args.skel_dir, args.grammar_dir)

    skeldir = pjoin(args.grammar_dir, args.skel_dir)
    proflocs = get_profile_locations(
        args.patterns, skeldir, skeleton=True
    )
    profile_match = partial(profile_location_match, locations=proflocs)
    skeletons = filter(
        profile_filter,
        find_skeletons(pjoin(args.grammar_dir, args.skel_dir))
    )
    if args.list_profiles:
        print('\n'.join(skeletons))
        return
    tmp = temp_dir()
    with pushd(args.grammar_dir):
        grm = get_grammar(args, tmp)
        logging.debug('Using grammar image at {}'.format(abspath(grm)))

        # FIXME: this should not filter based on gold profiles
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