import os
import shutil
import textwrap
import unittest
import subprocess


class TestBase(unittest.TestCase):
    output = 'tests/output.py'

    def tearDown(self):
        self.remove(self.output)

    @staticmethod
    def remove(f):
        try:
            os.remove(f)
        except FileNotFoundError:
            pass

    @classmethod
    def call(cls, *flags, inputfile='tests/data/some.md'):
        subprocess.call(
            ['mkcodes', '--output', cls.output] + list(flags) + [inputfile])

    def assertFileEqual(self, filename, expected):
        with open(filename, 'r') as output:
            self.assertEqual(output.read(), textwrap.dedent(expected))

    def assertOutput(self, expected):
        self.assertFileEqual(self.output, expected)


class TestMarkdown(TestBase):
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
        self.assertTrue(os.path.exists(self.output))

    def test_directory(self):
        self.call(inputfile='tests/data')
        self.assertTrue(os.path.exists(self.output))

    def test_multiple(self):
        try:
            subprocess.call([
                'mkcodes', '--output', 'tests/{name}.py', '--github',
                'tests/data/some.md', 'tests/data/other.md'])
            self.assertFileEqual('tests/some.py', """\
                bar = False


                backticks = range(5, 7)
                """)
            self.assertFileEqual('tests/other.py', """\
                qux = 4
                """)
        finally:
            self.remove('tests/some.py')
            self.remove('tests/other.py')

    def test_unexistant_output_directory(self):
        try:
            subprocess.call([
                'mkcodes', '--output', 'tests/unexistant/{name}.py',
                '--github', 'tests/data/some.md'])
            self.assertFileEqual('tests/unexistant/some.py', """\
                bar = False


                backticks = range(5, 7)
                """)
        finally:
            shutil.rmtree('tests/unexistant')

    @unittest.skip
    def test_glob(self):
        raise NotImplementedError


if __name__ == '__main__':
    unittest.main()
