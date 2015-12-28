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


def iglob(input):
    try:
        return glob.iglob(input + '/**', recursive=True)
    except TypeError:
        warnings.warn('In python<3.5, inputs are not recursive.')
        return glob.iglob(input + '/*')


def default_state():
    return [], True, False


def github_codeblocks(filename, safe):
    codeblocks = []
    codeblock_re = r'^```.*'
    codeblock_open_re = r'^```(py|python){0}$'.format('' if safe else '?')

    with open(filename, 'r') as f:
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


def markdown_codeblocks(filename, safe):
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
    markdowner.convertFile(filename, output=os.devnull)
    return codeblocks


def is_markdown(f):
    markdown_extensions = ['.markdown', '.mdown', '.mkdn', '.mkd', '.md']
    return os.path.splitext(f)[1] in markdown_extensions


def get_files(inputs):
    for i in inputs:
        if os.path.isdir(i):
            yield from filter(is_markdown, iglob(i))
        elif is_markdown(i):
            yield i


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

    for filename in get_files(inputs):
        code = '\n\n'.join(collect_codeblocks(filename, safe))

        inputname = os.path.splitext(os.path.basename(filename))[0]
        outputfilename = output.format(name=inputname)

        with open(outputfilename, 'w') as outputfile:
            outputfile.write(code)
