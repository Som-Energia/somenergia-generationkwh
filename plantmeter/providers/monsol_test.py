import datetime
from .monsol import (
    MonsolProvider,
    parseLocalTime,
    BaseProviderConnectionError,
    BaseProviderDownloadError,
    BaseProviderSyntaxError,
    )
from ..isodates import isodate

import unittest
from mock import patch

class MonsolProvide_Test(unittest.TestCase):
    def setUp(self):
        ""
        self.maxDiff = None

    def tearDown(self):
        ""

    def load_file(self, path):
        with open(path, 'r') as f:
            output = f.read().splitlines()
        return output

    def getContent(self, filename):
        import os
        path = os.path.dirname(os.path.realpath(__file__)) + '/../data/monsol/' + filename
        return self.load_file(path)

    def profileFromDate(self, start, hours, profile_kwh, daylight):
        return [
            {
            'ae': profile_kwh[idx],
            'datetime': parseLocalTime(
                    start + str(hour).zfill(2) + '0000' , daylight[idx]=='S')
            } for idx, hour in enumerate(hours)]

    def test_failHostname(self):
        m = MonsolProvider('monsol://user:password@hostname/path')
        self.assertRaises(BaseProviderConnectionError, m.download, isodate('2015-08-01'))

    def test_failConnection(self):
        from socket import error
        m = MonsolProvider('monsol://user:password@www.somenergia.coop/path')
        self.assertRaises(BaseProviderConnectionError, m.download, isodate('2015-08-01'))

    @patch('ftplib.FTP', autospec=True)
    def test_download(self, ftp_constructor):
        mock_ftp = ftp_constructor.return_value
        m = MonsolProvider('monsol://user:password@hostname/path')
        m.download(isodate('2015-08-01'))
    
        # TODO: Implement callback mockup
        mock_ftp.login.assert_called_once_with('user', 'password')
        mock_ftp.cwd.assert_called_once_with('path')
        self.assertEqual(mock_ftp.retrbinary.call_args[0], ('RETR 1_20150801.csv',))

    def test_extractEmptyFile(self):
        content = self.getContent('20_20160327_empty.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        measurements = m.extract(content, datetime.date(2015,9,4))
        self.assertEqual(measurements, [])

    def test_extractOnlyHeaderFile(self):
        content = self.getContent('20_20160327_header.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        measurements = m.extract(content, datetime.date(2015,9,4))
        self.assertEqual(measurements, [])

    from ..testutils import assertNsEqual

    def assertProfileEqual(self, result, expected):
        from yamlns import namespace as ns
        self.assertNsEqual(
            ns(data=[ns(a) for a in sorted(result,key=lambda x:x['datetime'])]).dump(),
            ns(data=[ns(a) for a in sorted(expected,key=lambda x:x['datetime'])]).dump(),
            )

    def test_extractFileWinter(self):
        content = self.getContent('20_20160326.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        actual = m.extract(content, datetime.date(2016,3,26))
        expected = self.profileFromDate(
                '20160326',
                list(range(0,24)),
                [0,0,0,0,0,0,0,0,7,14,21,29,24,26,26,28,23,16,6,0,0,0,0,0],
                ['W']*24)
        self.assertProfileEqual(actual, expected)

    def test_extractFileWinterToSummer(self):
        content = self.getContent('20_20160327.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        actual = m.extract(content, datetime.date(2016,3,27))
        expected = self.profileFromDate(
                '20160327',
                [0,1]+list(range(3,24)),
                [0,1,2,3,4,5,6,9,15,20,27,29,31,31,30,26,11,8,0,0,0,0,0],
                ['W']+['S']*22)
        self.assertProfileEqual(actual, expected)

    def test_extractFileSummerToWinter(self):
        content = self.getContent('20_20161030.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        actual = m.extract(content, datetime.date(2016,10,30))
        expected = self.profileFromDate(
                '20161030',
                [0,1,2,2]+list(range(3,24)),
                range(1,26),
                ['S']*3+['W']*22)
        self.assertProfileEqual(actual, expected)

    def test_extractFileSummer(self):
        content = self.getContent('20_20160328.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        actual = m.extract(content, datetime.date(2016,3,28))
        expected = self.profileFromDate(
                '20160328',
                range(0,24),
                [0,0,0,0,0,0,0,0,10,11,22,26,31,30,30,29,25,12,9,0,0,0,0,0],
                ['S']*24)
        self.assertProfileEqual(actual, expected)

    def test_wronglinesize(self):
        content = self.getContent('20_20160328_wrongLineSize.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        with self.assertRaises(BaseProviderSyntaxError):
            m.extract(content, datetime.date(2016,3,28))

    def test_wrongMissingDatetime(self):
        content = self.getContent('20_20160328_missingDate.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        with self.assertRaises(BaseProviderSyntaxError):
            m.extract(content, datetime.date(2016,3,28))

    def test_missingExportedEnergy(self):
        content = self.getContent('20_20160328_missingExportedEnergy.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        with self.assertRaises(BaseProviderSyntaxError):
            m.extract(content, datetime.date(2016,3,28))

    def test_missingImportedEnergy(self):
        content = self.getContent('20_20160328_missingImportedEnergy.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        with self.assertRaises(BaseProviderSyntaxError):
            m.extract(content, datetime.date(2016,3,28))

    def test_missingFormatDaylight(self):
        content = self.getContent('20_20160328_missingImportedEnergy.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        with self.assertRaises(BaseProviderSyntaxError):
            m.extract(content, datetime.date(2016,3,28))


# vim: et ts=4 sw=4
