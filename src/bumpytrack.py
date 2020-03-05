# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import os
import sys
import toml

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess


# Logging ######################################################################

class Logger(object):
    def set_verbose(self,verbose=True):
        self._verbose = verbose

    def log(self, message):
        print(message)

    def log_verbose(self, message):
        if not self._verbose:
            return
        self.log(message)

logger = Logger()


# System #######################################################################

def fail(message):
    logger.log(message)
    exit(1)

def run_command(command_tokens, allow_failures=False):
    completed_process = subprocess.run(command_tokens, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    failed = completed_process.returncode != 0
    output = completed_process.stdout.strip().decode('utf-8')  # Contains both stdout and stderr

    if failed and not allow_failures:
        command = " ".join(command_tokens)
        fail("Failed to execute '{command}'. Output was:\n\n{output}\n".format(**locals()))

    if allow_failures:
        ok = not failed
        return ok, output
    else:
        return output


# SemVer #######################################################################

def parse_version(version):
    try:
        str_tokens = version.split(".")

        if len(str_tokens) != 3:
            fail("Failed paring current version. There should be exactly 3 tokens.")

        int_tokens = [int(str_token) for str_token in str_tokens]
    except RuntimeError as error:
        fail("Failed parsing current version: " + str(error))

    return int_tokens

def version_tokens_to_str(int_tokens):
    return ".".join(str(int_token) for int_token in int_tokens)

def increment_version(current_version, part):
    current_version_tokens = parse_version(current_version)

    if part == "major":
        new_version_tokens = [current_version_tokens[0] + 1, 0, 0]
    elif part == "minor":
        new_version_tokens = [current_version_tokens[0], current_version_tokens[1] + 1, 0]
    elif part == "patch":
        new_version_tokens = [current_version_tokens[0], current_version_tokens[1], current_version_tokens[2] + 1]
    else:
        fail("Part should be one of: major, minor or patch.")

    return version_tokens_to_str(new_version_tokens)


# Low-level task helpers #######################################################

def file_replace(file_replace_config, current_version, new_version):
    file_path = file_replace_config["path"]
    logger.log_verbose("Replacing version string in '{file_path}'.".format(**locals()))

    search_template = file_replace_config.get("search_template", "{version}")
    search = search_template.format(version=current_version)
    replace = search_template.format(version=new_version)
    logger.log_verbose("Searching '{search}' and replacing for '{replace}'".format(**locals()))

    if not os.access(file_path, os.R_OK | os.W_OK):
        fail("File '{file_path}' not found or not accessible".format(**locals()))

    original_file_contents = None
    with codecs.open(file_replace_config["path"], "r", encoding="utf-8") as file:
        original_file_contents = file.read()

    new_file_contents = original_file_contents.replace(search, replace)
    if original_file_contents == new_file_contents:
        fail("Nothing to replace in file '{file_path}'. Aborting since this looks like a misconfiguration or an"
             "inconsistent version in config file.".format(**locals()))

    with codecs.open(file_replace_config["path"], "w", encoding="utf-8") as file:
        file.write(new_file_contents)

def git_bump_commit(modified_files, current_version, new_version):
    # TODO: make git path configurable
    commit_message = u"Bumping version: {current_version} → {new_version}".format(**locals())
    run_command(["git", "reset", "HEAD"])
    run_command(["git", "add"] + modified_files)
    run_command(["git", "commit", "-m", commit_message])

def git_undo_bump_commit(bumped_version):
    last_commit_message = run_command(["git", "log", "-1", "--pretty=%B"])
    is_bump = last_commit_message.startswith("Bumping version: ")
    bumps_to_expected_version = last_commit_message.endswith(bumped_version)
    if not (is_bump and bumps_to_expected_version):
        return False
    commit_undone, _out = run_command(["git", "reset", "--hard", "HEAD~1"], allow_failures=True)
    return commit_undone

def git_bump_tag(new_version):
    # TODO: make this format configurable
    tag = "v{new_version}".format(**locals())
    run_command(["git", "tag", tag])

def git_undo_bump_tag(bumped_version):
    tag = "v{bumped_version}".format(**locals())
    tag_deleted, _out = run_command(["git", "tag", "-d", tag], allow_failures=True)
    return tag_deleted


# High-level tasks / use-cases #################################################

def do_bump(args, config, config_path):
    # Get current version
    current_version = args.get("current_version") or config.get("current_version")
    if not current_version:
        fail("No way to obtain current version")
    logger.log("Current version: '{current_version}'".format(**locals()))

    # Get new version
    if args.get("new_version"):
        new_version = args.get("new_version")
    elif args.get("command"):  # We're now bumping, so command is the version "part" to bump
        new_version = increment_version(current_version, args.get("command"))
    else:
        fail("No way to obtain a new version")
    logger.log("New version: '{new_version}'".format(**locals()))

    # Replace version in config file and other configured files
    logger.log("Replacing version srting in files".format(**locals()))
    file_replace_configs = config.get("file_replaces") or []
    file_replace_configs.append({"path": config_path, "search_template": "current_version = \"{version}\""})
    modified_files = []
    for file_replace_config in file_replace_configs:
        file_path = file_replace_config['path']
        file_replace(file_replace_config, current_version, new_version)
        modified_files.append(file_path)

    # Git commit file changes
    if args.get("git_commit") if args.get("git_commit") is not None else config.get("git_commit"):
        logger.log("Committing changes to GIT")
        git_bump_commit(modified_files, current_version, new_version)

    # Git tag new version
    if args.get("git_tag") if args.get("git_tag") is not None else config.get("git_tag"):
        logger.log("Adding version tag to GIT")
        git_bump_tag(new_version)

def do_git_undo(args, config, config_path):
    # Get current version
    current_version = args.get("current_version") or config.get("current_version")
    if not current_version:
        fail("No way to obtain current version")
    logger.log("Undoing bump to version: '{current_version}'".format(**locals()))

    if not git_undo_bump_commit(current_version):
        fail("Couldn't undo bump commit. Aborting!")
    logger.log("Bump commit undone")

    if not git_undo_bump_tag(current_version):
        fail("Couldn't undo bump tag. Aborting!")
    logger.log("Bump tag removed")


# Entrypoints and bootstrapping ################################################

def load_config(config_path):
    config = None
    try:
        pyproject_toml = toml.load(config_path)
        config = pyproject_toml.get("tool", {}).get("bumpytrack", {})
    except RuntimeError:
        fail("Failed to load config file at '{config_path}'.")
    return config

def dispatch(args, config, config_path):
    if args.get("command") == "git-undo":
        do_git_undo(args, config, config_path)
    else:
        do_bump(args, config, config_path)

def commandline_entrypoint():
    # Parse args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version="Version: 1.1.3")  # Replaced by bumpytrack itself
    parser.add_argument("command", help="version token to bump ('major', 'minor' or 'patch') or 'git-undo' to remove any changes from Git")
    parser.add_argument("--current-version", help="force current version instead using version in config file")
    parser.add_argument("--new-version", help="force new version instead using version in config file")
    parser.add_argument("--git-commit", dest="git_commit", action="store_true", default=None, help="Git: Commit files with version replacements")
    parser.add_argument("--no-git-commit", dest="git_commit", action="store_false", default=None)
    parser.add_argument("--git-tag", dest="git_tag", action="store_true", default=None, help="Git: Tag this reference with the new version")
    parser.add_argument("--no-git-tag", dest="git_tag", action="store_false", default=None)
    parser.add_argument("--config-path", help="path to config file. Defaults to pyproject.toml in current directory")
    parser.add_argument("--verbose", action="store_true")
    args_namespace = parser.parse_args()
    args = vars(args_namespace)

    # Bootstrap
    logger.set_verbose(args.get("verbose"))
    config_path = args.get("config_path") or "pyproject.toml"
    config = load_config(config_path)

    dispatch(args, config, config_path)


if __name__ == "__main__":
    commandline_entrypoint()
