"""
The ``greenwind_data`` module contains functions to read and dump measured
feed-in time series from a GreenWind wind farm.

 The following data is available (year 2015 and 2016) for the turbines of
 3 wind farms:
 - power output in kW
 - wind speed in m/s
 - wind direction in °
 - error code

 Additionally the sum of the wind farm power output of each wind farm is
 available.

DateTimeIndex in 'Europe/Berlin' time zone.
"""

# Imports from lib_validation
import visualization_tools
import tools
import latex_tables
from matplotlib import pyplot as plt

# Other imports
import pandas as pd
import numpy as np
import os
import pickle
import logging
import math


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
                       resample=True, threshold=None, plot=False, x_limit=None,
                       frequency='30T', pickle_dump=True, filter_errors=True,
                       print_error_amount=False,
                       error_amount_filename='error_amount.csv',
                       zero_row_to_nan=True):
    r"""
    Fetches GreenWind data.

    Parameters
    ----------
    year : Integer
        Year to fetch.
    pickle_load : Boolean
        If True data frame is loaded from the pickle dump if False the data is
        loaded from the original csv files. Default: False.
    filename : String
        Filename including path of pickle dump. Default: 'greenwind_dump.p'.
    resample : Boolean
        If True the data will be resampled to the `frequency`. (mean power)
        Default: True.
    threshold : Integer or None
        Number of minimum values (not nan) necessary for resampling.
        Default: None.
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
    print_error_amount : Boolean
        If True amount of values set to nan due to error numbers are print for
        each turbine and wind farm (and printed to csv file). Default: False.
    error_amount_filename : String
        Filname including path of error amount data frame.
    zero_row_to_nan : Boolean
        If True if turbine data only contains zeros at one time step these
        values are set to nan.

    Returns
    -------
    green_wind_df : pandas.DataFrame
        GreenWind wind farm data.

    """
    if pickle_load:
        greenwind_df = pickle.load(open(filename, 'rb'))
    else:
        filenames = [
            'WF1_{0}.csv'.format(year),
            'WF2_{0}.csv'.format(year),
            'WF3_{0}.csv'.format(year)]
        greenwind_df = pd.DataFrame()
        for name in filenames:
            # Load data and drop duplicates
            df_part = read_data(name).drop_duplicates()
            if year == 2016:
                # Load data from 2015 as it contains data from January 2016
                name = name.replace('2016', '2015')
                df_part_2015 = read_data(name).drop_duplicates()
                df_part = pd.concat([df_part,
                                     df_part_2015.loc['2015-12-31 23:00:00':]],
                                    axis=0).sort_index()
            if name == 'WF1_2015.csv':
                # Set ambiguous duplicates to nan.
                df_part.loc[df_part.index.get_duplicates()] = np.nan
                df_part.drop_duplicates(inplace=True)
            # Add to DataFrame
            greenwind_df = pd.concat([greenwind_df, df_part], axis=1)
        # Convert index to DatetimeIndex and make time zone aware
        greenwind_df.index = pd.to_datetime(greenwind_df.index).tz_localize(
            'UTC').tz_convert('Europe/Berlin')
        # Choose time steps of the year only (there are some time steps from
        # the year before or after)
        greenwind_df = greenwind_df.loc[str(year)]
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
                    False if value in error_numbers else True for value in
                    greenwind_df[error_column].values]
                # Set values of columns to nan where boolean column is False
                indices = greenwind_df.loc[greenwind_df['{}_boolean'.format(
                    turbine_name)] == False].index
                greenwind_df.loc[indices, columns] = np.nan
                # Write amount of error time step to dictionary
                # and drop Boolean column
                error_dict[turbine_name] = len(indices)
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
                df.to_csv(error_amount_filename)
        print('---- Error filtering of {0} - Done. ----'.format(year))
        if zero_row_to_nan:
            print("---- Zero-rows of data in " +
                  "{} are being filtered. ----".format(year))
            turbine_names = set(['_'.join(item.split('_')[:3]) for
                                item in greenwind_df.columns if
                                item.split('_')[2] != 'power'])
            for turbine_name in turbine_names:
                cols = ['{}_wind_speed'.format(turbine_name),
                        '{}_power_output'.format(turbine_name),
                        '{}_wind_dir'.format(turbine_name),
                        '{}_error_number'.format(turbine_name)]
                # Df with booleans: True for zeros else False
                # Column 'zeros': True if all values in row are zero
                boolean_df = greenwind_df[cols].isin([0.0])
                boolean_df['zeros'] = (
                    boolean_df[cols[0]] * boolean_df[cols[1]] *
                    boolean_df[cols[2]] * boolean_df[cols[3]])
                # Get indices of rows where all values are zero
                indices = boolean_df.loc[boolean_df['zeros'] == True].index
                # Set values of greenwind_df[cols] to nan for indices
                greenwind_df[cols].loc[indices] = np.nan
                # Set values of wind farm power output to nan for indices
                greenwind_df['{}_power_output'.format(
                    '_'.join(turbine_name.split('_')[0:2]))].loc[
                    indices] = np.nan
                print(turbine_name)
                print(len(indices))
            print('---- Zero-rows filtering of {0} - Done. ----'.format(year))
        # Set negative values to nan
        power_columns = [column for column in list(greenwind_df) if
                   'power_output' in column]
        greenwind_df = tools.negative_values_to_nan(greenwind_df,
                                                    columns=power_columns )
        # Set power output of turbines above nominal power (all 2 MW) to nan
        greenwind_df = tools.higher_values_to_nan(
            df=greenwind_df, limit=2100, columns=power_columns)
        # Set wind farm power output to nan, where power output of a wind
        # turbine is nan (take sum again)
        for wf_name in wind_farm_names:
            greenwind_df.drop('{}_power_output'.format(wf_name), axis=1,
                              inplace=True)
            turbine_cols = [i for i in list(greenwind_df.columns) if
                            ('power_output' in i and wf_name in i)]
            greenwind_df['{}_power_output'.format(wf_name)] = greenwind_df[
                turbine_cols].sum(axis=1, skipna=False)
        if resample:
            # Delete error number columns as it is senseless to resample them
            greenwind_df.drop([column for column in list(greenwind_df) if
                               'error_number' in column], axis=1, inplace=True)
            # Resampling
            greenwind_df = tools.resample_with_nan_theshold(
                df=greenwind_df, frequency=frequency, threshold=threshold)
        else:
            # Add frequency attribute
            freq = pd.infer_freq(greenwind_df.index)
            greenwind_df.index.freq = pd.tseries.frequencies.to_offset(freq)
        if pickle_dump:
            pickle.dump(greenwind_df, open(filename, 'wb'))
    return greenwind_df


