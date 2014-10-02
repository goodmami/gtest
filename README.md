gtest
=====

DELPH-IN Grammar Testing Tool

The gtest tool is meant to help automate testing of DELPH-IN style HPSG grammars. Currently it only does regression testing against gold [incr tsdb()] profiles, but I may be interested in adding other kinds of tests (add a [feature request](https://github.com/goodmami/gtest/issues)). For example, tests for conformance to conventions (e.g. predicate names), semantic well-formedness, and so on.

## Setup

gtest relies heavily on several pieces of software:
  * [ACE](http://sweaglesw.org/linguistics/ace/)
  * [art](http://sweaglesw.org/linguistics/libtsdb/art)
  * [pyDelphin](https://github.com/goodmami/pydelphin)

In order to setup gtest for use, download ACE and art and make sure they are on `PATH`. E.g. if ACE and art are installed to `/opt/ace-0.9.18pre1/` and `/opt/art-0.1.7/`, respectively, you can add something like this to your `.bashrc` file:

```bash
PATH=/opt/ace-0.9.18pre1:/opt/art-0.1.7:"$PATH"
```

Also download pyDelphin (and install its dependencies, such as the Python3 version of networkx) and put it on `PYTHONPATH`. E.g. if pyDelphin is downloaded to `~/pydelphin`, then add this to your `.bashrc`:

```bash
PYTHONPATH=~/pydelphin:"$PYTHONPATH"
```

## Usage

gtest uses subcommands (like Subversion has `svn checkout` or `svn commit`), but currently there is only one, `R`, for regression testing. You can invoke it like this from the `gtest/` directory:

```bash
$ ./gtest -G path/to/grammar/ R testsuite1 testsuite2
```

gtest uses directories relative to the grammar directory (`-G`), so if your ACE config file is at `ace/config.tdl`, your skeletons are under `tsdb/skeletons/`, and your gold profiles are under `tsdb/gold/`, then this command will work, assuming you have skeletons and gold profiles named `testsuite1` and `testsuite2`. If not, you can adjust the locations with options to the gtest command. There are global options (try `./gtest -h`) and options specific to regression testing (try `./gtest R -h`).
