from pepython.task_def import task, s


@task
def clean():
    s("rm -rf build dist *.egg-info")
    s("pipenv install -e .")


@task
def build():
    s("pipenv run pip install --upgrade setuptools wheel")  # We _really_ want last versions ;p
    clean()
    s("pipenv run python setup.py sdist bdist_wheel")


@task
def publish():
    #s("pipenv run twine upload --repository-url https://test.pypi.org/legacy/ dist/*", interactive=True)
    s("pipenv run twine upload dist/*", interactive=True)


@task
def build_and_publish():
    build()
    publish()
