#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from scipy import integrate
import pandas as pd
from datetime import datetime
import chardet

def show_usage():
    print("usage: column2Integrate input_csv_file output_csv_file decimal\n\
    e.g. python ./integral_batch_file.py \' Irradiation\' dades_in.csv dades_out.csv ','")

def trapezoidal_approximation(ordered_sensors, from_date, to_date, outputDataFormat='%d/%m/%Y %H:%M:%S', timeSpacing=5./60., column2Integrate=' Irradiation'):
    ''' Trapezoidal aproximation of the 24 hours following first sensor entry'''

    '''Get the first date entry and create hourly time entries'''
    ts_start = pd.Series(pd.date_range(start=from_date, end=to_date, freq='H'))

    deltaT = pd.Timedelta(hours=1)
    timeStrings = ts_start.dt.strftime(outputDataFormat)
    integrals = []
    for start, timeString in zip(ts_start, timeStrings):
        end = start + deltaT
        interval4integral = ordered_sensors.loc[start:end]

        ''' Trapezoidal aproximation of the hour following first sensor entry '''
        test_integral = integrate.trapz(y = interval4integral[column2Integrate], dx = timeSpacing)

        integrals.append((timeString, test_integral))
    return integrals

def asciigraph_print(tuple_array, scale_factor = 10):
    '''for the lulz'''

    for t, v in tuple_array:
        print("{} {} {:.2f}".format(t, '=' * int(v/scale_factor), v))

def find_encoding(fname):
    with open(fname, 'rb') as f:
        r_file = f.read()
        result = chardet.detect(r_file)
    charenc = result['encoding']
    return charenc

def main():

    if len(sys.argv[1:]) != 4:
        print('Expecting 4 arguments, got {}'.format(len(sys.argv[1:])))
        show_usage()
        sys.exit(-1)

    '''TODO: use config file'''
    outputDataFormat = '%d/%m/%Y %H:%M:%S'

    '''TODO: sanitize'''
    column2Integrate = sys.argv[1]
    input_csv_file = sys.argv[2]
    output_csv_file = sys.argv[3]
    decimal = sys.argv[4]
    # decimal=',' # European decimal point

    guessed_encoding = find_encoding(input_csv_file)

    columnNames = pd.read_csv(input_csv_file, nrows=0, delimiter=';', encoding=guessed_encoding).columns
    forcedTypesDict = {column2Integrate: float}

    if column2Integrate not in columnNames:
        print('Column \'{}\' not in columnNames. Columns are {}.'.format(column2Integrate, columnNames))
        sys.exit(-1)

    columnsTypesDict = forcedTypesDict
    columnsTypesDict.update({col: str for col in columnNames if col not in forcedTypesDict})

    '''TODO: utf sandwich instead of keeping guessed_encoding'''

    sensors = pd.read_csv(input_csv_file, delimiter=';', encoding=guessed_encoding, dtype=columnsTypesDict, decimal=decimal)

    sensors['date_'] = sensors['DATE'] + sensors[' TIME']
    sensors['date_'] = pd.to_datetime(sensors['date_'], format='%d/%m/%Y %H:%M')

    ordered_sensors = sensors.set_index('date_')

    ''' Time in hours between readings '''
    timeSpacing = 5./60.

    from_date = pd.to_datetime(ordered_sensors['DATE'][0], format='%d/%m/%Y')
    to_date = pd.to_datetime(ordered_sensors['DATE'][-1], format='%d/%m/%Y')

    integrals = trapezoidal_approximation(ordered_sensors, from_date, to_date, outputDataFormat, timeSpacing, column2Integrate)

    integralsDF = pd.DataFrame(data = integrals, columns = ['datetime', column2Integrate])
    integralsDF.to_csv(output_csv_file, sep=';', encoding='utf-8', index=False)

    print("Saved {} records from {} to {}".format(len(integralsDF), from_date, to_date))
    print("Job's done, have a good day")
    asciigraph_print(integrals)

if __name__ == "__main__":
	main()
