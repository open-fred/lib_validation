import pandas as pd
import os
import pickle
from matplotlib import pyplot as plt
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
                     decimal=',', thousands='.', index_col=0,
                     usecols=kwargs['usecols'])
    return df


def restructure_data(filename, filter_cols=None, drop_na=False):
    df = read_data(filename)
    if filter_cols:
        df2 = df.filter(items=filter_cols, axis=1)
    if drop_na:
        df2 = df.dropna(axis='columns', how='all')
    return df2


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
        filter_cols = []
        with open(filename_column_names) as file:
            for line in file:
                line = line.strip()
                filter_cols.append(line)
        with open(filename_files) as file:
            data = pd.DataFrame()
            for line in file:
                name = line.strip()
                df = restructure_data(name, filter_cols)
                df.columns = new_column_names
                data = pd.concat([data, df])  # data could also be dictionary
        pickle.dump(data, open(filename_pickle, 'wb'))
    if pickle_load:
        data = pickle.load(open(filename_pickle, 'rb'))
    return data


def fast_plot(df, save_folder, y_limit=None, x_limit=None):
    for column in df.columns:
        fig = plt.figure(figsize=(16, 12))
        df[column].plot()
        plt.title(column, fontsize=20)
        plt.xticks(rotation='vertical')
        if y_limit:
            plt.ylim(ymin=x_limit[0], ymax=y_limit[1])
        if x_limit:
            plt.xlim(xmin=x_limit[0], xmax=x_limit[1])
        plt.tight_layout()
        fig.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 '..', save_folder,
                                                 str(save_folder+column))))

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
    'Nordstrand_P_W', 'Nordstrand_P_W_theo', 'Nordstrand_P_W_inst',
    'PPC_4919_P_W', 'PPC_4919_P_W_theo', 'PPC_4950_P_W',
    'PPC_4950_P_W_theo', 'PPC_4950_v_wind', 'PPC_5598_P_W',
    'PPC_5598_P_W_inst', 'PPC_5598_P_W_theo']

# Get the data of 2015 (and 2016/2017) and plot the results
x_limit = None
data_2015 = get_data('filenames_2015.txt', 'column_names_2015.txt',
                     new_column_names_2015, 'data_2015.p', pickle_load=False)
fast_plot(data_2015, save_folder='Plots_2015', x_limit=x_limit)
#data_2016_2017 = get_data('filenames_2016_2017.txt',
#                          'column_names_2016_2017.txt',
#                          new_column_names_2016_2017, 'data_2016_2017.p',
#                          pickle_load=True)
#fast_plot(data_2016_2017, save_folder='Plots_2016_2017', x_limit=x_limit)

# Sample for period of 2015 (possible mistakes in data)
#data = get_data('filenames.txt', 'column_names_2015.txt',
#                 new_column_names_2015, 'data_2015.p', pickle_load=False)
#x_limit = [10, 50]
#fast_plot(data, save_folder='Plots_2015_period', x_limit=x_limit)