def get_first_row_turbine_time_series(year, filename_raw_data=None,
                                      pickle_load_raw_data=False,
                                      filter_errors=True,
                                      print_error_amount=False,
                                      pickle_filename='greenwind_first_row.p',
                                      pickle_load=False, frequency='30T',
                                      resample=True, threshold=None,
                                      case='all', exact_degrees=False,
                                      mean_wind_dir=False, bias=False):
    r"""
    Fetches GreenWind data of first row turbine depending on wind direction.

    Parameters
    ----------
    year : Integer
        Year to fetch.
    filename_raw_data : String
        Filename including path of pickle dump from the
        :py:func:`~.get_greenwind_data` function.
    pickle_load_raw_data : Boolean
        If True data frame in :py:func:`~.get_greenwind_data` is loaded from
        the pickle dump if False the data is loaded from the original csv
        files. Note: if True the frequency is the frequency of the pickel dump
        of the raw data. Default: False.
    filter_errors : Booelan
        If True errors are filtered via the error code column. Default: True.
    print_error_amount : Boolean
        If True amount of values set to nan due to error numbers are print for
        each turbine and wind farm (and printed to csv file). Default: False.
    pickle_filename : String
        Filename including path of pickle dump.
    pickle_load : Boolean
        If True data frame is loaded from the pickle dump if False the data
        frame is created. Default: False.
    frequency : String (or freq object...?)
        # TODO add
    resample : Boolean
        If True the data will be resampled to the `frequency`. Default: True.
    threshold : Integer or None
        Number of minimum values (not nan) necessary for resampling.
        Default: None.

    Returns
    -------
    first_row_df : pandas.DataFrame
        GreenWind first row wind turbine data.


    """
    if pickle_load:
        first_row_df = pickle.load(open(pickle_filename, 'rb'))
    else:
        # Load greenwind data without resampling and do not dump.
        green_wind_df = get_greenwind_data(
            year=year, pickle_load=pickle_load_raw_data,
            filename=filename_raw_data, resample=False, threshold=threshold,
            pickle_dump=False, filter_errors=filter_errors,
            print_error_amount=print_error_amount)
        if exact_degrees:
            if case == 'weather_wind_speed_3':
                turbine_dict = {'wf_BE': {'wf_BE_2': (272, 346),
                                          'wf_BE_6': (364, 357)},
                                'wf_BS': {'wf_BS_7': (276, 353)}
                                }
                wind_dir_string = 'wind_dir'
            elif case == 'wind_dir_real':
                turbine_dict = {
                    'wf_BS': {
                        'wf_BS_2': (266, 276), 'wf_BS_7': (276, 353),
                        'wf_BS_12': (119, 119), 'wf_BS_13': (355.5, 360), # actually 1.5
                        'wf_BS_9': (353, 355.5)},
                    'wf_BNW': {
                        'wf_BNW_1': (0, 174), 'wf_BNW_2': (174, 354)
                    }}
                wind_dir_string = 'wind_dir_real'
            elif case == 'weather_wind_speed_3_real':
                turbine_dict = {'wf_BS': {'wf_BS_7': (276, 353)}}
                wind_dir_string = 'wind_dir'
            else:
                turbine_dict = {
                    'wf_BE': {
                        # 'wf_BE_1': (0, 115),  # bad correlation
                        'wf_BE_2': (272, 346), 'wf_BE_5': (100, 155),
                        'wf_BE_6': (364, 357), 'wf_BE_7': (229, 143)
                        },
                    'wf_BS': {
                        'wf_BS_2': (266, 276), 'wf_BS_7': (276, 353),
                        'wf_BS_12': (119, 119), 'wf_BS_13': (355.5, 360), # actually 1.5
                        'wf_BS_9': (353, 355.5)},
                    'wf_BNW': {
                        'wf_BNW_1': (0, 174), 'wf_BNW_2': (174, 354)
                        }}
                wind_dir_string = 'wind_dir'
        else:
            if case == 'weather_wind_speed_3':
                turbine_dict = {'wf_BE': {'wf_BE_2': (270, 315),
                                          'wf_BE_6': (315, 360)},
                                'wf_BS': {'wf_BS_7': (270, 315)}
                                }
                wind_dir_string = 'wind_dir'
            elif case == 'wind_dir_real':
                turbine_dict = {
                    'wf_BS': {
                        'wf_BS_2': (225, 270), 'wf_BS_5': (135, 180),
                        'wf_BS_7': (270, 360), 'wf_BS_10': (180, 225),
                        'wf_BS_12': (90, 135), 'wf_BS_14': (0, 90)
                    },
                    'wf_BNW': {
                        'wf_BNW_1': (0, 180), 'wf_BNW_2': (180, 360)
                    }}
                wind_dir_string = 'wind_dir_real'
            elif case == 'weather_wind_speed_3_real':
                turbine_dict = {'wf_BS': {'wf_BS_7': (270, 315)}}
                wind_dir_string = 'wind_dir'
            else:
                turbine_dict = {
                    'wf_BE': {
                        # 'wf_BE_1': (0, 90),
                        'wf_BE_2': (270, 315), 'wf_BE_5': (90, 180),
                        'wf_BE_6': (315, 360), 'wf_BE_7': (225, 270)
                        },
                    'wf_BS': {
                        'wf_BS_2': (225, 270), 'wf_BS_5': (135, 180),
                        'wf_BS_7': (270, 360), 'wf_BS_10': (180, 225),
                        'wf_BS_12': (90, 135), 'wf_BS_14': (0, 90)
                        },
                    'wf_BNW': {
                        'wf_BNW_1': (0, 180), 'wf_BNW_2': (180, 360)
                        }}
                wind_dir_string = 'wind_dir'
        wind_farm_names = list(set(['_'.join(item.split('_')[0:2]) for
                                   item in turbine_dict]))
        first_row_df = pd.DataFrame()
        for wind_farm_name in wind_farm_names:
            for turbine_name in turbine_dict[wind_farm_name]:
                # Set negative values of wind direction to 360 + wind direction
                negativ_indices = green_wind_df.loc[
                    green_wind_df['{}_{}'.format(
                        turbine_name, wind_dir_string)] < 0].index
                if not negativ_indices.empty:
                    green_wind_df['temp_360'] = 360.0
                    green_wind_df['{}_{}'.format(
                        turbine_name, wind_dir_string)].loc[
                        negativ_indices] = (
                        green_wind_df.loc[negativ_indices]['temp_360'] +
                        green_wind_df.loc[negativ_indices]['{}_{}'.format(
                            turbine_name, wind_dir_string)])
                    green_wind_df.drop('temp_360', axis=1, inplace=True)
                # Get indices of rows where wind direction lies between
                # specified values in `turbine_dict`. If wind direction is not
                # deviating more than 5° from mean wind direction. # TODO delete if not added
                # Example for 'wf_BE_1': 0 <= x < 90.
                if (mean_wind_dir or bias):
                    # Set wind_dir to mean wind direction
                    restrictions = ['wf_{}_{}'.format(wf, wind_dir_string) for
                                    wf in ['BE_1', 'BE_4', 'BS_11', 'BS_4']]
                    mean_dir = green_wind_df[[
                        col for col in green_wind_df.columns if
                        (wind_dir_string in col and
                         wind_farm_name in col and
                         col not in restrictions)]].mean(axis=1)
                if mean_wind_dir:
                    wind_dir = mean_dir
                else:
                    # Set wind_dir to turbine wind direction
                    wind_dir = green_wind_df['{}_{}'.format(
                        turbine_name, wind_dir_string)]
                if bias:
                    indices = green_wind_df.loc[
                        (wind_dir >=
                         float(
                             turbine_dict[wind_farm_name][turbine_name][0])) &
                        (wind_dir <
                         float(turbine_dict[wind_farm_name][
                                   turbine_name][1])) &
                        (abs(green_wind_df['{}_{}'.format(turbine_name,
                                                          wind_dir_string)] -
                             mean_wind_dir) <= 10.0)].index
                else:
                    indices = green_wind_df.loc[
                        (wind_dir >=
                         float(turbine_dict[wind_farm_name][turbine_name][0])) &
                        (wind_dir <
                         float(turbine_dict[wind_farm_name][
                                   turbine_name][1]))].index
                # Add temporary wind speed column with only nans # TODO not necessary
                green_wind_df['wind_speed_temp_{}'.format(
                    turbine_name)] = np.nan
                # Add wind speed of wind speed column for `indices`
                green_wind_df['wind_speed_temp_{}'.format(turbine_name)].loc[
                    indices] = green_wind_df['{}_wind_speed'.format(
                    turbine_name)].loc[indices]
                # Add temporary power output column with only nans
                green_wind_df['power_output_temp_{}'.format(
                    turbine_name)] = np.nan
                # Add wind speed of power output column for `indices`
                green_wind_df['power_output_temp_{}'.format(turbine_name)].loc[
                    indices] = green_wind_df['{}_power_output'.format(
                    turbine_name)].loc[indices]
            # Add power output and wind speed as mean from all temp columns
            wind_speed_columns = [
                column_name for column_name in list(green_wind_df) if
                ('wind_speed_temp' in column_name and
                 wind_farm_name in column_name)]
            power_output_columns = [
                column_name for column_name in list(green_wind_df) if
                ('power_output_temp' in column_name and
                 wind_farm_name in column_name)]
            green_wind_df['{}_wind_speed'.format(
                wind_farm_name)] = green_wind_df[wind_speed_columns].mean(
                axis=1, skipna=True)
            green_wind_df['{}_power_output'.format(
                wind_farm_name)] = green_wind_df[power_output_columns].mean(
                axis=1, skipna=True)
            # # Set wind speed and power output column to nan if all temporary
            # # columns are nan # TODO: not needed skipna, but nan if all nan
            # wind_indices = green_wind_df.loc[green_wind_df[
            #     wind_speed_columns].isnull().sum(axis=1) == len(
            #     wind_speed_columns)].index
            # power_indices = green_wind_df.loc[green_wind_df[
            #     power_output_columns].isnull().sum(axis=1) == len(
            #     wind_speed_columns)].index
            # green_wind_df['{}_wind_speed'.format(
            #     wind_farm_name)].loc[wind_indices] = np.nan
            # green_wind_df['{}_power_output'.format(
            #     wind_farm_name)].loc[power_indices] = np.nan
            first_row_df = pd.concat([first_row_df, green_wind_df[[
                '{}_wind_speed'.format(wind_farm_name),
                '{}_power_output'.format(wind_farm_name)]]], axis=1)
        pickle.dump(first_row_df, open(pickle_filename, 'wb'))
    if resample:
        first_row_df = tools.resample_with_nan_theshold(
            df=first_row_df, frequency=frequency, threshold=threshold)
    else:
        # Add frequency attribute
        freq = pd.infer_freq(first_row_df.index)
        first_row_df.index.freq = pd.tseries.frequencies.to_offset(freq)
    return first_row_df


