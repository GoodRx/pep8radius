from difflib import unified_diff
import os
from shutil import rmtree
from subprocess import CalledProcessError
import sys

if sys.version_info < (2, 7):
    from unittest2 import main, SkipTest, TestCase
else:
    from unittest import main, SkipTest, TestCase

# This ensures we are using the latest, without being in a package.
ROOT_DIR = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
sys.path.insert(0, ROOT_DIR)
from btyfi import Radius, RadiusGit, RadiusHg, check_output


def _in_test_directory():
    "If not in this directory, version control won't work correctly."
    # TODO just move to dir then move back?
    here, _ = os.path.split(os.path.realpath(__file__))
    return here == os.getcwd()


class TestRadius(TestCase):

    def __init__(self, *args, **kwargs):
        self._in_test_directory = _in_test_directory()
        self.using_vc = self.init_vc()
        super(TestRadius, self).__init__(*args, **kwargs)

    def init_vc(self):
        if not self._in_test_directory:
            return False
        return self.delete_and_create_repo()

    def setUp(self):
        if not self._in_test_directory:
            raise SkipTest("Not in test directory.")
        if not self.using_vc:
            raise SkipTest("%s not available" % self.vc)

    def check(self, original, modified, expected, test_name='check'):
        """Modify original to modified, and check that pep8radius
        turns this into expected."""

        temp_file = 'temp.py'

        with open(temp_file, 'w') as f:
            f.write(original)
        committed = self.successfully_commit_files([temp_file])

        with open(temp_file, 'w') as f:
            f.write(modified)

        # Run pep8radius
        r = Radius.new(vc=self.vc)
        r.pep8radius()

        with open(temp_file, 'r') as f:
            result = f.read()
        self.assert_equal(result, expected, test_name)

        # Run pep8radius again, it *should* be that this doesn't do anything.
        r.pep8radius()
        with open(temp_file, 'r') as f:
            result = f.read()
        self.assert_equal(result, expected, test_name)

    def assert_equal(self, result, expected, test_name):
        """like assertEqual but with a nice diff output if not equal"""
        self.assertEqual(result, expected,
                         self.diff(expected, result, test_name))

    # This is similar to autopep8's get_diff_text
    @staticmethod
    def diff(expected, result, file_name):
        """Return text of unified diff between old and new."""
        result, expected = result.splitlines(True), expected.splitlines(True)
        newline = '\n'
        diff = unified_diff(expected, result,
                            file_name + '/expected',
                            file_name + '/result',
                            lineterm=newline)
        text = newline
        for line in diff:
            text += line
            # Work around missing newline (http://bugs.python.org/issue2142).
            if not line.endswith(newline):
                text += newline + r'\ No newline at end of file' + newline
        return text


class MixinTests:

    """All Radius tests are placed in this class"""

    def test_one_line(self):
        original = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=2; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        modified = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=42; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        expected = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        self.check(original, modified, expected, 'test_one_line')


class TestRadiusGit(TestRadius, MixinTests):
    vc = 'git'

    def delete_and_create_repo(self):
        try:
            rmtree(os.path.join(os.getcwd(), '.git'))
        except OSError:
            pass
        try:
            check_output(["git", "init"])
            return True
        except (OSError, CalledProcessError):
            return False

    def successfully_commit_files(self, file_names,
                                  commit="initial_commit"):
        try:
            check_output(["git", "add"] + file_names)
            check_output(["git", "commit", "-m", commit])
            return True
        except (OSError, CalledProcessError):
            return False


class TestRadiusHg(TestRadius, MixinTests):
    vc = 'hg'

    def delete_and_create_repo(self):
        try:
            rmtree(os.path.join(os.getcwd(), '.hg'))
        except OSError:
            pass
        try:
            check_output(["hg", "init"])
            return True
        except (OSError, CalledProcessError):
            return False

    def successfully_commit_files(self, file_names,
                                  commit="initial_commit"):
        try:
            check_output(["hg", "add"] + file_names)
            check_output(["hg", "commit", "-m", commit])
            return True
        except (OSError, CalledProcessError):
            return False

if __name__ == '__main__':
    main()
