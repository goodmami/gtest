
# Adding a new test module

gTest can be extended with additional test modules, though you'll have
to edit the source in a few places (in addition to the new module) to
get it working. Here's a short guide to adding a new module for an
imaginary `xylophone` test:

1. Create your new module and place it under the `gtest/` directory.
    * Provide a module docstring with [docopt][] usage (see the other
      modules for examples). For example:

      ```
      Check if a grammar can use a Xylophone

      Usage: gtest (X|xylophone) [--xylophone=PATH]

      Options (RELPATH: {grammar-dir}):
        -x PATH, --xylophone PATH
                        path to a xylophone definition [default: :xylo]

      Examples:
          gtest -G ~/mygram X
          gtest -G ~/mygram X -x :extra/xylo
      ```

    * Provide a `run(args)` function. The `run()` function is called by
      gTest with the `args` parameter containing the command line
      arguments. This is the only entry point from the command line.
    * Resolve any relative paths with `gtest.util.make_keypath()`.
    * Prepare any things necessary for your testing environment. You may
      call the preparation methods given in `gtest.util`, such as
      `prepare_working_directory()`, or define these steps yourself.
    * Feel free to import other things from `gtest.util` or other modules
      (e.g. `gtest.skeletons` for tests that parse from skeletons).
    * Define (or call) the test from the `run()` function. Nothing is
      returned, so the test should print or log the results.

2. Add support for your module in `gtest.main`:
    * Add your command to the [docopt][]-usage in the docstring.
    * Handle it in the `main()` function:

        ```python
            ...
            elif args['<command>'] in ('X', 'xylophone'):
                import gtest.xylophone as test
            ...
        ```

# Command-line argument naming conventions

When adding a new module, you'll need to make it available with a
commandline-argument parser. Try to stick to these naming conventions:

* Only global options and commands use capital letters
* Choose available options names/letters, don't repeat or remove existing ones
* ... but subparser arguments can be reused if it's unique for the command
* Please provide a long-form in addition to a short one (e.g.
  `-l`/`--list-profiles`)

[docopt]: http://docopt.org/
