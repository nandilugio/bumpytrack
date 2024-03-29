![CI](https://github.com/nandilugio/bumpytrack/actions/workflows/ci.yml/badge.svg)

**Current version:** 1.1.7

Tested with Python 3.8, 3,9, 3.10 and 3.11 on latest Linux, MacOS and Windows. Code is simple. Probably works in other versions and platforms.

**Pypi:** https://pypi.org/project/bumpytrack/ </br>
**Github:** https://github.com/nandilugio/bumpytrack

# BumpyTrack

Bumping the ([semantic](https://semver.org/)) version of your software every time a release is done can be a tedious task, if you:
- Have the version written in various files, e.g. `setup.py` or a dedicated version file.
- Manage versioning with tags in GIT.

This little script automates this process for you.

Say you're using [`git-flow`](https://nvie.com/posts/a-successful-git-branching-model/) and you've just merged a feature to your development branch. You can just checkout and pull it, and then do:

```bash
bumpytrack minor  # or major if you have breaking changes, or patch if it's a simple bugfix
```

It will:
- Replace the version string in all relevant files (see config below).
- Commit those changes to GIT, taking care not to commit anything else (can be omitted).
- Create a GIT tag for this new version (can be omitted).

Now you're free to push, merge to master and deploy!

```bash
git push
git push --tags
```

Unless you forgot something or bumped by mistake of course, in which case you can just undo the commit and tag created in Git by doing:

```bash
bumpytrack git-undo
```

For the above version string replacements we'll need some config. [This example](https://github.com/nandilugio/bumpytrack/blob/master/pyproject.toml) should be autoexplicative. Create a `pyproject.toml` or add your config to the one you already have in the root of your repository and you're good to go.

## Installation

```bash
pip install bumpytrack
```

Then add a `pyproject.toml` to the root of your repository (if you don't already have it) and configure it [like this](https://github.com/nandilugio/bumpytrack/blob/master/pyproject.toml).

## Help

The script is really simple, and has a decent on-line documentation. Just do:

```bash
bumpytrack --help
```

Some of the available options:

```
  --current-version CURRENT_VERSION
                        force current version instead using version in config
                        file
  --new-version NEW_VERSION
                        force new version instead using version in config file
  --git-commit          Git: Commit files with version replacements
  --no-git-commit
  --git-tag             Git: Tag this reference with the new version
  --no-git-tag
  --config-path CONFIG_PATH
                        path to config file. Defaults to pyproject.toml in
                        current directory
  --verbose
```

You can also just [peek at the code](https://github.com/nandilugio/bumpytrack/blob/master/src/bumpytrack.py). Not much of it... it just adds one to some little numbers ;p

## Contributing

Make sure you have the lastest `pip` and `pipenv` versions:

```bash
pip install --upgrade pip pipenv
```

To start developing, start the environment by:

```bash
pipenv shell
pipenv install -d
```

The installed `bumpytrack` within the pipenv environment is the editable (alla `pip install -e .`) version of the package, so you can manually test right away.

This tool uses both [`pipenv`](https://pipenv.readthedocs.io/) for development and [`setuptools`](https://setuptools.readthedocs.io/) for packaging and distribution. To this date there is not a 100% community-accepted best practice so I've taken [this approach](https://github.com/pypa/pipenv/issues/209#issuecomment-337409290). In summary:

To add an _application_ dependency, add it in `setup.py` and leave it with a loose version definition. Then, just do `pipenv install -e .` to install the dependency. Pipenv locking mecanism will work as expected, since bumpytrack itself in in the `[packages]` section of `Pipfile` (check `Pipfile.lock` and you'll find the deps there).

To add a _development_ dependency, add it to `Pipfile` via `pipenv install -d <my-dependency>`.

This way there's a single source of truth for package definition. No need to repeat the deps in `setup.py` and `Pipfile*`.

### Tests

To test the project run [`pytest`](https://docs.pytest.org/) inside the `pipenv`. Once you have something running, run [`tox`](https://github.com/tox-dev/tox) to check it's compatible with all python versions supported.

IMPORTANT: in order to make `tox` test with different python versions, those have to be installed. [`pyenv`](https://github.com/pyenv/pyenv) is used for that purpose and should work out of the box. Check the required versions in [`tox.ini`](https://github.com/nandilugio/bumpytrack/blob/master/tox.ini) and related files.

### Dev tasks automation and publishing to PyPI

This project uses [`pepython`](https://github.com/nandilugio/pepython) for automation. There you'll find tasks to build and publish the package to PyPI.

Check [the project](https://github.com/nandilugio/pepython) out and the [`tasks.py`](https://github.com/nandilugio/bumpytrack/blob/master/tasks.py) file for more info.

## License

This project is licensed under the MIT License - see the [`LICENSE`](https://github.com/nandilugio/bumpytrack/blob/master/LICENSE) file for details.

