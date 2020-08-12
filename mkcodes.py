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

# There does not seem to be any specification for which info strings are
# accepted, but python-markdown passes it directly to pygments, so their
# mapping can be used as a guide:
# https://github.com/pygments/pygments/blob/master/pygments/lexers/_mapping.py
ext_map = {
    'cs': ['c#', 'csharp', 'c-sharp'],
    'py': ['python', 'python2', 'python3', 'py2', 'py3'],
}
# It's more straightforward to express the mappings by extension, but we
# actually need an inverted mapping.
language_map = {}
for ext, lang_strings in ext_map.items():
    for lang_string in lang_strings:
        language_map[lang_string] = ext


def github_codeblocks(filepath, safe, default_lang='py'):
    codeblocks = {}
    codeblock_re = r'^```.*'
    codeblock_open_re = r'^```(`*)(\w+){0}$'.format('' if safe else '?')

    with open(filepath, 'r') as f:
        # Initialize State
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
                        ext = language_map.get(language, language)
                        codeblocks.setdefault(ext, []).append(''.join(block))
                    else:
                        warnings.warn('No language hint found in safe mode. ' +
                                      'Skipping block beginning with: ' +
                                      block[0])

                    # Reset State
                    block = []
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
                    language = language.lower() if language else language
                    if not safe:
                        # we can sub a default language if not safe
                        language = language or default_lang
    return codeblocks


def markdown_codeblocks(filepath, safe, default_lang='py'):
    import markdown

    codeblocks = {}

    if safe:
        warnings.warn("'safe' option not available in 'markdown' mode.")

    class DoctestCollector(Treeprocessor):
        def run(self, root):
            nonlocal codeblocks
            codeblocks[default_lang] = (
                block.text for block in root.iterfind('./pre/code'))

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
    This compensates for https://bugs.python.org/issue23882
    and https://bugs.python.org/issue35617
    """
    to_path = to_path.expanduser().resolve()
    from_path = from_path.expanduser().resolve()

    # Sanity Check: This will raise an exception if paths aren't relative.
    to_path.relative_to(from_path)

    # Continue recursing if we haven't reached the base output directory.
    if to_path != from_path:
        (to_path / '__init__.py').touch()
        add_inits_along_path(from_path, to_path.parent)


@click.command()
@click.argument(
    'inputs', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--output', default='{name}.{ext}')
@click.option('--github/--markdown', default=bool(not markdown_enabled),
              help='Github-flavored fence blocks or pure markdown.')
@click.option('--safe/--unsafe', default=True,
              help='Allow code blocks without language hints.')
@click.option('--package-python', default=True, is_flag=True,
              help='Add __init__.py files to python dirs for test discovery')
@click.option('--default-lang', default='py',
              help='Assumed language for code blocks without language hints.')
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

            # stitch together the OUTPUT base directory with input directories
            # add the file format at the end.
            for lang, blocks in codeblocks.items():
                outputfilename = outputbasedir / filedir /\
                    outputbasename.format(name=filename, ext=lang)

                # make sure path exists, don't care if it already does
                outputfilename.parent.mkdir(parents=True, exist_ok=True)
                outputfilename.write_text('\n\n'.join(blocks))
                if package_python and lang == 'py':
                    add_inits_along_path(outputbasedir, outputfilename.parent)
