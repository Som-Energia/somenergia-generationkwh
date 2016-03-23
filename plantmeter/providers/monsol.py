import datetime
import ftplib
from plantmeter.providers import BaseProvider, BaseProviderConnectionError, \
        BaseProviderDownloadError, register, urlparse
from plantmeter.utils import daterange

import unittest
from mock import patch

class MonsolProvider(BaseProvider):
    """Monsol Provider
    """

    def __init__(self, uri=None):
        if uri is None:
            uri = "monsol://path"
        super(MonsolProvider, self).__init__(uri)
        self.uri = uri
        self.res = urlparse(self.uri) 

    def extract(self, content, start, end=None):
        def parse(line):
            items = line.split(';')
            return {
                    'datetime': datetime.datetime.strptime(items[0], '%Y-%m-%d %H:%M'),
                    'daylight': items[1],
                    'ae': int(items[3])
                    }

        if not end:
            end = start
        return [[measure
            for date in daterange(start, end + datetime.timedelta(days=1))
                for measure in (parse(line) for line in content)
                    if measure['datetime'].date() == date
            ]]

    def download(self, filename):
        client = None
        try:
            client = ftplib.FTP(self.res['hostname'])
            client.login(self.res['username'], self.res['password'])
        except Exception as e:
            raise BaseProviderConnectionError(e)

        import StringIO
        from contextlib import closing
        with closing(StringIO.StringIO()) as sio:
            try:
                client.cwd(self.res['path'])
                client.retrbinary('RETR ' + filename, callback=sio.write)
            except Exception as e:
                raise BaseProviderDownloadError()
            finally:
                client.quit()

            sio.seek(0)
            return sio.readlines()

    def get(self, start, end=None):
        return [self.extract(date, self.download(date)) for date in daterange(start, end)]

    def __enter__(self):
        return self

register("monsol", MonsolProvider)


class MonsolProvide_Test(unittest.TestCase):
    def setUp(self):
        ""

    def tearDown(self):
        ""

    def load_file(self, path):
        with open(path, 'r') as f:
            output = f.readlines()
        return output

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

    def test_extract(self):
        import os
        m = MonsolProvider('monsol://user:password@hostname/path')
        path = os.path.dirname(os.path.realpath(__file__)) + '/../data/monsol_20150904.csv'
        content = self.load_file(path)
        measurements = m.extract(content, datetime.date(2015,9,4))
        self.assertDictEqual(
                measurements[0][0],
                {
                    'daylight': 'S', 
                    'ae': 0, 
                    'datetime': datetime.datetime(2015, 9, 4, 0, 0)
                    })
        self.assertDictEqual(
                measurements[0][-1],
                {
                    'daylight': 'S',
                    'ae': 0,
                    'datetime': datetime.datetime(2015, 9, 4, 23, 0)
                    })

    @unittest.skip("tobe implemented!")
    def test_get(self):
        ""

# vim: et ts=4 sw=4
