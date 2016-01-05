import os
import shutil
import textwrap
import unittest
import subprocess


class TestBase(unittest.TestCase):
    outputfile = 'tests/output/output.py'

    def tearDown(self):
        shutil.rmtree('tests/output', ignore_errors=True)

    @classmethod
    def call(cls, *flags, inputfile='tests/data/some.md'):
        subprocess.call([
            'mkcodes', '--output', cls.outputfile] + list(flags) + [inputfile])

    def assertFileEqual(self, filename, expected):
        with open(filename, 'r') as output:
            self.assertEqual(output.read(), textwrap.dedent(expected))


class TestMarkdown(TestBase):

    def assertOutput(self, expected):
        self.assertFileEqual(self.outputfile, expected)

    @unittest.skip
    def test_markdown_safe(self):
        raise NotImplementedError

    def test_github_safe(self):
        self.call('--github', '--safe')
        self.assertOutput("""\
            bar = False


            backticks = range(5, 7)
            """)

    def test_markdown_unsafe(self):
        self.call('--markdown', '--unsafe')
        self.assertOutput("""\
            baz = None
            """)

    def test_github_unsafe(self):
        self.call('--github', '--unsafe')
        self.assertOutput("""\
            foo = True


            bar = False


            backticks = range(5, 7)
            """)


class TestInputs(TestBase):
    @classmethod
    def call(cls, **kwargs):
        super().call('--github', **kwargs)

    def test_file(self):
        self.call()
        self.assertTrue(os.path.exists(self.outputfile))

    def test_file_without_code(self):
        """Code files should not be written for markdown files with no code."""
        self.call(inputfile='tests/data/nocode.md')
        self.assertFalse(os.path.exists('tests/output/nocode.py'))

    def test_directory(self):
        self.call(inputfile='tests/data')
        self.assertTrue(os.path.exists(self.outputfile))

    def test_directory_recursive(self):
        subprocess.call([
            'mkcodes', '--output', 'tests/output/{name}.py', '--github',
            'tests/data'])
        self.assertTrue(os.path.exists('tests/output/some.py'))
        self.assertTrue(os.path.exists('tests/output/other.py'))
        self.assertTrue(os.path.exists('tests/output/nest/deep.py'))

    def test_multiple(self):
        subprocess.call([
            'mkcodes', '--output', 'tests/output/{name}.py', '--github',
            'tests/data/some.md', 'tests/data/other.md'])
        self.assertFileEqual('tests/output/some.py', """\
            bar = False


            backticks = range(5, 7)
            """)
        self.assertFileEqual('tests/output/other.py', """\
            qux = 4
            """)
        self.assertFalse(os.path.exists('tests/output/nest/deep.py'))

    def test_unexistant_output_directory(self):
        subprocess.call([
            'mkcodes', '--output', 'tests/output/unexistant/{name}.py',
            '--github', 'tests/data/some.md'])
        self.assertFileEqual('tests/output/unexistant/some.py', """\
            bar = False


            backticks = range(5, 7)
            """)

    @unittest.skip
    def test_glob(self):
        raise NotImplementedError


if __name__ == '__main__':
    unittest.main()
