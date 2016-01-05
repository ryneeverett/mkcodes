import os
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
    markdowner.convertFile(filepath, output=os.devnull)
    return codeblocks


def is_markdown(f):
    markdown_extensions = ['.markdown', '.mdown', '.mkdn', '.mkd', '.md']
    return os.path.splitext(f)[1] in markdown_extensions


def get_nested_files(directory, depth):
    for i in glob.iglob(directory + '/*'):
        if os.path.isdir(i):
            yield from get_nested_files(i, depth+1)
        elif is_markdown(i):
            yield (i, depth)


def get_files(inputs):
    for i in inputs:
        if os.path.isdir(i):
            yield from get_nested_files(i, 0)
        elif is_markdown(i):
            yield (i, 0)


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

    for filepath, depth in get_files(inputs):
        codeblocks = collect_codeblocks(filepath, safe)

        if codeblocks:
            filename = os.path.splitext(filepath)[0]
            outputname = os.sep.join(filename.split(os.sep)[-1-depth:])

            outputfilename = output.format(name=outputname)

            outputdir = os.path.dirname(outputfilename)
            if not os.path.exists(outputdir):
                os.makedirs(outputdir)
                with open(os.path.join(outputdir, '__init__.py'), 'w'):
                    pass

            with open(outputfilename, 'w') as outputfile:
                outputfile.write('\n\n'.join(codeblocks))
