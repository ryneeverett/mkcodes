""" XXX Note, this doesn't work because `filename` is undefined."""
import os

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


class CodeCollector(Treeprocessor):
    def run(self, root):

        codeblocks = (block.text for block in root.iterfind('./pre/code'))

        with open(OUTPUTFILENAME, 'w') as outputfile:
            outputfile.write('\n\n'.join(codeblocks))


class MkcodeExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {'output': '{name}.py'}
        return super(MkcodeExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.treeprocessors.add("doctest", CodeCollector(md), '_end')

        global OUTPUTFILENAME
        OUTPUTFILENAME = self.getConfig('output').format(
            name=os.path.splitext(filename)[0])

def makeExtension(**kwargs):
    return MkcodeExtension(**kwargs)