def evaluate_duplicates(years):
    duplicates_dict = {}
    for year in years:
        duplicates_dict[year] = {}
        filenames = [
            'WF1_{0}.csv'.format(year),
            'WF2_{0}.csv'.format(year),
            'WF3_{0}.csv'.format(year)]
        for name in filenames:
            df_part = read_data(name)
            # Get duplicates
            duplicates = df_part.index.get_duplicates()
            # Data frame with only duplicated indices
            duplicates_df = df_part.loc[duplicates]
            # Get amount of duplicates per time step before drop
            duplicates_per_step = {}
            for time_step in duplicates:
                duplicates_per_step[time_step] = len(
                    duplicates_df.loc[time_step])
            # Drop duplicates
            df_part.drop_duplicates(inplace=True)
            # Get remaining duplicated indices
            duplicates_after_drop = df_part.index.get_duplicates()
            # Get unique error numbers
            unique_error_numbers = error_numbers_from_df(duplicates_df)
            # Create duplicates dict
            duplicates_dict[year][name.split('_')[0]] = {
                'duplicates_before_drop': duplicates,
                'duplicates_after_drop': duplicates_after_drop,
                'duplicates_df': duplicates_df,
                'duplicates_df_after_drop':
                df_part.loc[duplicates_after_drop],
                'duplicates_per_step_before_drop': duplicates_per_step,
                'error_numbers': unique_error_numbers}
    print('--- duplicates dict ---')
    print(duplicates_dict)
    print('--- The duplicates dict should be looked at in debugging mode ---')
    return duplicates_dict


def evaluate_nans(years):
    df = pd.DataFrame()
    for year in years:
        df_part_year = pd.DataFrame()
        filenames = [
            'WF1_{0}.csv'.format(year),
            'WF2_{0}.csv'.format(year),
            'WF3_{0}.csv'.format(year)]
        for name in filenames:
            df_part = pd.DataFrame(read_data(name).isnull().sum()).sort_index()
            df_part.columns = [year]
            df_part_year = pd.concat([df_part_year, df_part], axis=0)
        df = pd.concat([df, df_part_year], axis=1)
    return df


