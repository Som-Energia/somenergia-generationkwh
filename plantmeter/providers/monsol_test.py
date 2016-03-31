import datetime
from ..providers import BaseProviderConnectionError, \
        BaseProviderDownloadError, BaseProviderSyntaxError
from .monsol import MonsolProvider , parseLocalTime

import unittest
from mock import patch

class MonsolProvide_Test(unittest.TestCase):
    def setUp(self):
        ""

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

    def profileFromDate(self, start, hours, profile_kWh, daylight):
        return [
            {
            'ae': profile_kWh[idx],
            'datetime': parseLocalTime(
                    start + str(hour).zfill(2) + '0000' , daylight[idx]=='S')
            } for idx, hour in enumerate(hours)]

    def test_failHostname(self):
        m = MonsolProvider('monsol://user:password@hostname/path')
        self.assertRaises(BaseProviderConnectionError, m.download, 'tes.csv')

    def test_failConnection(self):
        from socket import error
        m = MonsolProvider('monsol://user:password@www.somenergia.coop/path')
        self.assertRaises(BaseProviderConnectionError, m.download, 'tes.csv')

    @patch('ftplib.FTP', autospec=True)
    def test_download(self, ftp_constructor):
        mock_ftp = ftp_constructor.return_value
        m = MonsolProvider('monsol://user:password@hostname/path')
        m.download('test.csv')
    
        # TODO: Implement callback mockup
        mock_ftp.login.assert_called_once_with('user', 'password')
        mock_ftp.cwd.assert_called_once_with('path')
        self.assertEqual(mock_ftp.retrbinary.call_args[0], ('RETR test.csv',))

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

    def test_extractFileWinter(self):
        content = self.getContent('20_20160326.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        actual = m.extract(content, datetime.date(2016,3,26))
        expected = self.profileFromDate(
                '20160326',
                range(0,24),
                [0,0,0,0,0,0,0,0,0,7,14,21,29,24,26,26,28,23,16,6,0,0,0,0],
                ['W']*24)
        self.assertItemsEqual(actual, expected)

    def test_extractFileWinterToSummer(self):
        content = self.getContent('20_20160327.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        actual = m.extract(content, datetime.date(2016,3,27))
        expected = self.profileFromDate(
                '20160327',
                [0,1]+range(3,24),
                [0,0,0,0,0,0,0,0,9,15,20,27,29,31,31,30,26,11,8,0,0,0,0],
                ['W']*2+['S']*21)
        self.assertItemsEqual(actual, expected)

    def test_extractFileSummer(self):
        content = self.getContent('20_20160328.csv')
        m = MonsolProvider('monsol://user:password@hostname/path')
        actual = m.extract(content, datetime.date(2016,3,28))
        expected = self.profileFromDate(
                '20160328',
                range(0,24),
                [0,0,0,0,0,0,0,0,0,10,11,22,26,31,30,30,29,25,12,9,0,0,0,0],
                ['S']*24)
        self.assertItemsEqual(actual, expected)

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
