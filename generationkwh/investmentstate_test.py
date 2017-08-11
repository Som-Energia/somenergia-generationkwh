# -*- coding: utf-8 -*-

from generationkwh.investmentstate import InvestmentState
import unittest
from yamlns import namespace as ns
from .isodates import isodate

# Readable verbose testcase listing
unittest.TestCase.__str__ = unittest.TestCase.id


class InvestmentState_Test(unittest.TestCase):

    def assertNsEqual(self, dict1, dict2):
        def parseIfString(nsOrString):
            if type(nsOrString) in (dict, ns):
                return nsOrString
            return ns.loads(nsOrString)

        def sorteddict(d):
            if type(d) not in (dict, ns):
                return d
            return ns(sorted(
                (k, sorteddict(v))
                for k,v in d.items()
                ))
        dict1 = sorteddict(parseIfString(dict1))
        dict2 = sorteddict(parseIfString(dict2))

        return self.assertMultiLineEqual(dict1.dump(), dict2.dump())

    def assertLogEquals(self, log, expected):
        for x in log.splitlines():
            self.assertRegexpMatches(x,
                u'\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}.\\d+ [^]]+\\] .*',
                u"Linia de log con formato no estandard"
            )
            
        logContent = ''.join(
                x.split('] ')[1]+'\n'
                for x in log.splitlines()
                if u'] ' in x
                )
        self.assertMultiLineEqual(logContent, expected)


    def test_changes_by_default_noChange(self):
        inv = InvestmentState()
        self.assertNsEqual(inv.changed(), """\
            {}
            """)


    



# vim: ts=4 sw=4 et
