import os
import shutil
import textwrap
import unittest
import subprocess

import click.testing

import mkcodes


class TestBase(unittest.TestCase):
    outputfile = 'tests/output/output.py'

    def tearDown(self):
        shutil.rmtree('tests/output', ignore_errors=True)

    @classmethod
    def call(cls, *flags, inputfile='tests/data/some.md'):
        runner = click.testing.CliRunner()
        runner.invoke(mkcodes.main,
                      ['--output', cls.outputfile] + list(flags) + [inputfile])

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
    def assertOutputFileEqual(self, filename, expected):
        self.assertFileEqual(os.path.join('tests/output', filename), expected)

    @staticmethod
    def _output_path_exists(path):
        return os.path.exists(os.path.join('tests/output', path))

    @classmethod
    def call(cls, *args, **kwargs):
        super().call('--github', *args, **kwargs)

    def test_file(self):
        self.call()
        self.assertTrue(self._output_path_exists('output.py'))

    def test_file_without_code(self):
        """Code files should not be written for markdown files with no code."""
        self.call(inputfile='tests/data/nocode.md')
        self.assertFalse(self._output_path_exists('nocode.py'))

    def test_directory(self):
        self.call(inputfile='tests/data')
        self.assertTrue(self._output_path_exists('output.py'))

    def test_directory_recursive(self):
        self.call(
            '--output', 'tests/output/{name}.py', '--github', 'tests/data')
        self.assertTrue(self._output_path_exists('some.py'))
        self.assertTrue(self._output_path_exists('other.py'))
        self.assertTrue(self._output_path_exists('nest/deep.py'))
        self.assertFalse(self._output_path_exists('not_markdown.py'))
        self.assertTrue(self._output_path_exists('nest/more/why.py'))

    def test_multiple(self):
        self.call(
            '--output', 'tests/output/{name}.py', '--github',
            'tests/data/some.md', 'tests/data/other.md')
        self.assertOutputFileEqual('some.py', """\
            bar = False


            backticks = range(5, 7)
            """)
        self.assertOutputFileEqual('other.py', """\
            qux = 4
            """)
        self.assertFalse(self._output_path_exists('nest/deep.py'))

    def test_unexistant_output_directory(self):
        self.call(
            '--output', 'tests/output/unexistant/{name}.py',
            '--github', 'tests/data/some.md')
        self.assertOutputFileEqual('unexistant/some.py', """\
            bar = False


            backticks = range(5, 7)
            """)

    def test_prefixed_deep_blocks(self):
        self.call(
            '--output', 'tests/output/test_{name}.py', '--github',
            'tests/data')
        self.assertTrue(self._output_path_exists('test_some.py'))
        self.assertTrue(self._output_path_exists('test_other.py'))
        self.assertTrue(self._output_path_exists('nest/test_deep.py'))
        self.assertTrue(self._output_path_exists('nest/more/test_why.py'))
        self.assertTrue(self._output_path_exists('nest/less/test_why.py'))

        # Check that mkcodes can actually output a valid test directory.
        proc = subprocess.run(
            ['python3', '-m', 'unittest', 'discover', 'tests/output'],
            capture_output=True, text=True)
        self.assertIn('Ran 2 tests', proc.stderr)
        self.assertIn('OK', proc.stderr)

    def test_other_languages(self):
        self.call(
            '--output', 'tests/output/test_{name}.{ext}',
            '--github', 'tests/langdata')
        self.assertTrue(self._output_path_exists('test_java.java'))
        self.assertTrue(self._output_path_exists('test_csharp.cs'))
        self.assertFalse(self._output_path_exists('test_csharp.csharp'))
        self.assertTrue(self._output_path_exists('test_multilang.cs'))
        self.assertTrue(self._output_path_exists('test_multilang.java'))
        self.assertTrue(self._output_path_exists('test_multilang.py'))
        self.assertTrue(self._output_path_exists('test_multilang.js'))
        self.assertTrue(self._output_path_exists('no_py_tree/test_clean.js'))
        self.assertFalse(self._output_path_exists('no_py_tree/__init__.py'))
        self.assertTrue(self._output_path_exists('pytree/test_buried.py'))
        self.assertTrue(self._output_path_exists('pytree/__init__.py'))

        # __init__.py should not be created in the base output directory.
        self.assertFalse(self._output_path_exists('__init__.py'))

    @unittest.skip
    def test_glob(self):
        raise NotImplementedError


if __name__ == '__main__':
    unittest.main()
