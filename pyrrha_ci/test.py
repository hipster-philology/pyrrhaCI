from .code import PyrrhaCI, Rule, _Ret
from unittest import TestCase


class TestPyrrhaCi(TestCase):
    def setUp(self) -> None:
        self.errors = []

    def reroute_print(self, *args, **kwargs):
        self.errors.append((args, kwargs))

    def make_pyrrha_ci(self, **kwargs) -> PyrrhaCI:
        test = PyrrhaCI(**kwargs)
        test.static_print = self.reroute_print
        return test

    def test_allowed_lemma(self):
        test = self.make_pyrrha_ci(
            expected_columns=["token", "lemma"],
            allowed_lemma={"Key": set(), "WithPOS": {"aPos"}}
        )
        self.assertEqual(test._test_lemma("Key"), _Ret(0, False, True, False), "Test succeeded")
        self.assertEqual(test._test_lemma("Nonexistent"), _Ret(1, True, True, False), "Test Failed")
