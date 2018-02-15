"""
The ``enertrag_data`` module contains functions to read and dump measured
feed-in time series from a Enertrag wind farm.

The following data is available (year 2016) for the 17 turbines:
- meter (Zählerstand) in kW
- power output in kW
- wind speed in m/s  # TODO: korregiert???
- wind direction (gondel position) in °
ATTENTION: gondel position is not correct!!

Additionally the sum of the power output of all wind turbines is available in
column 'wf_9_power_output'.

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


def get_enertrag_data(pickle_load=False, filename='enertrag_dump.p',
                      resample=True, plot=False, x_limit=None, frequency='30T'):
    # TODO: add plots to check data
    r"""
    Fetches Enertrag data.

    pickle_load : Boolean
        If True data frame is loaded from the pickle dump if False the data is
        loaded from the original csv files (or from smaller csv file that was
        created in an earlier run if `csv_load` is True).
        Either set `pickle_load` or `csv_load` to True. Default: False.
    filename : String
        Filename including path of pickle dump. Default: 'pickle_dump.p'.
    resample : Boolean
        If True the data will be resampled to the `frequency`. (mean power)
    plot : Boolean
        If True each column of the data farme is plotted into a seperate
        figure. Default: False
    x_limit : list of floats or integers
        Values for xmin and xmax in case of `plot` being True and x limits
        wanted. Default: None.
    frequency : String (or freq object...?)
        # TODO add

    Returns
    -------
    enertrag_df : pandas.DataFrame
        Enertrag wind farm data.

    """
    if pickle_load:
        enertrag_df = pickle.load(open(filename, 'rb'))
    else:
        filename_files = os.path.join(os.path.dirname(__file__),
                                      'helper_files/filenames_enertrag.txt')
        enertrag_df = pd.DataFrame()
        with open(filename_files) as file:
            for line in file:
                name = line.strip()
                df_part = read_data(name)
                turbine_name = name.split('_')[1].split('.')[0]
                # Rename columns
                df_part.rename(columns={
                    'Zählerstand[kWh]': 'wf_9_{0}_meter'.format(turbine_name),
                    'Windgeschwindigkeit[m/s]': 'wf_9_{0}_wind_speed'.format(
                        turbine_name),
                    'Leistung[kW]': 'wf_9_{0}_power_output'.format(
                        turbine_name),
                    'Gondelposition': 'wf_9_{0}_wind_dir'.format(
                        turbine_name)},
                               inplace=True)
                # Add to DataFrame
                enertrag_df = pd.concat([enertrag_df, df_part], axis=1)
            # Convert index to DatetimeIndex and make time zone aware
            enertrag_df.index = pd.to_datetime(enertrag_df.index).tz_localize(
                'UTC').tz_convert('Europe/Berlin')
            if resample:
                enertrag_df = enertrag_df.resample(frequency).mean()
            # Add frequency attribute
            freq = pd.infer_freq(enertrag_df.index)
            enertrag_df.index.freq = pd.tseries.frequencies.to_offset(freq)
            # Get wind farm power output
            enertrag_df['wf_9_power_output'] = enertrag_df.loc[:,
                                               [column for column in
                                                list(enertrag_df) if
                                                'power_output' in column]].sum(
                skipna=True, axis=1)
            pickle.dump(enertrag_df, open(filename, 'wb'))
    return enertrag_df

if __name__ == "__main__":
    # Decide whether to resample to a certain frequency
    resample = True
    frequency = '30T'
    filename = os.path.join(os.path.dirname(__file__), 'dumps/validation_data',
                            'enertrag_data_2016.p') # Filename for pickle dump
    df = get_enertrag_data(resample=resample, filename=filename)

