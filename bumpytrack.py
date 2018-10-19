import logging
import os
import yaml

log = logging.getLogger()


def fail(message):
    import pdb; pdb.set_trace()
    log.error(message)
    exit(1)


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
    elif part == "tiny":
        new_version_tokens = [current_version_tokens[0], current_version_tokens[1], current_version_tokens[2] + 1]
    else:
        fail("Part should be one of: major, minor or tiny.")

    return version_tokens_to_str(new_version_tokens)


def file_replace(file_replace_config, current_version, new_version):
    search = file_replace_config["search_template"].format(version=current_version)
    replace = file_replace_config["search_template"].format(version=new_version)

    file_path = file_replace_config["path"]
    if not os.access(file_path, os.R_OK | os.W_OK):
        fail(f"File {file_path} not found or not accessible")

    original_file_contents = None
    with open(file_replace_config["path"], "r") as file:
        original_file_contents = file.read()

    new_file_contents = original_file_contents.replace(search, replace)

    with open(file_replace_config["path"], "w") as file:
        file.write(new_file_contents)


def git_commit(current_version, new_version):
    raise NotImplementedError


def git_tag(new_version):
    raise NotImplementedError


def main(**args):
    log_level = args.get("log_level") or "INFO"
    try:
        log.setLevel(getattr(logging, log_level.upper()))
    except AttributeError:
        fail("Log level should be one of Python's valid log level names.")

    # Load config
    config_path = args.get("config_path") or ".bumpytrack.yml"
    config = yaml.load(open(config_path))

    # Get current version
    current_version = args.get("current_version") or config.get("current_version")
    if not current_version:
        fail("No way to obtain current version")
    log.info(f"Current version: {current_version}")

    # Get new version
    if args.get("new_version"):
        new_version = args.get("new_version")
    elif args.get("part"):
        new_version = increment_version(current_version, args.get("part"))
    else:
        fail("No way to obtain a new version")
    log.info(f"New version: {new_version}")

    # Replace version in config file and other configured files
    file_replace_configs = [{"path": config_path, "search_template": "current_version: {version}"}]
    file_replace_configs += config.get("file_replaces", [])
    for file_replace_config in file_replace_configs:
        log.info(f"Replacing version in file {file_replace_config['path']}")
        file_replace(file_replace_config, current_version, new_version)

    # Git commit file changes
    if args.get("git_commit", config.get("git_commit")):
        log.info("Committing changes to GIT")
        git_commit(current_version, new_version)

    # Git tag new version
    if args.get("git_tag", config.get("git_tag")):
        log.info("Adding version tag to GIT")
        git_tag(new_version)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("part", help="major, minor or tiny")
    parser.add_argument("--current-version")
    parser.add_argument("--new-version")
    parser.add_argument("--git-commit")
    parser.add_argument("--git-tag")
    parser.add_argument("--config-path")
    parser.add_argument("--log-level")
    args_namespace = parser.parse_args()
    args = vars(args_namespace)

    main(**args)
