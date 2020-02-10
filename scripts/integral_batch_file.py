#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from scipy import integrate
import pandas as pd
from datetime import datetime

def show_usage():
    print('Usage: python integral_batch_file.py <input_csv_file> <output_csv_file>')

def trapezoidal_approximation(ordered_sensors, day, outputDataFormat='%d/%m/%Y %H:%M:%S', timeSpacing=5./60.):
    ''' Trapezoidal aproximation of the 24 hours following first sensor entry'''

    '''Get the first date entry and create hourly time entries'''
    ts_start = pd.Series(pd.date_range(start=day, periods=24, freq='H'))

    deltaT = pd.Timedelta(hours=1)
    timeStrings = ts_start.dt.strftime(outputDataFormat)

    integrals = []
    for start, timeString in zip(ts_start, timeStrings):
        end = start + deltaT
        interval4integral = ordered_sensors.loc[start:end]

        ''' Trapezoidal aproximation of the hour following first sensor entry '''
        test_integral = integrate.trapz(y = interval4integral[' Irradiation'], dx = timeSpacing)

        integrals.append((timeString, test_integral))

    return integrals

def asciigraph_print(tuple_array, scale_factor = 10):
    '''for the lulz'''

    for t, v in tuple_array:
        print("{} {}".format(t, '=' * int(v/scale_factor)))

def plot_dataframe(dataFrame, output_png = 'graph.png'):
    ''' WIP plotting the irradiation daily graph'''

    dataFrame.plot()
    # import matplotlib as plt
    #
    # plt.plot(tuple_array)
    # plt.savefig(output_png)
    # plt.show()

def main():

    if len(sys.argv[1:]) != 2:
        print('Expecting 2 arguments, got {}'.format(len(sys.argv[1:])))
        show_usage()
        sys.exit(-1)

    '''TODO: use config file'''
    outputDataFormat = '%d/%m/%Y %H:%M:%S'

    '''TODO: sanitize'''
    input_csv_file = sys.argv[1]
    output_csv_file = sys.argv[2]


    sensors = pd.read_csv(input_csv_file, delimiter=';', encoding='utf-8')
    sensors['date_'] = sensors['DATE'] + sensors[' TIME']
    sensors['date_'] = pd.to_datetime(sensors['date_'])

    ordered_sensors = sensors.set_index('date_')

    ''' Time in hours between readings '''
    timeSpacing = 5./60.

    dayToProcess = ordered_sensors['DATE'][0]

    integrals = trapezoidal_approximation(ordered_sensors, dayToProcess, outputDataFormat, timeSpacing)

    integralsDF = pd.DataFrame(data = integrals, columns = ['datetime', 'Irradiation'])
    integralsDF.to_csv(output_csv_file, sep=';', encoding='utf-8', index=False)

    #print('\n'.join('{}: {}'.format(*k) for k in integrals))

    #asciigraph_print(integrals, 10)

    plot_dataframe(integralsDF)

    print("Saved {} records".format(len(integralsDF)))
    print("Job's done, have a good day")

if __name__ == "__main__":
	main()
