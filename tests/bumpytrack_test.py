# -*- coding: utf-8 -*-

import contextlib
import os
import shutil
import sys

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if assert_success:
        assert completed_process.returncode == 0

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

    return {
        "project_path": project_path_str,
        "config_path": config_path_str,
        "replaceable_file_path": replaceable_file_path_str,
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


# Feature/Integration Tests ####################################################


def test_cli_info():
    completed_process = run("bumpytrack -h")
    assert "usage:" in completed_process.stdout

    completed_process = run("bumpytrack --version")
    # Add stdout and stderr not to restrict where the version is actually written
    process_output = completed_process.stdout.strip() + completed_process.stderr.strip()
    assert process_output == b"Version: 1.1.3"  # Replaced by bumpytrack itself


def test_bump_replaces_version_in_files(project_context):
    with cwd_at(project_context["project_path"]):
        completed_process = run(
            "bumpytrack minor --no-git-commit --no-git-tag --config-path " + project_context["config_path"]
        )
        assert completed_process.stdout.strip() == \
               b"Current version: '1.2.3'\n" \
               b"New version: '1.3.0'\n" \
               b"Replacing version srting in files"
        with open(project_context["config_path"], "rb") as f:
            config_file_contents = f.read()
            assert b"1.3.0" in config_file_contents
        with open(project_context["replaceable_file_path"], "rb") as f:
            replaceable_file_contents = f.read()
            assert b"1.3.0" in replaceable_file_contents
            assert b"\xc3\xa1\xc3\xa8\xc4\xa9\xc3\xb4\xc3\xbc" in replaceable_file_contents  # UTF-8 for "áèĩôü"


# Unit Tests ###################################################################


def test_version_incrementing(fail_mocking):
    fail_mock, stopping_at_fail = fail_mocking
    
    assert stopping_at_fail(bumpytrack.increment_version)("1.2.3", "major") == "2.0.0"
    assert stopping_at_fail(bumpytrack.increment_version)("1.2.3", "minor") == "1.3.0"
    assert stopping_at_fail(bumpytrack.increment_version)("1.2.3", "patch") == "1.2.4"