def error_numbers_from_df(df):
    error_numbers = []
    for column_name in list(df):
        if 'error_number' in column_name:
            error_numbers.extend(df[column_name].unique())
    sorted_error_numbers = pd.Series(
        pd.Series(error_numbers).unique()).sort_values()
    sorted_error_numbers.index = np.arange(len(sorted_error_numbers))
    return sorted_error_numbers


def get_error_numbers(year):
    df = get_greenwind_data(year=year, resample=False,
                            pickle_load=False, pickle_dump=False)
    sorted_error_numbers = error_numbers_from_df(df)
    return sorted_error_numbers


def get_highest_wind_speeds(year, filename_green_wind, pickle_load=False,
                            filename='green_wind_highest_wind_speed.p'):
    if pickle_load:
        green_wind_df = pickle.load(open(filename, 'rb'))
    else:
        # Load greenwind data without resampling and do not dump.
        green_wind_df = get_greenwind_data(
            year=year, pickle_load=True,
            filename=filename_green_wind, resample=False,
            pickle_dump=False, filter_errors=True,
            print_error_amount=False)
        wind_cols = [col for col in list(green_wind_df) if
                     (col.split('_')[3] == 'wind' and col.split('_')[
                         4]) == 'speed']
        wfs = ['wf_BE', 'wf_BS', 'wf_BNW']
        for wf in wfs:
            wind_cols_wf = [col for col in wind_cols if wf in col]
            green_wind_df['{}_highest_wind_speed'.format(wf)] = (
                green_wind_df[wind_cols_wf].apply(max, axis=1))
        columns = ['{}_highest_wind_speed'.format(wf) for wf in wfs]
        green_wind_df = green_wind_df[columns]
        pickle.dump(green_wind_df, open(filename, 'wb'))
    return green_wind_df


def get_highest_power_output_and_wind_speed(
        year, filename_green_wind, pickle_load=False,
        filename='green_wind_highest_power_output.p'):
    if pickle_load:
        highest_df = pickle.load(open(filename, 'rb'))
    else:
        # Load greenwind data without resampling and do not dump.
        green_wind_df = get_greenwind_data(
            year=year, pickle_load=True,
            filename=filename_green_wind, resample=False,
            pickle_dump=False, filter_errors=True,
            print_error_amount=False)
        power_cols = [col for col in list(green_wind_df) if
                      (col.split('_')[3] == 'power' and
                       col.split('_')[4]) == 'output']
        wfs = ['wf_BE', 'wf_BS', 'wf_BNW']
        for wf in wfs:
            power_cols_wf = [col for col in power_cols if wf in col]
            green_wind_df['{}_highest_power_output'.format(wf)] = (
                green_wind_df[power_cols_wf].apply(max, axis=1))
        columns = ['{}_highest_power_output'.format(wf) for wf in wfs]
        power_df = green_wind_df[columns]
        wind_df = get_highest_wind_speeds(
            year, filename_green_wind, pickle_load=True,
            filename=os.path.join(
                os.path.dirname(__file__), 'dumps/validation_data',
                'green_wind_highest_wind_speed_{}.p'.format(year)))
        csv_df = pd.concat([power_df, green_wind_df[power_cols]], axis=1)
        csv_df.sort_index(axis=1, inplace=True)
        csv_df.to_csv('data/GreenWind/highest_power_output_{}.csv'.format(
            year))
        highest_df = pd.concat([power_df, wind_df], axis=1)
        pickle.dump(highest_df, open(filename, 'wb'))
    return highest_df


def plot_green_wind_wind_roses():
    for year in [2015, 2016]:
        filename = os.path.join(os.path.dirname(__file__),
                                'dumps/validation_data',
                                'greenwind_data_{0}.p'.format(year))
        green_wind_df = get_greenwind_data(
            year=year, resample=False, pickle_load=True, filename=filename,
            filter_errors=True, print_error_amount=False)
        # Drop wind farm data
        green_wind_df.drop([
            'wf_BE_power_output', 'wf_BS_power_output', 'wf_BNW_power_output'],
            axis=1, inplace=True)
        # Get turbine names
        turbines = set(['_'.join(column.split('_')[0:3]) for column in
                        list(green_wind_df)])
        # Construct pairs of wind direction and wind speed of each turbine and
        # plot wind roses
        for turbine_name in turbines:
            visualization_tools.plot_wind_rose(
                wind_speed=green_wind_df['{}_wind_speed'.format(
                    turbine_name)].values,
                wind_direction=green_wind_df['{}_wind_dir'.format(
                    turbine_name)].values,
                filename=os.path.join(
                    os.path.dirname(__file__), 'Plots/wind_roses',
                    'wind_rose_{0}_{1}'.format(turbine_name, year)),
                title='Wind rose of {0} in {1}'.format(turbine_name, year))


def evaluate_wind_directions(year, save_folder='', corr_min=0.8,
                             pickle_load=False, WT_14=False):
    pickle_path = os.path.join(os.path.dirname(__file__),
                               'dumps/validation_data',
                               'green_wind_wind_dir_{}'.format(year))
    if pickle_load:
        wind_directions_df = pickle.load(open(pickle_path, 'rb'))
    else:
        # Get Greenwind wind direction data
        green_wind_data = get_greenwind_data(
            year=year, resample=False, pickle_load=True, filter_errors=True,
            print_error_amount=False)
        # Select wind directions
        wind_directions_df = green_wind_data[[
            column_name for column_name in list(green_wind_data) if
            '_'.join(column_name.split('_')[3:]) == 'wind_dir']]
        pickle.dump(wind_directions_df, open(pickle_path, 'wb'))
    wfs = ['wf_BE', 'wf_BS', 'wf_BNW']
    for wf in wfs:
        wf_wind_dir_df = wind_directions_df[[
            column_name for column_name in list(wind_directions_df) if
            wf in column_name]]
        if (WT_14 and wf == 'wf_BS'):
            # Set negative values of wind direction to 360 + wind direction
            wf_wind_dir_df['temp_360'] = 360.0
            negativ_indices = wf_wind_dir_df.loc[
                wf_wind_dir_df['wf_BS_14_wind_dir'] < 0].index
            wf_wind_dir_df['wf_BS_14_wind_dir'].loc[negativ_indices] = (
                wf_wind_dir_df['temp_360'] +
                wf_wind_dir_df['wf_BS_14_wind_dir'])
            wf_wind_dir_df.drop('temp_360', axis=1, inplace=True)
        correlation = wf_wind_dir_df.corr().sort_index().sort_index(axis=1)
        amount_df = pd.DataFrame(
            correlation[correlation >= corr_min].count() - 1,
            columns=['corr >= {}'.format(corr_min)]).transpose()
        pd.concat([correlation, amount_df], axis=0).to_csv(
            os.path.join(
                save_folder, 'gw_wind_dir_corr_{0}_{1}_{2}.csv'.format(
                    wf, year, corr_min)))
        logging.info("Wind direction evaluation was written to csv.")


