import pandas as pd
import os
import pickle
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
        Path where the data file is stored. Default: './data'
    usecols : list of strings or list of integers, optional
        .... Default: None

    Returns
    -------
    pandas.DataFrame

    """
    if 'datapath' not in kwargs:
        kwargs['datapath'] = os.path.join(os.path.dirname(__file__),
                                          'data')
    if 'usecols' not in kwargs:
        kwargs['usecols'] = None

    df = pd.read_csv(os.path.join(kwargs['datapath'], filename), sep=';',
                     decimal=',', index_col=0, usecols=kwargs['usecols'])
    return df


def restructure_data(filename, filter_cols=None, drop_na=False):
    df = read_data(filename)
    if filter_cols:
        df2 = df.filter(items=filter_cols, axis=1)
    if drop_na:
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


def data_evaluation(filename):
    """
    Evaluate the data in terms of which variables are given for each dataset.

    Parameters:
    -----------
    filename : string
        Name of file that contains names of files to be evaluated.
    """
    # Initialise pandas.DataFrame
    df_compare = pd.DataFrame()
    # Read file and add to DataFrame for each line (= filenames)
    with open(filename) as file:
            for line in file:
                name = line.strip()
                df = restructure_data(name)
                df2 = pd.DataFrame(data=1, index=list(df),
                                   columns=[name])
                df_compare = pd.concat([df_compare, df2], axis=1)
    df_compare.to_csv('evaluation.csv')
    return df_compare


def get_data(filename_files, filename_column_names, new_column_names,
             filename_pickle='pickle_dump.p', pickle_load=True):
    if not pickle_load:
#        usecols = [0]
#        with open(filename_column_names) as file:
#            for line in file:
#                line = line.strip()
#                usecols.append(line)
        filter_cols = []
        with open(filename_column_names) as file:
            for line in file:
                line = line.strip()
                filter_cols.append(line)
        with open(filename_files) as file:
            data = pd.DataFrame()
            for line in file:
                name = line.strip()
#                df = read_data(name, usecols=usecols)
                df = restructure_data(name, filter_cols)
                df.columns = new_column_names
                data = pd.concat([data, df])  # data could also be dictionary
        pickle.dump(data, open(filename_pickle, 'wb'))
    if pickle_load:
        data = pickle.load(open(filename_pickle, 'rb'))
    return data

#check_column_names('filenames_2015.txt')
#df_compare = data_evaluation('filenames_all.txt')

new_column_names_2016_2017 = [
    'Bredstedt_P_W', 'Bredstedt_P_W_theo', 'Bredstedt_v_wind',
    'Bredstedt_wind_dir', 'Bredstedt_P_W_inst', 'Goeser_P_W',
    'Goeser_P_W_theo', 'Goeser_v_wind', 'Goeser_wind_dir', 'Goeser_P_W_inst',
    'PPC_4919_P_W', 'PPC_4919_P_W_theo', 'PPC_4919_v_wind',
    'PPC_4919_wind_dir', 'PPC_4919_P_W_inst', 'PPC_4950_P_W',
    'PPC_4950_P_W_theo', 'PPC_4950_v_wind', 'PPC_4950_wind_dir',
    'PPC_4950_P_W_inst', 'PPC_5598_P_W', 'PPC_5598_P_W_theo',
    'PPC_5598_v_wind', 'PPC_5598_wind_dir', 'PPC_5598_P_W_inst']

new_column_names_2015 = [
    'Bredstedt_P_W', 'Bredstedt_P_W_theo', 'Bredstedt_v_wind',
    'Bredstedt_wind_dir', 'Bredstedt_P_W_inst',
    'Nordstrand_P_W', 'Nordstrand_P_W_inst', 'Nordstrand_P_W_inst',
    'PPC_4919_P_W', 'PPC_4919_P_W_theo', 'PPC_4950_P_W',
    'PPC_4950_P_W_theo', 'PPC_4950_v_wind', 'PPC_5598_P_W',
    'PPC_5598_P_W_inst', 'PPC_5598_P_W_theo']

#data = get_data('filenames_2015.txt', 'column_names_2015.txt',
#                new_column_names_2015, 'data_2015.p', pickle_load=False)


data = get_data('filenames_2016_2017.txt', 'column_names_2016_2017.txt',
                new_column_names_2016_2017, 'data_2016_2017.p',
                pickle_load=False)
data.to_csv('ergebnis.csv')
#get_data(new_names, 'filenames_2015.txt')

#df.to_csv('out_1.csv', sep='\t')
#df2.to_csv('out.csv', sep='\t')

#
#print(list(df2))
