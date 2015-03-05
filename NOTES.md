
# Adding a new test module

gTest can be extended with additional test modules, though you'll have to edit
the source in a few places (in addition to the new module) to get it working.
Here's a short guide to adding a new module for an imaginary `xylophone` test:

1. Create your new module and place it under the `gtest/` directory.
    * Provide a `run(args)` function. The `run()` function is called by
      `gTest` with the `args` parameter containing the command line
      arguments. This is the only entry point from the command line.
    * Resolve any relative paths with `util.make_keypath()`.
    * Prepare any things necessary for your testing environment. You may call
      the preparation methods given in `util`, such as `prepare()` or
      `prepare_working_directory()`, or define these steps yourself.
    * Feel free to import other things from `util.py` or other modules
      (e.g. `skeletons.py` for tests that parse from skeletons).
    * Define (or call) the test from the `run()` function. Nothing is
      returned, so the test should print or log the results.

1. Import your new module in gTest.py

    ```python
    from gtest import (regression, coverage, xylophone)
    ```

1. Add a new argument subparser, ideally with help messages. In addition,
    * Provide a description, and an epilog with example invocations
    * Select a parent parser (e.g. skel_parser) if you need the same features
    * Please explain what RELPATH is if you allow :xyz relative paths
    * Add `test={module}` to the argument parser so your module will be
      called (from `{module}.run(args)`).

    Here's an example:

    ```python
    xylo = subparsers.add_parser(
        'X',
        help='xylophone test',
        description='Check if the grammar can use a Xylophone.'
        epilog='examples:\n'
            '  gTest X\n'
            '  gTest X -x :extra/xylo'
    )
    xylo.add_argument(
        '-x', '--xylophone',
        default=':xylo', metavar='[PATH|:RELPATH]',
        help='directory containing a xylophone definition (RELPATH: '
            '{grammar-dir}; default: :xylo).'
    )
    xylo.set_defaults(test=xylophone)
    ```

# Command-line argument naming conventions

When adding a new module, you'll need to make it available with a
commandline-argument parser. Try to stick to these naming conventions:

* Only global options and commands use capital letters
* Choose available options names/letters, don't repeat or remove existing ones
* ... but subparser arguments can be reused if it's unique for the command
* Please provide a long-form in addition to a short one (e.g. -s/--skel-dir)