def plot_wind_directions_of_farms(year, pickle_load_wind_dir_df,
                                  adapt_negative=True):
    if pickle_load_wind_dir_df:
        pickle_path = os.path.join(os.path.dirname(__file__),
                                   'dumps/validation_data',
                                   'green_wind_wind_dir_{}'.format(year))
        wind_directions_df = pickle.load(open(pickle_path, 'rb'))
    else:
        # Get Greenwind wind direction data
        green_wind_data = get_greenwind_data(
            year=year, resample=False, pickle_load=False, filter_errors=True,
            print_error_amount=False)
        # Select wind directions
        wind_directions_df = green_wind_data[[
            column_name for column_name in list(green_wind_data) if
            '_'.join(column_name.split('_')[3:]) == 'wind_dir']]
    for wf in ['BE', 'BS', 'BNW']:
        wind_dir_df_wf = wind_directions_df[[
            col for col in wind_directions_df.columns if wf in col]]
        if adapt_negative:
            # Set negative values of wind direction to 360 + wind direction
            for column in wind_dir_df_wf.columns:
                negativ_indices = wind_dir_df_wf.loc[
                    wind_dir_df_wf[column] < 0].index
                if not negativ_indices.empty:
                    wind_dir_df_wf['temp_360'] = 360.0
                    wind_dir_df_wf[column].loc[negativ_indices] = (
                        wind_dir_df_wf.loc[negativ_indices]['temp_360'] +
                        wind_dir_df_wf.loc[negativ_indices][column])
                    wind_dir_df_wf.drop('temp_360', axis=1, inplace=True)
            filename_add_on = 'adapt_negative'
        else:
            filename_add_on = ''
        fig, ax = plt.subplots()
        wind_dir_df_wf.plot(ax=ax, legend=True)
        plt.xlim(xmin=wind_dir_df_wf.index[0],
                 xmax=wind_dir_df_wf.index[50])
        # maximum = wind_dir_df_wf.values.min()
        # print(maximum)
        plt.ylim(ymin=-100,  ymax=360)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        fig.savefig(os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/inc/images/evaluation_wind_dir',
            'Wind_directions_{}_{}{}'.format(wf, year, filename_add_on)),
            bbox_inches="tight")
        plt.close()


def evaluate_wind_dir_vs_gondel_position(year, save_folder, corr_min):
    # TODO laufen lassen auf RLI PC!!
    # Load greenwind data without resampling and do not dump.
    green_wind_df = get_greenwind_data(
        year=year, pickle_load=True,
        filename=os.path.join(
            os.path.dirname(__file__), 'dumps/validation_data',
            'greenwind_data_{0}_raw_resolution.p'.format(year)),
        resample=False, pickle_dump=False, filter_errors=True)
    for wf, turbine_nb in zip(['BE', 'BS', 'BNW'], [9, 14, 2]):
        dict = {}
        for i in range(turbine_nb):
            df = green_wind_df[['wf_{}_{}_wind_dir'.format(wf, i + 1),
                                'wf_{}_{}_wind_dir_real'.format(wf, i + 1)]]
            corr = df.corr().iloc[:, 0][1]
            dict['{}_{}'.format(wf, i + 1)] = corr
        dict_df = pd.DataFrame(dict, index=['corr']).transpose()
        dict_df['mean_bias'] = np.nan
        for i in range(turbine_nb):
            df = green_wind_df[['wf_{}_{}_wind_dir'.format(wf, i + 1),
                                'wf_{}_{}_wind_dir_real'.format(wf, i + 1)]]
            bias = df.iloc[:, 0] - df.iloc[:, 1]
            dict_df['mean_bias'].loc['{}_{}'.format(wf, i + 1)] = bias.mean()
        dict_df.to_csv(os.path.join(
            os.path.dirname(__file__), save_folder,
            'correlation_{}_{}.csv'.format(wf, year)))


