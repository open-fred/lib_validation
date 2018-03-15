"""
The ``greenwind_data`` module contains functions to read and dump measured
feed-in time series from a GreenWind wind farm.

# The following data is available (year 2016) for the 17 turbines:
# - meter (Zählerstand) in kW
# - power output in kW
# - wind speed in m/s
# - wind direction (gondel position) in °
# ATTENTION: gondel position is not correct!!
#
# Additionally the sum of the power output of all wind turbines is available in
# column 'wf_9_power_output'.

DateTimeIndex in 'Europe/Berlin' time zone.
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


def read_data(filename):
    r"""
    Fetches data from a csv file.

    Parameters
    ----------
    filename : string
        Name of data file.

    Returns
    -------
    pandas.DataFrame

    """
    df = pd.read_csv(os.path.join(os.path.dirname(__file__),
                                  'data/GreenWind', filename),
                     sep=',', decimal='.', index_col=0)
    return df


def get_greenwind_data(year, pickle_load=False, filename='greenwind_dump.p',
                       resample=True, plot=False, x_limit=None,
                       frequency='30T', pickle_dump=True, filter_errors=True,
                       print_error_amount=False):
    # TODO: add plots to check data
    r"""
    Fetches GreenWind data.

    Parameters
    ----------
    year : Integer
        Year to fetch.
    pickle_load : Boolean
        If True data frame is loaded from the pickle dump if False the data is
        loaded from the original csv files (or from smaller csv file that was
        created in an earlier run if `csv_load` is True).
        Either set `pickle_load` or `csv_load` to True. Default: False.
    filename : String
        Filename including path of pickle dump. Default: 'greenwind_dump.p'.
    resample : Boolean
        If True the data will be resampled to the `frequency`. (mean power)
        Default: True.
    plot : Boolean
        If True each column of the data farme is plotted into a seperate
        figure. Default: False
    x_limit : list of floats or integers
        Values for xmin and xmax in case of `plot` being True and x limits
        wanted. Default: None.
    frequency : String (or freq object...?)
        # TODO add
    pickle_dump : Boolean
        If True the data frame is dumped to `filename`. Default: True.
    filter_errors : Booelan
        If True errors are filtered via the error code column. Default: True.

    Returns
    -------
    greendwind_df : pandas.DataFrame
        GreenWind wind farm data.

    """
    if pickle_load:
        greenwind_df = pickle.load(open(filename, 'rb'))
    else:
        filenames = [
            # 'WF1_{0}.csv'.format(year),
            'WF2_{0}.csv'.format(year),
            'WF3_{0}.csv'.format(year)]
        greenwind_df = pd.DataFrame()
        for name in filenames:
            df_part = read_data(name).drop_duplicates()
            # Add to DataFrame
            greenwind_df = pd.concat([greenwind_df, df_part], axis=1)
        # Convert index to DatetimeIndex and make time zone aware
        greenwind_df.index = pd.to_datetime(greenwind_df.index).tz_localize(
            'UTC').tz_convert('Europe/Berlin')
        if filter_errors:
            print("---- Errors of GreenWind data in " +
                  "{} are being filtered. ----".format(year))
            # Initialize dictionary for amount of error time steps
            error_dict = {}
            # Get numbers that do display an error
            error_numbers = pd.read_csv(
                os.path.join(os.path.dirname(__file__), 'data/GreenWind',
                             'errors.csv'))['error_numbers'].dropna().values
            # # Get numbers that do not display an error
            # no_error_numbers = pd.read_csv(
            #     os.path.join(os.path.dirname(__file__),
            #                  'data/GreenWind', 'no_errors.csv'))[
            #     'error_number'].values
            error_columns = [
                column_name for column_name in list(greenwind_df) if
                    'error_number' in column_name]
            for error_column in error_columns:
                turbine_name = '_'.join(error_column.split('_')[:3])
                # Get columns to be edited (same wind turbine and wind farm)
                columns = [
                    column for column in list(greenwind_df) if
                    ((turbine_name + '_' in column or
                      column == '{}_power_output'.format('_'.join(
                          turbine_name.split('_')[:2]))) and
                      column != '{}_error_number'.format(turbine_name))]
                # Add column with boolean depending on error number
                # np.nan is error, True is no error
                greenwind_df['{}_boolean'.format(turbine_name)] = [
                    np.nan if value in error_numbers else True for value in
                    greenwind_df[error_column].values]
                # Set values of columns to nan where boolean column is nan
                for column_name in columns:
                    greenwind_df[column_name] = greenwind_df[
                        '{}_boolean'.format(turbine_name)] * greenwind_df[
                            column_name]
                # Write amount of error time step to dictionary
                # and drop Boolean column
                error_dict[turbine_name] = greenwind_df[
                        '{}_boolean'.format(turbine_name)].isna().sum()
                greenwind_df.drop('{}_boolean'.format(turbine_name), axis=1,
                                  inplace=True)
            # Add amount of error time steps of wind farm power output to dict
            wind_farm_names = list(set(['_'.join(item.split('_')[:2]) for
                                        item in error_columns]))
            turbine_names = ['_'.join(item.split('_')[:3]) for
                             item in error_columns]
            for item in wind_farm_names:
                error_dict[item] = sum(error_dict[name] for
                                       name in turbine_names if item in name)
            if print_error_amount:
                # Print amount of time steps set to nan
                df = pd.DataFrame(error_dict, index=['amount']).transpose()
                visualization_tools.print_whole_dataframe(df)
                df.to_csv(os.path.join(os.path.dirname(__file__),
                          '../../../User-Shares/Masterarbeit/Daten/Twele/',
                          'filtered_error_amount_{}.csv'.format(year)))
        print('---- Error filtering of {0} Done. ----'.format(year))
        if resample:
            greenwind_df = greenwind_df.resample(frequency).mean()  # TODO do not resample if most of the values are nans
        else:
            # Add frequency attribute
            freq = pd.infer_freq(greenwind_df.index)
            greenwind_df.index.freq = pd.tseries.frequencies.to_offset(freq)
        if pickle_dump:
            pickle.dump(greenwind_df, open(filename, 'wb'))
    return greenwind_df


def get_error_numbers(year):
    df = get_greenwind_data(year=year, resample=False,
                            pickle_load=False, pickle_dump=False)
    error_numbers = []
    for column_name in list(df):
        if 'error_number' in column_name:
            error_numbers.extend(df[column_name].unique())
    sorted_error_numbers = pd.Series(
        pd.Series(error_numbers).unique()).sort_values()
    sorted_error_numbers.index = np.arange(len(sorted_error_numbers))
    return sorted_error_numbers


if __name__ == "__main__":
    years = [
        2015,
        2016
    ]
    # Decide whether to resample to a certain frequency
    resample = True
    frequency = '30T'
    # Decide whether to filter out time steps with error codes (not filtered
    # is: error code 0 and error codes that are not an error but information)
    # and whether to print the amount of time steps being filtered
    filter_errors = True
    print_error_amount = True
    for year in years:
        filename = os.path.join(os.path.dirname(__file__),
                                'dumps/validation_data',
                                'greenwind_data_{0}.p'.format(year))
        df = get_greenwind_data(year=year, resample=resample,
                                filename=filename, filter_errors=filter_errors,
                                print_error_amount=print_error_amount)

    # Evaluation of error numbers - decide whether to execute:
    error_numbers = False
    if error_numbers:
        error_numbers_total =[]
        for year in years:
            error_numbers = get_error_numbers(year)
            error_numbers.to_csv(
                os.path.join(os.path.dirname(__file__),
                             '../../../User-Shares/Masterarbeit/Daten/Twele/',
                             'error_numbers_{}.csv'.format(year)))
            error_numbers_total.extend(error_numbers)
        sorted_error_numbers_total = pd.Series(
            pd.Series(error_numbers_total ).unique()).sort_values()
        sorted_error_numbers_total.index = np.arange(
            len(sorted_error_numbers_total ))
        sorted_error_numbers_total.to_csv(
            os.path.join(os.path.dirname(__file__),
                         '../../../User-Shares/Masterarbeit/Daten/Twele/',
                         'error_numbers_total.csv'.format(year)))
