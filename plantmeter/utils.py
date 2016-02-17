from datetime import timedelta, date

def daterange(start_date, end_date):
    if not end_date:
        end_date = start_date + timedelta(1)
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)