def plot_wind_dir_vs_power_output(year, resolution, adapt_negative=True,
                                  xlim=True, mean=None, v_std_step=0.5):
    if resolution == 10:
        green_wind_data_pickle = os.path.join(
            os.path.dirname(__file__), 'dumps/validation_data',
            'greenwind_data_{0}_raw_resolution.p'.format(year))
    elif resolution == 30:
        green_wind_data_pickle = os.path.join(
            os.path.dirname(__file__), 'dumps/validation_data',
            'greenwind_data_{0}.p'.format(year))
    else:
        raise ValueError("resolution must  be 10 or 30")
    green_wind_df = pickle.load(open(green_wind_data_pickle, 'rb'))
    keep_cols = [col for col in green_wind_df.columns if
                 ('power_output' in col or 'wind_dir' in col or
                  'wind_speed' in col and 'real' not in col)]
    green_wind_df = green_wind_df[keep_cols]
    green_wind_df.drop(['wf_{}_power_output'.format(name) for
                        name in ['BE', 'BS', 'BNW']], axis=1, inplace=True)
    if adapt_negative:
        # Set negative values of wind direction to 360 + wind direction
        wind_dir_cols = [col for col in green_wind_df.columns if
                         'wind_dir' in col]
        for column in wind_dir_cols:
            negativ_indices = green_wind_df.loc[
                green_wind_df[column] < 0].index
            green_wind_df['temp_360'] = 360.0
            if not negativ_indices.empty:
                green_wind_df[column].loc[negativ_indices] = (
                    green_wind_df.loc[negativ_indices]['temp_360'] +
                    green_wind_df.loc[negativ_indices][column])
            green_wind_df.drop('temp_360', axis=1, inplace=True)
        filename_add_on = '_adapt_negative'
    else:
        filename_add_on = ''
    # Dict for title
    turbine_dict_exact = {
            # 'wf_BE_1': (0, 115),  # bad correlation
            'wf_BE_2': (272, 346), 'wf_BE_5': (100, 155),
            'wf_BE_6': (364, 357), 'wf_BE_7': (229, 143),
            'wf_BS_2': (266, 276), 'wf_BS_7': (276, 353),
            'wf_BS_12': (119, 119), 'wf_BS_13': (355.5, 360),  # actually 1.5
            'wf_BS_9': (353, 355.5),
            'wf_BNW_1': (0, 174), 'wf_BNW_2': (174, 354)}
    turbine_dict = {
            # 'wf_BE_1': (0, 90),  # bad correlation
            'wf_BE_2': (270, 315), 'wf_BE_5': (90, 180),
            'wf_BE_6': (315, 360), 'wf_BE_7': (225, 270),
            'wf_BS_2': (225, 270), 'wf_BS_5': (135, 180),
            'wf_BS_7': (270, 360), 'wf_BS_10': (180, 225),
            'wf_BS_12': (90, 135), 'wf_BS_14': (0, 90),
            'wf_BNW_1': (0, 180), 'wf_BNW_2': (180, 360)}
    # build pairs
    turbine_names = set(
        ['_'.join(col.split('_')[0:3]) for col in green_wind_df.columns])
    pairs_df_list = [green_wind_df.loc[:, [
        '{0}_wind_dir'.format(turbine_name),
        '{0}_power_output'.format(turbine_name),
        '{0}_wind_speed'.format(turbine_name)]] for
                     turbine_name in turbine_names]
    for pair_df in pairs_df_list:
        # nan to other columns
        pair_df.loc[:, pair_df.columns[0]].loc[pair_df.loc[
            pair_df.loc[:, pair_df.columns[1]].isnull() == True].index] = np.nan
        pair_df.loc[:, pair_df.columns[1]].loc[pair_df.loc[
            pair_df.loc[:,
            pair_df.columns[0]].isnull() == True].index] = np.nan
        turbine_name = '_'.join(pair_df.columns[0].split('_')[0:3])
        if mean:
            # Get maximum wind speed rounded to the next integer
            maximum_v_int = math.ceil(
                pair_df['{}_wind_speed'.format(turbine_name)].max())
            # Get maximum standard wind speed rounded to next v_std_step
            maximum_v_std = (maximum_v_int if
                             maximum_v_int - pair_df['{}_wind_speed'.format(
                                 turbine_name)].max() < v_std_step else
                             maximum_v_int - v_std_step)
            # Add v_std (standard wind speed) column to data frame
            pair_df['v_std'] = np.nan
            standard_wind_speeds = np.arange(0.0, maximum_v_std + v_std_step,
                                             v_std_step)
            for v_std in standard_wind_speeds:
                # Set standard wind speeds depending on wind_speed column value
                indices = pair_df.loc[(pair_df.loc[:, '{}_wind_speed'.format(
                    turbine_name)] <= v_std) &
                                 (pair_df.loc[:, '{}_wind_speed'.format(
                                     turbine_name)] > (
                                     v_std - v_std_step))].index
                pair_df['v_std'].loc[indices] = v_std
            # Drop rows where v_std is nan
            keep_indices = pair_df[['v_std']].stack().index.get_level_values(0)
            pair_df = pair_df.loc[keep_indices]
            # For each standard wind direction get mean for every standard wind
            # speed
            standard_wind_dirs = np.arange(0.0, 360 + 10.0, 10.0)
            plot_df = pd.DataFrame()
            for dir_std in standard_wind_dirs:
                # Set standard wind speeds depending on wind_speed column value
                indices = pair_df.loc[(pair_df.loc[:, '{}_wind_dir'.format(
                    turbine_name)] <= dir_std) &
                                 (pair_df.loc[:, '{}_wind_dir'.format(
                                     turbine_name)] > (
                                     dir_std - 10.0))].index
                df_v_std = pd.DataFrame(pair_df.loc[indices])
                df_v_std.set_index('v_std', inplace=True)
                df_v_std = df_v_std.groupby(df_v_std.index).mean()
                df_v_std.drop([col for col in df_v_std.columns if
                               ('wind_speed' in col or
                                'wind_dir' in col)], axis=1, inplace=True)
                df_v_std['wind_speed'] = df_v_std.index
                df_v_std['wind_dir'] = dir_std
                plot_df = pd.concat([plot_df, df_v_std], axis=0)
            pair_df = pd.DataFrame(plot_df)
            filename_add_on_3 = '_mean'
            folder_add_on = 'mean/{}'.format(str(v_std_step).replace('.', '_'))
            marker_size = 1
        else:
            filename_add_on_3 = ''
            folder_add_on = ''
            marker_size = 0.1
        fig, ax = plt.subplots()
        x_value = [col for col in list(pair_df) if 'wind_dir' in col][0]
        y_value = [col for col in list(pair_df) if 'power_output' in col][0]
        wind_speed = [col for col in list(pair_df) if 'wind_speed' in col][0]
        # pair_df[wind_speed].loc[pair_df.loc[pair_df[wind_speed] == np.nan].index] = -5.0
        pair_df.plot.scatter(x=x_value, y=y_value, ax=ax,
                             c=wind_speed, cmap='winter',
                             s=marker_size,
                             # alpha=0.5
                             )
        if turbine_name in turbine_dict:
            ax.plot((turbine_dict[turbine_name][0], turbine_dict[turbine_name][0]),
                    (-5, 2100), c='black', alpha=0.5, linestyle='--',
                    linewidth=1)
            ax.plot(
                (turbine_dict[turbine_name][1], turbine_dict[turbine_name][1]),
                (-5, 2100), c='black', alpha=0.5, linestyle='--',
                linewidth=1)
        if (turbine_name in turbine_dict_exact and
                turbine_name not in turbine_dict):
            ax.plot((turbine_dict_exact[turbine_name][0],
                     turbine_dict_exact[turbine_name][0]), (-5, 2100),
                    c='black', alpha=0.5, linestyle='--', linewidth=1)
            ax.plot((turbine_dict_exact[turbine_name][1],
                     turbine_dict_exact[turbine_name][1]), (-5, 2100),
                    c='black', alpha=0.5, linestyle='--', linewidth=1)
        if (turbine_name in turbine_dict_exact and
                turbine_name in turbine_dict):
            title = "{} degrees {} degrees 'exact' {}".format(
                turbine_name, turbine_dict[turbine_name],
                turbine_dict_exact[turbine_name])
        elif (turbine_name in turbine_dict and
                    turbine_name not in turbine_dict_exact):
            title = "{} degrees {}".format(
                turbine_name, turbine_dict[turbine_name])
        elif (turbine_name not in turbine_dict and
                    turbine_name in turbine_dict_exact):
            title = "{} degrees 'exact' {}".format(
                turbine_name, turbine_dict_exact[turbine_name])
        else:
            title = turbine_name
        plt.title(title)
        if xlim:
            plt.xlim(xmin=-5, xmax=365)
            filename_add_on_2 = '_xlim'
            folder = 'xlim'
        else:
            filename_add_on_2 = ''
            folder = ''
        fig.savefig(os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/inc/images/gw_wind_dir_vs_power_output/pdf',
            folder, folder_add_on, 'correlation_{}_{}_{}{}{}{}.pdf'.format(
                turbine_name, year, resolution, filename_add_on, filename_add_on_2,
                filename_add_on_3)))
        plt.close()

