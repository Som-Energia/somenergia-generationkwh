import datetime
import ftplib
import pytz

from . import (
    BaseProvider,
    BaseProviderConnectionError,
    BaseProviderDownloadError,
    BaseProviderSyntaxError,
    register,
    urlparse,
    )
from ..isodates import (
    daterange,
    toLocal,
    parseLocalTime as mtcParseLocalTime,
    addHours,
)

def parseLocalTime(string, isSummer):
    return mtcParseLocalTime(string, isSummer, format="%Y%m%d%H%M%S")


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
            measureTime = parseLocalTime(items[0], items[3]=='S')
            periodStart = addHours(measureTime, hours=-1)
            return {
                    'datetime': periodStart,
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

    def download(self, date):
        # TODO: Dynamic plant identifier
        filename = '1_{date.year}{date.month:02d}{date.day:02d}.csv'.format(**locals())
        client = None
        try:
            client = ftplib.FTP(self.res['hostname'])
            client.login(self.res['username'], self.res['password'])
        except Exception as e:
            raise BaseProviderConnectionError(e)

        try:
            from StringIO import StringIO
        except ImportError:
            from io import StringIO
        from contextlib import closing
        with closing(StringIO()) as sio:
            try:
                client.cwd(self.res['path'])
                client.retrbinary('RETR ' + filename, callback=sio.write)
            except Exception as e:
                raise BaseProviderDownloadError('Failed downloading %s' % filename)
            finally:
                client.quit()

            sio.seek(0)
            return sio.read().splitlines()

    def get(self, start, end):
        assert start is None or type(start)==datetime.date, (
            "start date should be a date but is {}".format(start))
        assert end is None or type(end)==datetime.date, (
            "start date should be a date but is {}".format(end))

        if not end:
            end = toLocal(datetime.datetime.now()).date()
        return [self.extract(self.download(date), date) for date in daterange(start, end)]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

register("monsol", MonsolProvider)


# vim: et ts=4 sw=4
