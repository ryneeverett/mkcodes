import os
from pathlib import Path
import re
import glob
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
    """ Take in an iterable of paths, yield the files and parent dirs in those paths"""
    markdown_extensions = ['.markdown', '.mdown', '.mkdn', '.mkd', '.md']
    for i in inputs:
        path = Path(i)
        if path.is_dir():
            """ let's iterate the directory and yield files """
            for child in path.rglob('*'):
                if child.is_file() and child.suffix in markdown_extensions:
                    yield child, path
        else:
            if path.suffix in markdown_extensions:
                yield path, path.parent


def makedirs(directory):
    to_make = []

    while directory:
        try:
            os.mkdir(directory)
        except FileNotFoundError:
            directory, tail = os.path.split(directory)
            to_make.append(tail)
        else:
            with open(os.path.join(directory, '__init__.py'), 'w'):
                pass
            if to_make:
                directory = os.path.join(directory, to_make.pop())
            else:
                break


@click.command()
@click.argument(
    'inputs', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--output', default='{name}.py')
@click.option('--github/--markdown', default=bool(not markdown_enabled),
              help='Github-flavored fence blocks or pure markdown.')
@click.option('--safe/--unsafe', default=True,
              help='Allow code blocks without language hints.')
def main(inputs, output, github, safe):
    collect_codeblocks = github_codeblocks if github else markdown_codeblocks
    # to output deep trees with a file pattern
    # we should break out the directory and the filename pattern
    outputbasedir = Path(output).parent
    outputbasename = Path(output).name

    for filepath, input_path in get_files(inputs):
        codeblocks = collect_codeblocks(filepath, safe)

        if codeblocks:
            #we want the path to the file, and the file without an extension
            fp = Path(filepath)
            filedir =fp.parent.relative_to(input_path)
            filename = fp.stem

            # stitch together the OUTPUT base directory, with the input directories
            # add the file format at the end.
            outputfilename = outputbasedir / filedir / outputbasename.format(name=filename)

            outputdir = os.path.dirname(outputfilename)
            if not os.path.exists(outputdir):
                makedirs(outputdir)

            with open(outputfilename, 'w') as outputfile:
                outputfile.write('\n\n'.join(codeblocks))
