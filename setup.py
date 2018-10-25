import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="bumpytrack",
    version="0.2.0",
    description="Simple semantic-version bumper in python that works.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nandilugio/bumpytrack",
    author="Fernando Stecconi",
    author_email="nandilugio@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pyyaml",
        "subprocess32",
    ],
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "bumpytrack = bumpytrack.bumpytrack:commandline_entrypoint",
        ]
    }
)

