Current version: 0.3.0

Compatible with Python >=2.7

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
- Commit those changes to GIT, taking care not to commit anything else.
- Create a GIT tag for this new version.

Now you're free to push, merge to master and deploy!

For the above version string replacements we'll need some config. [This example](https://github.com/nandilugio/bumpytrack/blob/master/bumpytrack.example.yml) should be autoexplicative. Save it as `.bumpytrack.yml` in the root of your repository and you're good to go.

## Installation

```bash
pip install bumpytrack
```

Then add a `.bumpytrack.yml` to the root of your repository and configure it [like this](https://github.com/nandilugio/bumpytrack/blob/master/bumpytrack.example.yml).

## Help

The script is really simple, and has a decent on-line documentation. Just do:

```bash
bumpytrack --help
```

Some of the available options:

```
  --current-version CURRENT_VERSION
                        Force current version instead using version in config
                        file.
  --new-version NEW_VERSION
                        Force new version instead using version in config
                        file.
  --git-commit          GIT: Commit files with version replacements.
  --no-git-commit
  --git-tag             GIT: Tag this reference with the new version.
  --no-git-tag
  --config-path CONFIG_PATH
                        Path to config file. Defaults to .bumpytrack.yml in
                        current directory.
  --verbose
```

You can also just [peek at the code](https://github.com/nandilugio/bumpytrack/blob/master/bumpytrack/bumpytrack.py). Not much of it... it just adds one to some little numbers ;p

## Development

Make sure you have the lastest `pip` and `pipenv` versions:

```bash
pip install --update pip pipenv
```

To start developing, start the environment by:

```bash
pipenv shell
pipenv install -d
```

This tool uses both [`pipenv`](https://pipenv.readthedocs.io/) for development and [`setuptools`](https://setuptools.readthedocs.io/) for packaging and distribution. To this date there is not a 100% community-accepted best practice so I've taken [this approach](https://github.com/pypa/pipenv/issues/209#issuecomment-337409290). In summary:

To add an _application_ dependency, add it in `setup.py` and leave it with a loose version definition. Then, just do `pipenv install -e .` to install the dependency. Pipenv locking mecanism will work as expected, since bumpytrack itself in in the `[packages]` section of `Pipfile` (check `Pipfile.lock` and you'll find the deps there).

To add a _development_ dependency, add it to `Pipfile` via `pipenv install -d <my-dependency>`.

This way there's a single source of truth for package definition. No need to repeat the deps in `setup.py` and `Pipfile*`.

## License

This project is licensed under the MIT License - see the [`LICENSE`](https://github.com/nandilugio/bumpytrack/blob/master/LICENSE) file for details.

