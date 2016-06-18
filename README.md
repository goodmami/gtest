gTest
=====

DELPH-IN Grammar Testing Tool

The gTest tool is meant to help automate testing of DELPH-IN style HPSG grammars. Currently it only does the following:

- regression tests against gold [incr tsdb()] profiles
- coverage tests against [incr tsdb()] skeletons
- semantic tests against [incr tsdb()] skeletons

Other tests can be added by following the instructions in the
[NOTES.md](NOTES.md) file.

## Setup

gTest relies heavily on several pieces of software:
  * [ACE](http://sweaglesw.org/linguistics/ace/)
  * [art](http://sweaglesw.org/linguistics/libtsdb/art)
  * [pyDelphin][]

In order to setup gTest for use, download ACE and art and make sure they are on `PATH`. E.g. if ACE and art are installed to `/opt/ace/` and `/opt/art/`, respectively, you can add something like this to your `.bashrc` file:

```bash
PATH=/opt/ace:/opt/art:"$PATH"
```

Also install [pyDelphin][] (via PIP or download and put it on `PYTHONPATH`; more details are available on pyDelphin's website).

## Usage

gTest uses subcommands (like Subversion has `svn checkout` or `svn commit`). You can invoke them like this from the `gtest/` directory, followed by a list of tests:

##### Regression testing

```bash
$ ./gTest -G ~/grammar/ R [tests..]
```

A test can be specified with an initial colon (as in `:testsuite1`), in which case it searches the skeletons directory of the grammar (`tsdb/skeletons/` by default):

```bash
$ ./gTest -G ~/grammar/ R :testsuite1
```

A test can also be specified with a path relative to the grammar, or with an absolute path:

```bash
$ ./gTest -G ~/grammar/ R tsdb/skeletons/testsuite2 ~/grammar/tsdb/skeletons/testsuite3
```

Globbing stars can perform all matching tests:

```bash
$ ./gTest -G ~/grammar/ R :testsuite*
```

In all cases, the test specified is used to find the skeleton path, and the gold profile is then found by looking for relative portion of the path under the gold directory (e.g. `tsdb/gold/testsuite1`, etc.).

There are global options (try `./gTest -h`) and test-specific options (try `./gTest [R|C|M] -h`), mostly for adjusting the locations of relative paths.

##### Coverage testing

```bash
$ ./gTest -G ~/grammar/ C [tests..]
```

##### Semantic testing

```bash
$ ./gTest -G ~/grammar/ M [tests..]
```

[pyDelphin]: https://github.com/goodmami/pydelphin
