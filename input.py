import pandas as pd
import os
#import numpy as np


def read_data(filename, **kwargs):
    r"""
    Fetches power time series from a file.

    Parameters
    ----------
    filename : string, optional
        Name of data file. Provided data files are 'power_curves.csv' and
        'power_coefficient_curves.csv'. Default: 'power_curves.csv'.

    Other Parameters
    ----------------
    datapath : string, optional
        Path where the data file is stored. Default: './data/ArgeNetz'
    usecols : list of strings or list of integers, optional
        .... Default: None

    Returns
    -------
    pandas.DataFrame

    """
    if 'datapath' not in kwargs:
        kwargs['datapath'] = os.path.join(os.path.dirname(__file__),
                                          'data/ArgeNetz')
    if 'usecols' not in kwargs:
        kwargs['usecols'] = None

    df = pd.read_csv(os.path.join(kwargs['datapath'], filename), sep=';',
                     decimal=',', index_col=0, usecols=kwargs['usecols'])
    return df


def restructure_data(filename):
    df = read_data(filename)
    df2 = df.dropna(axis='columns', how='all')
    return df2


def check_column_names(filename):
    column_names_check = list(restructure_data('2016-02-01+00P1M_.csv'))
    with open(filename) as file:
        for line in file:
            name = line.strip()
            df = restructure_data(name)
            column_names = list(df)
            if column_names != column_names_check:
                print(str(name) + ' columns:')
#                print(column_names)


#check_column_names('filenames.txt')

# TODO: check column names, if same: new column names to columns, 
# TODO: add filenames from 2017 and 2015 (sublimetext!!!)

#df.to_csv('out_1.csv', sep='\t')
#df2.to_csv('out.csv', sep='\t')

#
#print(list(df2))
