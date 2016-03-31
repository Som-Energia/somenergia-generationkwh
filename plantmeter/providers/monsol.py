import datetime
import ftplib
import pytz

from plantmeter.providers import BaseProvider, BaseProviderConnectionError, \
        BaseProviderDownloadError, BaseProviderSyntaxError, register, urlparse
from plantmeter.utils import daterange


tz = pytz.timezone('Europe/Madrid')
def parseLocalTime(string, isSummer=False):
    naive = datetime.datetime.strptime(string,
        "%Y%m%d%H%M%S")
    localized = tz.localize(naive)
    if not isSummer: return localized
    if localized.dst(): return localized
    onehour = datetime.timedelta(hours=1)
    lesser = tz.normalize(localized-onehour)
    return lesser if lesser.dst() else localized


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
        def valid(line):
            items = line.split(';')

            n_items = 4
            return (items[0].isdigit() and
                items[1].isdigit() and
                items[2].isdigit() and
                items[3] in ['S', 'W']) if (len(items)==n_items and '' not in items) else False

        def parse(line):
            if not valid(line):
                raise BaseProviderSyntaxError('Data not valid: %s' % line)

            items = line.split(';')
            return {
                    'datetime': parseLocalTime(items[0], items[3]=='S'),
                    'ae': int(items[1])
                    }

        if not end:
            end = start

        header_offset = 1
        return [measure
            for date in daterange(start, end + datetime.timedelta(days=1))
                for measure in (parse(line) for idx,line in enumerate(content) if idx>header_offset)
                    if measure['datetime'].date() == date
            ]

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
            return sio.read().splitlines()

    def get(self, start, end=None):
        return [self.extract(date, self.download(date)) for date in daterange(start, end)]

    def __enter__(self):
        return self

register("monsol", MonsolProvider)


# vim: et ts=4 sw=4
