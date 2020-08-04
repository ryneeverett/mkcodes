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

"""
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
"""
# much easier to write the other names that an extension is known by
ext_map = {'py': ['python', 'py', 'python2', 'python3', 'py2', 'py3', 'PYTHON', 'Python']}
ext_map['cs'] = ['c#','csharp', 'c-sharp', 'cs', 'CS', 'CSHARP', 'C#']
ext_map['java'] = ['java', 'JAVA', 'Java']
# then invert that mapping
language_map = {}
for ext, lang_strings in ext_map.items():
    for lang_string in lang_strings:
        language_map[lang_string] = ext


def github_codeblocks(filepath, safe, default_lang='py'):
    codeblocks = {}
    codeblock_re = r'^```.*'
    codeblock_open_re = r'^```(`*)(py|python){0}$'.format('' if safe else '?')

    with open(filepath, 'r') as f:
        block = []
        language = None
        in_codeblock = False

        for line in f.readlines():
            # does this line contain a codeblock begin or end?
            codeblock_delimiter = re.match(codeblock_re, line)

            if in_codeblock:
                if codeblock_delimiter:
                    # we are closing a codeblock
                    if language:
                        # finished a codeblock, append everything
                        # codeblocks.append(''.join(block))
                        # import pudb; pu.db
                        blocks = codeblocks.get(language, [])
                        blocks.append(''.join(block))
                        codeblocks[language] = blocks

                    block = []
                    if safe:
                        language = None
                    in_codeblock = False
                else:
                    block.append(line)
            elif codeblock_delimiter:
                # beginning a codeblock
                in_codeblock = True
                # does it have a language?
                lang_match = re.match(codeblock_open_re, line)
                if lang_match:
                    language = lang_match.group(2)
                    if not safe:
                        # we can sub a default language if not safe
                        language = language or default_lang
                else:
                    if safe:
                        language = None
                    else:
                        language = default_lang
    return codeblocks

def github_markdown_codeblocks(filepath, safe, default_lang='py'):
    import markdown
    codeblocks = {}
    if safe:
        warnings.warn("'safe' option not available in 'github-markdown' mode.")

    class DoctestCollector(Treeprocessor):
        def run(self, root):
            nonlocal codeblocks
            codeblocks[default_lang] = (block.text for block in root.iterfind('./pre/code'))

    class DoctestExtension(Extension):
        def extendMarkdown(self, md, md_globals):
            md.registerExtension(self)
            md.treeprocessors.add("doctest", DoctestCollector(md), '_end')

    doctestextension = DoctestExtension()
    markdowner = markdown.Markdown(extensions=['fenced_code', doctestextension])
    markdowner.convertFile(input=str(filepath), output=os.devnull)
    return codeblocks



def markdown_codeblocks(filepath, safe, default_lang='py'):
    import markdown

    codeblocks = {}

    if safe:
        warnings.warn("'safe' option not available in 'markdown' mode.")

    class DoctestCollector(Treeprocessor):
        def run(self, root):
            nonlocal codeblocks
            codeblocks[default_lang] = (block.text for block in root.iterfind('./pre/code'))

    class DoctestExtension(Extension):
        def extendMarkdown(self, md, md_globals):
            md.registerExtension(self)
            md.treeprocessors.add("doctest", DoctestCollector(md), '_end')

    doctestextension = DoctestExtension()
    markdowner = markdown.Markdown(extensions=[doctestextension])
    markdowner.convertFile(input=str(filepath), output=os.devnull)
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

def add_inits_along_path(from_path, to_path):
    """Recursively add __init__.py files to a directory
    This compensates for https://bugs.python.org/issue23882 and https://bugs.python.org/issue35617
    """
    to_path = to_path.expanduser().resolve()
    from_path = from_path.expanduser().resolve()
    if to_path.relative_to_path(from_path):
        (to_path / '__init__.py').to_pathuch()
        if from_path.resolve() != to_path.parent.resolve():
            add_inits_along_path(from_path, to_path.parent()


@click.command()
@click.argument(
    'inputs', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--output', default='{name}.{ext}')
@click.option('--github/--markdown', default=bool(not markdown_enabled),
              help='Github-flavored fence blocks or pure markdown.')
@click.option('--safe/--unsafe', default=True,
              help='Allow code blocks without language hints.')
@click.option('--package-python', default=True,
              help='Add __init__.py files to python output to aid in test discovery')
@click.option('--default_lang', default='py',
              help='Assumed language for code blocks without language hits.')
def main(inputs, output, github, safe, package_python, default_lang):
    collect_codeblocks = github_codeblocks if github else markdown_codeblocks
    outputbasedir = Path(output).parent
    outputbasename = Path(output).name

    for filepath, input_path in get_files(inputs):
        codeblocks = collect_codeblocks(filepath, safe, default_lang)

        if codeblocks:
            fp = Path(filepath)
            filedir = fp.parent.relative_to(input_path)
            filename = fp.stem

            # stitch together the OUTPUT base directory with the input directories
            # add the file format at the end.
            for lang, blocks in codeblocks.items():
                outputfilename = outputbasedir / filedir / outputbasename.format(name=filename, ext=lang)

                # make sure path exists, don't care if it already does
                outputfilename.parent.mkdir(parents=True, exist_ok=True)
                outputfilename.write_text('\n\n'.join(blocks))
                if package_python and lang=='py':
                    add_inits_along_path(outputbasedir, outputfilename.parent)
