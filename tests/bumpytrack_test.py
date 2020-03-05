# -*- coding: utf-8 -*-

import codecs
import contextlib
import os
import shutil
import sys

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess

import pytest
import six

import bumpytrack


@contextlib.contextmanager
def cwd_at(path):
    original_wd = os.getcwd()
    os.chdir(path)
    try: yield
    finally: os.chdir(original_wd)


@pytest.fixture
def project_context(tmpdir):
    project_path = tmpdir
    config_path = project_path.join("pyproject.toml")
    replaceable_file_path = project_path.join("replaceable.txt")
    shutil.copyfile("tests/data/integration_tests_pyproject.toml", str(config_path))
    shutil.copyfile("tests/data/replaceable.txt", str(replaceable_file_path))

    return {
        "project_path": str(project_path),
        "config_path": str(config_path),
        "replaceable_file_path": str(replaceable_file_path),
    }


@pytest.fixture
def fail_mocking(mocker):
    FailCalled = type("FailCalled", (RuntimeError,), {})

    def fail_called(*args, **kwargs):
        raise FailCalled()

    def stopping_at_fail(callback):
        def wrapper(*args, **kwargs):
            try:
                return callback(*args, **kwargs)
            except FailCalled:
                pass
        return wrapper

    fail_mock = mocker.patch("bumpytrack.fail", side_effect=fail_called)

    return (fail_mock, stopping_at_fail)


def test_cli_info():
    completed_process = subprocess.run(["bumpytrack", "-h"])
    assert completed_process.returncode == 0
    
    completed_process = subprocess.run(
        ["bumpytrack", "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    assert completed_process.returncode == 0
    assert completed_process.stdout.strip() == b"Version: 1.1.3"  # Replaced by bumpytrack itself


def test_integration(project_context):
    with cwd_at(project_context["project_path"]):
        completed_process = subprocess.run(
            [
                "bumpytrack", "minor",
                "--no-git-commit", "--no-git-tag",
                "--config-path", project_context["config_path"]
            ],
            stdout=subprocess.PIPE
        )
        
        assert completed_process.returncode == 0
        assert completed_process.stdout.strip() == \
            b"Current version: '1.2.3'\n" \
            b"New version: '1.3.0'\n" \
            b"Replacing version srting in files"
        with open(project_context["replaceable_file_path"], "rb") as f:
            replaceable_file_contents = f.read()
            assert b"1.3.0" in replaceable_file_contents
            assert b"\xc3\xa1\xc3\xa8\xc4\xa9\xc3\xb4\xc3\xbc" in replaceable_file_contents  # UTF-8 for áèĩôü


def test_version_incrementing(fail_mocking):
    fail_mock, stopping_at_fail = fail_mocking
    
    assert stopping_at_fail(bumpytrack.increment_version)("1.2.3", "major") == "2.0.0"
    assert stopping_at_fail(bumpytrack.increment_version)("1.2.3", "minor") == "1.3.0"
    assert stopping_at_fail(bumpytrack.increment_version)("1.2.3", "patch") == "1.2.4"
