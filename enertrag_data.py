"""
The ``enertrag_data`` module contains functions to read and dump measured
feed-in time series from a Enertrag wind farm.

The following data is available (year 2016):
- 
TODO: adjust this information

"""

# Imports from lib_validation
import visualization_tools
import analysis_tools
import tools

# Other imports
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import os
import pickle


def read_data(filename, **kwargs):
    r"""
    Fetches data from a csv file.

    Parameters
    ----------
    filename : string
        Name of data file.

    Other Parameters
    ----------------
    datapath : string, optional
        Path where the data file is stored. Default: './data'
    usecols : list of strings or list of integers, optional
        TODO: add explanation Default: None

    Returns
    -------
    pandas.DataFrame

    """
    df = pd.read_csv(os.path.join(os.path.dirname(__file__),
                                  'data/Enertrag', filename),
                     sep=',', decimal='.', index_col=0)
    return df


def get_enertrag_data(pickle_load=False, filename='pickle_dump.p',
                      plot=False, x_limit=None):
    r"""
    Fetches Enertrag data.

    pickle_load : Boolean
        If True data frame is loaded from the pickle dump if False the data is
        loaded from the original csv files (or from smaller csv file that was
        created in an earlier run if `csv_load` is True).
        Either set `pickle_load` or `csv_load` to True. Default: False.
    filename : String
        Filename including path of pickle dump. Default: 'pickle_dump.p'.
    plot : Boolean
        If True each column of the data farme is plotted into a seperate
        figure. Default: False
    x_limit : list of floats or integers
        Values for xmin and xmax in case of `plot` being True and x limits
        wanted. Default: None.

    Returns
    -------
    enertrag_df : pandas.DataFrame
        Enertrag wind farm data.

    """
    if pickle_load:
        df = pickle.load(open(filename, 'rb'))
    else:
        filename_files = os.path.join(os.path.dirname(__file__),
                                      'helper_files/filenames_enertrag.txt')
        new_column_names = ['']
        df = pd.DataFrame()
        with open(filename_files) as file:
            df = pd.DataFrame()
            for line in file:
                name = line.strip()
                df_part = read_data(name)
                df_part.columns = new_column_names
                df = pd.concat([df, df_part])
#        df.index = indices
                
    return

if __name__ == "__main__":
    df = get_enertrag_data()