if __name__ == "__main__":
    # Select cases: (parameters below in section)
    load_data = False
    evaluate_first_row_turbine = True
    evaluate_highest_wind_speed = False
    evaluate_highest_power_output = False
    plot_wind_roses = False
    evaluate_wind_direction_corr = False
    plot_wind_direcions = False
    wind_dir_vs_gondel_position = False
    plot_wind_dir_vs_power = False
    nans_evaluation = False
    duplicates_evaluation = False
    error_numbers = False

    years = [
        2015,
        2016
    ]

    # ----- Load data -----#
    if load_data:
        # Decide whether to resample to a certain frequency with a certain
        # threshold
        resample_info = [True, False]
        frequency = '30T'
        threshold = 2  # Original are 10
        # Decide whether to filter out time steps with error codes (not
        # filtered is: error code 0 and error codes that are not an error but
        # information) and whether to print the amount of time steps being
        # filtered
        filter_errors = True
        print_error_amount = True
        print_erroer_amount_total = True
        zero_row_to_nan = True
        for resample in resample_info:
            for year in years:
                if resample:
                    filename = os.path.join(
                        os.path.dirname(__file__), 'dumps/validation_data',
                        'greenwind_data_{0}.p'.format(year))
                else:
                    filename = os.path.join(
                        os.path.dirname(__file__),
                        'dumps/validation_data',
                        'greenwind_data_{0}_raw_resolution.p'.format(year))
                error_amount_filename = os.path.join(
                    os.path.dirname(__file__),
                    '../../../User-Shares/Masterarbeit/Daten/Twele/',
                    'filtered_error_amount_{}.csv'.format(year))
                df = get_greenwind_data(
                    year=year, resample=resample,
                    frequency=frequency, threshold=threshold,
                    filename=filename, filter_errors=filter_errors,
                    print_error_amount=print_error_amount,
                    error_amount_filename=error_amount_filename,
                    zero_row_to_nan=zero_row_to_nan)

            if print_erroer_amount_total and print_error_amount: # TODO not for both resampling cases
                filenames = [os.path.join(
                    os.path.dirname(__file__),
                    '../../../User-Shares/Masterarbeit/Daten/Twele/',
                    'filtered_error_amount_{}.csv'.format(year)) for
                    year in years]
                dfs = [pd.read_csv(filename, index_col=0).rename(
                    columns={'amount': year}) for filename, year in zip(
                    filenames, years)]
                df = pd.concat(dfs, axis=1)
                error_amout_df = df.loc[['wf_BE', 'wf_BS', 'min_periods']]
                error_amout_df.rename(index={ind: ind.replace('wf_', 'WF ') for
                                             ind in error_amout_df.index},
                                      inplace=True)
                error_amout_df.to_csv(os.path.join(
                    os.path.dirname(__file__),
                    '../../../User-Shares/Masterarbeit/Daten/Twele/',
                    'filtered_error_amount_years.csv'))
                latex_filename = os.path.join(
                    os.path.dirname(__file__),
                    '../../../User-Shares/Masterarbeit/Latex/Tables/',
                    'filtered_error_amount_years.tex')
                error_amout_df.to_latex(
                    buf=latex_filename,
                    column_format=latex_tables.create_column_format(
                        len(error_amout_df.columns), 'c'),
                    multicolumn_format='c')

    # ----- First row turbine -----#
    if evaluate_first_row_turbine:
        # Parameters
        cases = [
            'wind_dir_real',
            'wind_speed_1',
            'weather_wind_speed_3',
            'weather_wind_speed_3_real'
        ]
        first_row_resample = True
        first_row_frequency = '30T'
        first_row_threshold = 2
        first_row_filter_errors = True
        first_row_print_error_amount = False
        first_row_print_erroer_amount_total = False # only with pickle_load_raw_data False!
        pickle_load_raw_data = True
        exact_degrees = False
        mean_wind_dir = True  # Use mean wind direction (of correlating wind directions) instead of single turbine wind directions
        bias = True
        for case in cases:
            for year in years:
                filename_raw_data = os.path.join(
                    os.path.dirname(__file__), 'dumps/validation_data',
                    'greenwind_data_{0}_raw_resolution.p'.format(year))
                if exact_degrees:
                    add_on = '_exact_degrees'
                else:
                    add_on = ''
                if mean_wind_dir:
                    add_on_2 = 'mean_wind_dir'
                else:
                    add_on_2 = ''
                if bias:
                    add_on_3 = '_bias'
                else:
                    add_on_3 = ''
                if case == 'wind_speed_1':
                    pickle_filename = os.path.join(
                        os.path.dirname(__file__), 'dumps/validation_data',
                        'greenwind_data_first_row_{0}{1}{2}{3}.p'.format(
                            year, add_on, add_on_2, add_on_3))
                if case == 'weather_wind_speed_3':
                    pickle_filename = os.path.join(
                        os.path.dirname(__file__), 'dumps/validation_data',
                        'greenwind_data_first_row_{0}_weather_wind_speed_3{1}{2}{3}.p'.format(
                            year, add_on, add_on_2, add_on_3))
                if case == 'wind_dir_real':
                    pickle_filename = os.path.join(
                        os.path.dirname(__file__), 'dumps/validation_data',
                        'greenwind_data_first_row_{0}_wind_dir_real{1}{2}{3}.p'.format(
                            year, add_on, add_on_2, add_on_3))
                if case == 'weather_wind_speed_3_real':
                    pickle_filename = os.path.join(
                        os.path.dirname(__file__), 'dumps/validation_data',
                        'greenwind_data_first_row_{0}_weather_wind_speed_3_real{1}{2}{3}.p'.format(
                            year, add_on, add_on_2, add_on_3))
                error_amount_filename = os.path.join(
                    os.path.dirname(__file__),
                    '../../../User-Shares/Masterarbeit/Daten/Twele/',
                    'filtered_error_amount__first_row{}.csv'.format(year))
                df = get_first_row_turbine_time_series(
                    year=year, filename_raw_data=filename_raw_data,
                    pickle_load_raw_data=pickle_load_raw_data,
                    filter_errors=first_row_filter_errors,
                    print_error_amount=first_row_print_error_amount,
                    pickle_filename=pickle_filename,
                    frequency=first_row_frequency, resample=first_row_resample,
                    threshold=first_row_threshold, case=case,
                    exact_degrees=exact_degrees, mean_wind_dir=mean_wind_dir)

            # wfs = ['wf_BE', 'wf_BS', 'wf_BNW']
            # temp_cols = [col for col in list(green_wind_df) if
            #              'wind_speed_temp' in col]
            # temp_cols.extend(
            #     ['highest_wind_speed_{}'.format(wf) for wf in wfs])
            # wind_cols = [col for col in list(green_wind_df) if
            #              (col.split('_')[3] == 'wind' and col.split('_')[
            #                  4]) == 'speed']
            # print(wind_cols)
            # for wf in wfs:
            #     green_wind_df['highest_wind_speed_{}'.format(wf)] = np.nan
            #     wind_cols_wf = [col for col in wind_cols if wf in col]
            #     temp_cols_wf = [col for col in temp_cols if wf in col]
            #     for index in green_wind_df.index:
            #         green_wind_df.loc[index]['highest_wind_speed_{}'.format(
            #             wf)] = (np.nan if green_wind_df.loc[index][
            #             wind_cols_wf].dropna().empty
            #                     else max(
            #             green_wind_df.loc[index][wind_cols_wf].dropna()))
            #     wf_cols = list(wind_cols_wf)
            #     wf_cols.extend(temp_cols_wf)
            #     wf_cols.extend(
            #         [col.replace('speed', 'dir') for col in wind_cols_wf])
            #     green_wind_df[wf_cols].to_csv(
            #         'first_row_check_{}_{}.csv'.format(wf, year),
            #         sep=',', encoding='utf-8')
            # green_wind_df[temp_cols].to_csv(
            #     'first_row_check_{}.csv'.format(year), sep=',',
            #     encoding='utf-8')

        if (first_row_print_erroer_amount_total and
                first_row_print_error_amount):
            filenames = [os.path.join(
                os.path.dirname(__file__),
                '../../../User-Shares/Masterarbeit/Daten/Twele/',
                'filtered_error_amount_first_row{}.csv'.format(year)) for
                year in years]
            dfs = [pd.read_csv(filename, index_col=0).rename(
                columns={'amount': year}) for
                   filename, year in zip(filenames, years)]
            df = pd.concat(dfs, axis=1)
            error_amout_df = df.loc[['wf_BE', 'wf_BS', 'wf_BNW']]
            error_amout_df.rename(index={ind: ind.replace('wf_', 'WF ') for
                                         ind in error_amout_df.index})
            error_amout_df.to_csv(os.path.join(
                os.path.dirname(__file__),
                '../../../User-Shares/Masterarbeit/Daten/Twele/',
                'filtered_error_amount_years_first_row.csv'))

    # ---- highest wind speed ----#
    if evaluate_highest_wind_speed:
        for year in years:
            filename_green_wind = os.path.join(
                os.path.dirname(__file__), 'dumps/validation_data',
                'greenwind_data_{0}.p'.format(year))
            filename = os.path.join(
                os.path.dirname(__file__), 'dumps/validation_data',
                'green_wind_highest_wind_speed_{}.p'.format(year))
            highest_wind_speed = get_highest_wind_speeds(
                year, filename_green_wind, pickle_load=False,
                filename=filename)
            print(highest_wind_speed)

    # ---- highest power output ----#
    if evaluate_highest_power_output:  # TODO: ATTENTION: dump was renamed!!!!
        for year in years:
            filename_green_wind = os.path.join(
                os.path.dirname(__file__), 'dumps/validation_data',
                'greenwind_data_{0}_raw_resolution.p'.format(year))
            filename = os.path.join(
                os.path.dirname(__file__), 'dumps/validation_data',
                'greenwind_data_first_row_{0}_highest_power.p'.format(year))
            highest_power_output = get_highest_power_output_and_wind_speed(
                year, filename_green_wind, filename=filename)

    # ---- Plot wind roses ----#
    if plot_wind_roses:
        plot_green_wind_wind_roses()

    # ---- Wind direction correlation ----#
    if evaluate_wind_direction_corr:
        corr_mins = [0.6, 0.7, 0.8]
        frequency = None
        WT_14 = True
        folder = os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/Tables/Evaluation',
            'green_wind_wind_direction')
        for corr_min in corr_mins:
            for year in years:
                evaluate_wind_directions(year=year, save_folder=folder,
                                         corr_min=corr_min, WT_14=WT_14)

    # ---- Plot wind directions ---- #
    if plot_wind_direcions:
        adapt_negatives = [
            True,
            False
        ]
        for adapt_negative in adapt_negatives:
            for year in years:
                plot_wind_directions_of_farms(
                    year, pickle_load_wind_dir_df=True,
                    adapt_negative=adapt_negative)

    # ---- Wind direction vs. golden position ----#
    if wind_dir_vs_gondel_position:
        corr_min = 0.6
        folder = os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/Tables/Evaluation/' +
            'gw_wind_dir_vs_gondel_pos')
        for year in years:
            evaluate_wind_dir_vs_gondel_position(year=year, save_folder=folder,
                                                 corr_min=corr_min)
    # ---- Wind direction vs. power output plots ---- #
    if plot_wind_dir_vs_power:
        resolutions = [
            10,
            # 30
        ]
        xlims = [
            True,
            False
        ]
        means = [
            True,
            # False
        ]
        v_std_steps = [
            # 0.5,
            # 1.0,
            3.0
            # 4.0
        ]

        for year in years:
            for resolution in resolutions:
                for xlim in xlims:
                    for mean in means:
                        for v_std_step in v_std_steps:
                            if (mean and xlim):
                                pass
                            elif (not mean and v_std_step != v_std_steps[0]):
                                pass
                            else:
                                plot_wind_dir_vs_power_output(
                                    year=year, resolution=resolution,
                                    xlim=xlim, mean=mean,
                                    v_std_step=v_std_step)

    # Evaluation of nans
    if nans_evaluation:
        nans_df = evaluate_nans(years)
        nans_df.to_csv(os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Daten/Twele/',
            'nans_evaluation.csv'))

    # Evaluation of duplicates
    if duplicates_evaluation:
        duplicates_dict = evaluate_duplicates(years)

    # Evaluation of error numbers - decide whether to execute:
    if error_numbers:
        error_numbers_total = []
        for year in years:
            error_numbers = get_error_numbers(year)
            error_numbers.to_csv(
                os.path.join(os.path.dirname(__file__),
                             '../../../User-Shares/Masterarbeit/Daten/Twele/',
                             'error_numbers_{}.csv'.format(year)))
            error_numbers_total.extend(error_numbers)
        sorted_error_numbers_total = pd.Series(
            pd.Series(error_numbers_total).unique()).sort_values()
        sorted_error_numbers_total.index = np.arange(
            len(sorted_error_numbers_total))
        sorted_error_numbers_total.to_csv(
            os.path.join(os.path.dirname(__file__),
                         '../../../User-Shares/Masterarbeit/Daten/Twele/',
                         'error_numbers_total.csv'.format(year)))
