from plantmeter.providers import BaseProvider, register, urlparse
from plantmeter.utils import daterange
import datetime
import xlrd

class TFMProvider(BaseProvider):
    """TFM Provider 
    """
    date_fmt = '&dia={date.day:02d}&mes={date.month:02d}&any={date.year:04d}'
    sheet_names = [u'Dades Instantaneas', u'Corba de carrega', u'Sondes', u'Dades Resumides']
    var_names = [u'Temps', u'Generaci\xf3', u'Temp. Modul', u'Temp. Ambient']
 
    def __init__(self, uri=None):
        if uri is None:
            uri = 'tfm://user:password@localhost:port/path'
        super(TFMProvider, self).__init__(uri)
        self.uri = uri
        self.res = urlparse(self.uri)

    def download(self, date):
        import requests
        return requests.get('http://' + self.res['hostname'] + '/' + self.res['path'] + 
            self.date_fmt.format(**locals())).content

    def extract(self, date, content):
        import xlrd
        sheets = [u'Dades Instantaneas', u'Corba de carrega', u'Sondes', u'Dades Resumides']
        book = xlrd.open_workbook(file_contents=content)
        if book.nsheets != 4 or set(book.sheet_names()) != set(self.sheet_names): 
            raise Exception('Failed parsing data')
       
        sheet = book.sheet_by_name('Dades Resumides')
        var_names = [cell.value for cell in sheet.row(0)]
        if sheet.ncols != 4 or sheet.nrows != 25 or set(var_names) != set(self.var_names): 
            raise Exception('Corruputed data')
        return [{'datetime': datetime.datetime.combine(date,datetime.time.min)+datetime.timedelta(hours=3),
                 'ae': sheet.row(idx)[1].value} 
                     for idx in range(1,25)] 

    def get(self, start, end=None):
        return [self.extract(date, self.download(date)) for date in daterange(start, end)]

    def disconnect(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

register("tfm", TFMProvider)
