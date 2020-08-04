A command-line utility for pulling code blocks out of markdown files. Currently only handles python code blocks.

```sh
$ pip install -e git+https://github.com/ryneeverett/mkcodes.git#egg=mkcodes

# For traditional markdown code-block support.
$ pip install markdown

$ mkcodes --help
Usage: mkcodes [OPTIONS] INPUTS...

Options:
  --output TEXT
  --github / --markdown  Github-flavored fence blocks or pure markdown.
  --safe / --unsafe      Only use code blocks with language hints.
  --help                 Show this message and exit.
```

Why would I want such a thing?
------------------------------

My purpose is testing.

You can easily enough doctest a markdown file with `python -m doctest myfile.md`, but I don't like typing or looking at a whole bunch of `>>>` and `...`'s. Also there's no way that I know of to run linters against such code blocks.

Instead, I include (pytest) functional tests in my codeblocks, extract the code blocks with this script, and then run my test runner and linters against the output files.

Running Tests
-------------

```sh
python setup.py develop
./test
```
