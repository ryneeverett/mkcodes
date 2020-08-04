import os
from pathlib import Path
import re
import warnings

import click

try:
    import markdown as markdown_enabled
except ImportError:
    markdown_enabled = False
else:
    from markdown.extensions import Extension
    from markdown.treeprocessors import Treeprocessor


def github_codeblocks(filepath, safe):
    codeblocks = []
    codeblock_re = r'^```.*'
    codeblock_open_re = r'^```(`*)(py|python){0}$'.format('' if safe else '?')

    with open(filepath, 'r') as f:
        block = []
        python = True
        in_codeblock = False

        for line in f.readlines():
            codeblock_delimiter = re.match(codeblock_re, line)

            if in_codeblock:
                if codeblock_delimiter:
                    if python:
                        codeblocks.append(''.join(block))
                    block = []
                    python = True
                    in_codeblock = False
                else:
                    block.append(line)
            elif codeblock_delimiter:
                in_codeblock = True
                if not re.match(codeblock_open_re, line):
                    python = False
    return codeblocks


def markdown_codeblocks(filepath, safe):
    import markdown

    codeblocks = []

    if safe:
        warnings.warn("'safe' option not available in 'markdown' mode.")

    class DoctestCollector(Treeprocessor):
        def run(self, root):
            nonlocal codeblocks
            codeblocks = (block.text for block in root.iterfind('./pre/code'))

    class DoctestExtension(Extension):
        def extendMarkdown(self, md, md_globals):
            md.registerExtension(self)
            md.treeprocessors.add("doctest", DoctestCollector(md), '_end')

    doctestextension = DoctestExtension()
    markdowner = markdown.Markdown(extensions=[doctestextension])
    markdowner.convertFile(str(filepath), output=os.devnull)
    return codeblocks


def get_files(inputs):
    """ Yield the files and parent dirs from an iterable of paths. """
    markdown_extensions = ['.markdown', '.mdown', '.mkdn', '.mkd', '.md']
    for i in inputs:
        path = Path(i)
        if path.is_dir():
            for child in path.rglob('*'):
                if child.is_file() and child.suffix in markdown_extensions:
                    yield child, path
        elif path.suffix in markdown_extensions:
            yield path, path.parent

def add_inits_to_dir(path):
    """Recursively add __init__.py files to a directory
    This compensates for https://bugs.python.org/issue23882 and https://bugs.python.org/issue35617
    """
    for child in path.rglob('*'):
        if child.is_dir():
            (child / '__init__.py').touch()


@click.command()
@click.argument(
    'inputs', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--output', default='{name}.py')
@click.option('--github/--markdown', default=bool(not markdown_enabled),
              help='Github-flavored fence blocks or pure markdown.')
@click.option('--safe/--unsafe', default=True,
              help='Allow code blocks without language hints.')
@click.option('--package-python', default=True,
              help='Add __init__.py files to python output to aid in test discovery')
def main(inputs, output, github, safe, package_python):
    collect_codeblocks = github_codeblocks if github else markdown_codeblocks
    outputbasedir = Path(output).parent
    outputbasename = Path(output).name

    for filepath, input_path in get_files(inputs):
        codeblocks = collect_codeblocks(filepath, safe)

        if codeblocks:
            fp = Path(filepath)
            filedir = fp.parent.relative_to(input_path)
            filename = fp.stem
            outputfilename = outputbasedir / filedir / outputbasename.format(name=filename)

            outputfilename.parent.mkdir(parents=True, exist_ok=True)
            outputfilename.write_text('\n\n'.join(codeblocks))
            if package_python:
                add_inits_to_dir(outputbasedir)

            if package_python:
                add_inits_to_dir(outputbasedir)
