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

    Returns
    -------
    pandas.DataFrame

    """
    if 'datapath' not in kwargs:
        kwargs['datapath'] = os.path.join(os.path.dirname(__file__),
                                          'data/ArgeNetz')

    df = pd.read_csv(os.path.join(kwargs['datapath'], filename), sep=';',
                     decimal=',', index_col=0)
    return df


def restructure_data(filename):
    df = read_data(filename)
    df2 = df.dropna(axis='columns', how='all')
    return df2


def check_column_names(filename):
    # Extract all filenames from txt file
    filenames = pd.read_csv(filename)
    print(filenames)
    column_names_check = list(restructure_data('2016-02-01+00P1M_.csv'))

    for name in filenames:
        df = read_data(name)
        df2 = df.dropna(axis='columns', how='all')
        column_names = list(df2)
        if column_names is not column_names_check:
            print(str(name) + ' columns:')
            print(list(df2))

check_column_names('filenames.txt')

# TODO: check column names, if same: new column names to columns, 
# TODO: add filenames from 2017 and 2015 (sublimetext!!!)

#df.to_csv('out_1.csv', sep='\t')
#df2.to_csv('out.csv', sep='\t')

#
#print(list(df2))
