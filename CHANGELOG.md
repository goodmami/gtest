# Change Log

## [Unreleased][unreleased]

This release uses [docopt][] to simplify adding new command parsers,
and at the same time changes how gTest is invoked. If installed, a
`gtest` command is made available (note it's all lowercase). When not
installed, a `gtest.sh` script emulates the command's behavior for Posix
shells. Support is also added for testing static profiles, rather than
parsing them each time.

### Added

* `gtest.main` module
* Entry point in `setup.py` for a `gtest` command
* `gtest.sh` executable for running without installation
* `--static` option tests with existing profiles and doesn't compile a
  grammar or parse profiles

### Removed

* `gTest.py`
* `gTest` shell script (now `gtest.sh`)

### Changed

* Changed argument parsing from argparse to [docopt][]
* Subcommands now have long forms:
  - `R` > `regression`
  - `C` > `coverage`
  - `M` > `semantics`
* `--skeletons` option is now `--profiles` since it could be either
  skeletons or parsed profiles
* Test iteration (for testing or listing) is now sorted (like `sort -V`)

[docopt]: http://docopt.org/

## [v0.1.1][]

### Added

* `setup.py` script

### Changed

* Fixed Python 2.7 compatibility
* Made `__version__` string accessible from `gtest` package directly

## [v0.1.0][]

First versioned release. For previous changes, please consult the
[commit history](../../commits/master).

[unreleased]: ../../tree/develop
[v0.1.1]: ../../releases/tag/v0.1.1
[v0.1.0]: ../../releases/tag/v0.1.0
[README]: README.md

