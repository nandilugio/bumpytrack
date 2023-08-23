import contextlib
import os
import shutil
import subprocess

import pytest

import bumpytrack


# Utils ########################################################################


@contextlib.contextmanager
def cwd_at(path):
    original_wd = os.getcwd()
    os.chdir(path)
    try: yield
    finally: os.chdir(original_wd)


def run(command, assert_success=True):
    completed_process = subprocess.run(
        command,
        shell=True,
        encoding='utf-8',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if assert_success:
        if completed_process.returncode != 0:
            print("Non-zero exit running " + command)
            print("Stdout was:\n" + completed_process.stdout)
            print("Stderr was:\n" + completed_process.stderr)
            assert False

    return completed_process


# Fixtures #####################################################################


@pytest.fixture
def project_context(tmpdir):
    project_path = tmpdir
    project_path_str = str(project_path)

    config_path_str = str(project_path.join("pyproject.toml"))
    replaceable_file_path_str = str(project_path.join("replaceable.txt"))
    source_file_path_str = str(project_path.join("source.txt"))

    shutil.copyfile("tests/data/integration_tests_pyproject.toml", config_path_str)
    shutil.copyfile("tests/data/replaceable.txt", replaceable_file_path_str)
    shutil.copyfile("tests/data/source.txt", source_file_path_str)

    with cwd_at(project_path_str):
        run("git init")
        run("git config user.email \"test@test.test\"")
        run("git config user.name test")
        run("git add .")
        run("git commit -m \"Initial commit.\"")

    return {
        "project_path": project_path_str,
        "config_path": config_path_str,
        "replaceable_file_path": replaceable_file_path_str,
        "source_file_path": source_file_path_str,
    }


@pytest.fixture
def fail_mocking(mocker):
    class FailCalled(RuntimeError): pass

    def fail_called(*_args, **_kwargs):
        raise FailCalled()

    def stopping_at_fail(callback):
        def wrapper(*args, **kwargs):
            try:
                return callback(*args, **kwargs)
            except FailCalled:
                pass
        return wrapper

    fail_mock = mocker.patch("bumpytrack.fail", side_effect=fail_called)

    return fail_mock, stopping_at_fail


# End-to-End Tests #############################################################


def test_cli_info():
    completed_process = run("bumpytrack -h")
    assert "usage:" in completed_process.stdout

    completed_process = run("bumpytrack --version")
    # Add stdout and stderr not to restrict where the version is actually written
    process_output = completed_process.stdout.strip() + completed_process.stderr.strip()
    assert process_output == "Version: 1.1.5"  # Replaced by bumpytrack itself


def test_bump_replaces_version_in_files(project_context):
    with cwd_at(project_context["project_path"]):
        completed_process = run(
            "bumpytrack minor --no-git-commit --no-git-tag --config-path " + project_context["config_path"]
        )
        assert completed_process.stdout.strip() == \
               "Current version: '1.2.3'.\n" \
               "New version: '1.3.0'.\n" \
               "Replacing version string in files..."
        with open(project_context["config_path"], "r", encoding="utf-8") as f:
            config_file_contents = f.read()
            assert "1.3.0" in config_file_contents
        with open(project_context["replaceable_file_path"], "r", encoding="utf-8") as f:
            replaceable_file_contents = f.read()
            assert "1.3.0" in replaceable_file_contents
            assert "áèĩôü" in replaceable_file_contents


def test_bump_commits_and_tags_repo(project_context):
    with cwd_at(project_context["project_path"]):
        completed_process = run("git log --oneline")
        assert "Bumping version" not in completed_process.stdout

        run("bumpytrack patch --git-commit --git-tag --config-path " + project_context["config_path"])

        completed_process = run("git log --oneline")
        assert "Bumping version: 1.2.3 → 1.2.4" in completed_process.stdout

        completed_process = run("git describe --tags --abbrev=0")
        assert completed_process.stdout.strip() == "v1.2.4"


def test_git_undo_removes_latest_bump_and_nothing_else(project_context):
    with cwd_at(project_context["project_path"]):

        # Build previous state, containing other bumps
        run("bumpytrack major --git-commit --git-tag --config-path " + project_context["config_path"])  # Bumps to 2.0.0
        with open(project_context["source_file_path"], "w", encoding="utf-8") as f: f.write("New source line.")
        run("git add .")
        run("git commit -m \"Some changes...\"")

        # Remember the state we want to be in after we undo
        git_log_before_last_bump = run("git log --oneline").stdout
        git_tags_before_last_bump = run("git tag").stdout
        cat_project_before_last_bump = run("cat ./*").stdout

        # Bump we want to undo
        run("bumpytrack minor --git-commit --git-tag --config-path " + project_context["config_path"])  # Bumps to 2.1.0

        # Assert there are changes in git and in the files
        assert run("git log --oneline").stdout != git_log_before_last_bump
        assert run("git tag").stdout != git_tags_before_last_bump
        assert run("cat ./*").stdout != cat_project_before_last_bump

        # Undo!
        completed_process = run("bumpytrack git-undo --config-path " + project_context["config_path"])

        # Assert undo was ok and we're in the same situation as before last bump
        assert completed_process.stdout.strip() == \
               "Undoing bump to version: '2.1.0'.\n" \
               "Bump commit undone.\n" \
               "Bump tag removed."
        assert run("git log --oneline").stdout == git_log_before_last_bump
        assert run("git tag").stdout == git_tags_before_last_bump
        assert run("cat ./*").stdout == cat_project_before_last_bump

        # Try undoing again
        completed_process = run("bumpytrack git-undo --config-path " + project_context["config_path"], assert_success=False)

        # Assert undo didn't take effect and we're still in the same situation as before last bump
        assert completed_process.returncode != 0
        assert completed_process.stdout.strip() == "Undoing bump to version: '2.0.0'."
        assert completed_process.stderr.strip() == "Can only undo bumps corresponding to the most recent commit.\nAborting!"
        assert run("git log --oneline").stdout == git_log_before_last_bump
        assert run("git tag").stdout == git_tags_before_last_bump
        assert run("cat ./*").stdout == cat_project_before_last_bump


def test_git_undo_removes_latest_bump_commit_or_tag_separately(project_context):
    with cwd_at(project_context["project_path"]):

        # Build previous state, containing other bumps
        run("bumpytrack patch --git-commit --git-tag --config-path " + project_context["config_path"])  # Bumps to 1.2.4
        with open(project_context["source_file_path"], "w", encoding="utf-8") as f: f.write("New source line.")
        run("git add .")
        run("git commit -m \"Some changes...\"")

        # Remember the state we want to be in after we undo
        git_log_before_last_bump = run("git log --oneline").stdout
        git_tags_before_last_bump = run("git tag").stdout
        cat_project_before_last_bump = run("cat ./*").stdout

        # Bump we want to undo: only commit
        run("bumpytrack minor --git-commit --config-path " + project_context["config_path"])  # Bumps to 1.3.0

        # Assert there are changes in git log and in the files...
        assert run("git log --oneline").stdout != git_log_before_last_bump
        assert run("cat ./*").stdout != cat_project_before_last_bump

        # ...but not in the git tags
        assert run("git tag").stdout == git_tags_before_last_bump

        # Undo!
        completed_process = run("bumpytrack git-undo --config-path " + project_context["config_path"])

        # Assert undo was ok and we're in the same situation as before last bump
        assert completed_process.stdout.strip() == \
               "Undoing bump to version: '1.3.0'.\n" \
               "Bump commit undone.\n" \
               "Could not delete tag 'v1.3.0'. Did it exist?"
        assert run("git log --oneline").stdout == git_log_before_last_bump
        assert run("git tag").stdout == git_tags_before_last_bump
        assert run("cat ./*").stdout == cat_project_before_last_bump

        # Try undoing again
        completed_process = run("bumpytrack git-undo --config-path " + project_context["config_path"], assert_success=False)

        # Assert undo didn't take effect and we're still in the same situation as before last bump
        assert completed_process.returncode != 0
        assert completed_process.stdout.strip() == "Undoing bump to version: '1.2.4'."
        assert completed_process.stderr.strip() == "Can only undo bumps corresponding to the most recent commit.\nAborting!"
        assert run("git log --oneline").stdout == git_log_before_last_bump
        assert run("git tag").stdout == git_tags_before_last_bump
        assert run("cat ./*").stdout == cat_project_before_last_bump


# Unit Tests ###################################################################


def test_version_incrementing(fail_mocking):
    fail_mock, stopping_at_fail = fail_mocking

    fail_mock.assert_not_called()
    stopping_at_fail(bumpytrack.increment_version)("1.2.3", "not_a_valid_part")
    fail_mock.assert_called_once_with("Part 'not_a_valid_part' not recognized. Should be one of: major, minor or patch.")

    assert stopping_at_fail(bumpytrack.increment_version)("1.2.3", "major") == "2.0.0"
    assert stopping_at_fail(bumpytrack.increment_version)("1.2.3", "minor") == "1.3.0"
    assert stopping_at_fail(bumpytrack.increment_version)("1.2.3", "patch") == "1.2.4"
