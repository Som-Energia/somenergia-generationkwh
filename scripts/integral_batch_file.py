#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from scipy import integrate
import pandas as pd
from datetime import datetime
import chardet

def show_usage():
    print("usage: column2Integrate input_data_file output_data_file decimal\n\
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

def parse_csv(input_data_file, column2Integrate, decimal):

    guessed_encoding = find_encoding(input_data_file)

    forcedTypesDict = {column2Integrate: float}
    columnsTypesDict = forcedTypesDict

    columnNames = pd.read_csv(input_data_file, nrows=0, delimiter=';', encoding=guessed_encoding).columns

    if column2Integrate not in columnNames:
        print('Column \'{}\' not in columnNames. Columns are {}.'.format(column2Integrate, columnNames))
        sys.exit(-1)

    columnsTypesDict.update({col: str for col in columnNames if col not in forcedTypesDict})

    sensors = pd.read_csv(input_data_file, encoding=guessed_encoding, dtype=columnsTypesDict, decimal=decimal)

    sensors['date_'] = sensors['DATE'] + sensors[' TIME']
    sensors['date_'] = pd.to_datetime(sensors['date_'], format='%d/%m/%Y %H:%M')

    ordered_sensors = sensors.set_index('date_')

    return ordered_sensors

def parse_xlsx(input_data_file, column2Integrate):

    forcedTypesDict = {column2Integrate: float}
    columnsTypesDict = forcedTypesDict

    columnNames = pd.read_excel(io=input_data_file, header=0).columns

    if column2Integrate not in columnNames:
        print('Column \'{}\' not in columnNames. Columns are {}.'.format(column2Integrate, columnNames))
        sys.exit(-1)

    columnsTypesDict.update({col: str for col in columnNames if col not in forcedTypesDict})

    ordered_sensors = pd.read_excel(input_data_file, index_col=0, parse_dates=True, convert_float=False, dtype=columnsTypesDict)

    '''todo standarize both csv and excel'''
    ordered_sensors.rename(columns={'TIME':'DATE'})

    return ordered_sensors

def main():

    if len(sys.argv[1:]) != 4:
        print('Expecting 4 arguments, got {}'.format(len(sys.argv[1:])))
        show_usage()
        sys.exit(-1)

    '''TODO: use config file'''
    outputDataFormat = '%d/%m/%Y %H:%M:%S'

    '''TODO: sanitize'''
    column2Integrate = sys.argv[1]
    input_data_file = sys.argv[2]
    output_data_file = sys.argv[3]
    decimal = sys.argv[4]
    # decimal=',' # European decimal point

    '''TODO: utf sandwich instead of keeping guessed_encoding'''

    if input_data_file.endswith('csv'):

        ordered_sensors = parse_csv(input_data_file, column2Integrate=column2Integrate, decimal=decimal)

    elif input_data_file.endswith('xls') or input_data_file.endswith('xlsx'):

        ordered_sensors = parse_xlsx(input_data_file, column2Integrate=column2Integrate)

    else:
        print("Only .csv, .xls and .xlsx are supported")
        sys.exit(-2)

    ''' Time in hours between readings '''
    timeSpacing = 5./60.

    from_date = ordered_sensors.index[0].floor('d')
    to_date   = ordered_sensors.index[-1].ceil('d')

    integrals = trapezoidal_approximation(ordered_sensors, from_date, to_date, outputDataFormat, timeSpacing, column2Integrate)

    integralsDF = pd.DataFrame(data = integrals, columns = ['datetime', column2Integrate])
    integralsDF.to_csv(output_data_file, sep=';', encoding='utf-8', index=False)

    print("Saved {} records from {} to {}".format(len(integralsDF), from_date, to_date))
    print("Job's done, have a good day")
    asciigraph_print(integrals)

if __name__ == "__main__":
	main()
