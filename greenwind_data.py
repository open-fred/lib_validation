"""
The ``greenwind_data`` module contains functions to read and dump measured
feed-in time series from a GreenWind wind farm.

The following data is available (year 2015 and 2016) for the turbines of
3 wind farms:
- power output in kW
- wind speed in m/s
- wind direction in °  (only for two wind farms)
- nacelle position in °
- error code

Additionally the sum of the wind farm power output of each wind farm is
available. Apart from that, 'first row time series' depending on wind
directions (nacelle positions) can be fetched.

DateTimeIndex in 'UTC' time zone.

"""

# Imports from lib_validation
import visualization_tools
import tools

# Other imports
import pandas as pd
import numpy as np
import os
import pickle


def path_to(where='data', projects_location='~/rl-institut/'):
    """
    Creates path to data.

    where : str
        Specifies where path will point to. Default: 'data'.
    projects_location : str
        Location where 04_Projekte of rl-institut is mounted.
        Default: '~/rl-institut/'.

    """
    greenwind_location = '04_Projekte/163_Open_FRED/03-Projektinhalte/AP5 Einspeisezeitreihen/5.2 Wind/Daten_Twele/'
    if where == 'data':
        add = 'processed_data/'
    if where == 'errors':
        add = 'Error codes/'
    return os.path.join(projects_location, greenwind_location, add)

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
    df = pd.read_csv(os.path.join(path_to(where='data'), filename),
                     sep=',', decimal='.', index_col=0, parse_dates=True)
    return df


def get_greenwind_data(year, pickle_load=False, filename='greenwind_dump.p',
                       resample=True, threshold=None, plot=False, x_limit=None,
                       frequency='30T', pickle_dump=True, filter_errors=True,
                       print_error_amount=False,
                       error_amount_filename='error_amount.csv',
                       zero_row_to_nan=True, csv_dump=False):
    r"""
    Fetches GreenWind data.

    Parameters
    ----------
    year : integer
        Year to fetch.
    pickle_load : boolean
        If True data frame is loaded from the pickle dump if False the data is
        loaded from the original csv files. Default: False.
    filename : string
        Filename including path of pickle dump. Default: 'greenwind_dump.p'.
    resample : boolean
        If True the data will be resampled to the `frequency`. (mean power)
        Default: True.
    threshold : integer or None
        Number of minimum values (not nan) necessary for resampling.
        Default: None.
    plot : boolean
        If True each column of the data farme is plotted into a seperate
        figure. Default: False
    x_limit : list of floats or integers
        Values for xmin and xmax in case of `plot` being True and x limits
        wanted. Default: None.
    frequency : string
        Frequency attribute. Default: '30T'
    pickle_dump : boolean
        If True the data frame is dumped to `filename`. Default: True.
    filter_errors : boolean
        If True errors are filtered via the error code column. Default: True.
    print_error_amount : boolean
        If True amount of values set to nan due to error numbers are print for
        each turbine and wind farm (and printed to csv file). Default: False.
    error_amount_filename : string
        Filname including path of error amount data frame.
    zero_row_to_nan : boolean
        If True if turbine data only contains zeros at one time step these
        values are set to nan.
    csv_dump : boolean
        If True data is saved in csv file with the file name of `filename`.
        Default: False.

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
        # Convert index to DatetimeIndex and make time zone aware (UTC)
        greenwind_df.index = pd.to_datetime(greenwind_df.index).tz_localize(
            'UTC')
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
                os.path.join(path_to(where='errors'),
                             'errors.csv'))['error_numbers'].dropna().values
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
        # Set negative values to zero execpt from < 30 W
        power_columns = [column for column in list(greenwind_df) if
                         'power_output' in column]
        greenwind_df = handle_negative_values(greenwind_df,
                                              columns=power_columns,
                                              limit=-30)
        # Set power output of turbines above 5% higher of nominal power
        # (all 2 MW) to nan
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
        if csv_dump:
            greenwind_df.to_csv(filename.replace('.p', '.csv'))
    return greenwind_df


def get_first_row_turbine_time_series(year, filename_raw_data=None,
                                      pickle_load_raw_data=False,
                                      filter_errors=True,
                                      print_error_amount=False,
                                      pickle_filename='greenwind_first_row.p',
                                      pickle_load=False, frequency='30T',
                                      resample=True, threshold=None,
                                      case='all', exact_degrees=False,
                                      mean_wind_dir=False, bias=False,
                                      add_info=False, csv_dump=False):
    r"""
    Fetches GreenWind data of first row turbine depending on wind direction.

    Parameters
    ----------
    year : integer
        Year to fetch.
    filename_raw_data : string
        Filename including path of pickle dump from the
        :py:func:`~.get_greenwind_data` function.
    pickle_load_raw_data : boolean
        If True data frame in :py:func:`~.get_greenwind_data` is loaded from
        the pickle dump if False the data is loaded from the original csv
        files. Note: if True the frequency is the frequency of the pickel dump
        of the raw data. Default: False.
    filter_errors : Booelan
        If True errors are filtered via the error code column. Default: True.
    print_error_amount : boolean
        If True amount of values set to nan due to error numbers are print for
        each turbine and wind farm (and printed to csv file). Default: False.
    pickle_filename : string
        Filename including path of pickle dump.
    pickle_load : boolean
        If True data frame is loaded from the pickle dump if False the data
        frame is created. Default: False.
    frequency : string
        Frequency attribute.
    resample : boolean
        If True the data will be resampled to the `frequency`. Default: True.
    threshold : integer or None
        Number of minimum values (not nan) necessary for resampling.
        Default: None.
    case : string
        Decides on wind directions/wind turbines being used for the first row
        time series. Options: 'weather_wind_speed_3': only northern/western
        directions, 'wind_dir_real': uses wind directions istead of nacelle
        positions, 'weather_wind_speed_3_real', any other: default (nacelle
        positions, all wind directions). Default: 'all'.
    exact_degrees : boolean
        If True more exact degrees are used. However, no great difference was
        detected. Default: False.
    mean_wind_dir : boolean
        If True mean wind direction of considered wind turbines is used for
        the decision whether a wind turbine stands in the first row.
        Default: False.
    bias : boolean
        If True time steps are only considered if the bias of wind direction
        from mean wind direction <= 10°. Default: False.
    add_info : boolean
        If True info for evaulation is added to data frames. Default: False.
    csv_dump : boolean
        If True data is saved in csv file with the file name of `filename`.
        Default: False.

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
                        'wf_BS_12': (119, 119), 'wf_BS_13': (355.5, 360),
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
                        # 'wf_BS_12': (119, 119),
                        'wf_BS_13': (355.5, 360),
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
                        # 'wf_BE_1': (0, 90),  # bad correlation
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
            if add_info:
                # Add columns that are filled with information later
                green_wind_df['{}_turbine_first_row'.format(
                    wind_farm_name)] = ''
                green_wind_df['{}_wind_dir_first_row'.format(
                    wind_farm_name)] = ''
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
                # specified values in `turbine_dict`.
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
                         float(turbine_dict[wind_farm_name][
                             turbine_name][0])) &
                        (wind_dir <
                         float(turbine_dict[wind_farm_name][
                                   turbine_name][1]))].index
                # Add temporary wind speed column with only nans
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
                if add_info:
                    # Add information about which turbine was used for which
                    # time step and the wind direction measured at that turbine
                    green_wind_df['{}_turbine_first_row'.format(
                        wind_farm_name)].loc[indices] += turbine_name
                    green_wind_df['{}_wind_dir_first_row'.format(
                        wind_farm_name)].loc[indices] += green_wind_df[
                            '{}_{}'.format(turbine_name,
                                           wind_dir_string)].apply(str)
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
            if add_info:
                cols = ['{}_wind_speed'.format(wind_farm_name),
                        '{}_power_output'.format(wind_farm_name),
                        '{}_turbine_first_row'.format(wind_farm_name),
                        '{}_wind_dir_first_row'.format(wind_farm_name)]
            else:
                cols = ['{}_wind_speed'.format(wind_farm_name),
                        '{}_power_output'.format(wind_farm_name)]
            first_row_df = pd.concat([first_row_df, green_wind_df[cols]],
                                     axis=1)
        pickle.dump(first_row_df, open(pickle_filename, 'wb'))
        if csv_dump:
            first_row_df.to_csv(pickle_filename.replace('.p', '.csv'))
    if resample:
        first_row_df = tools.resample_with_nan_theshold(
            df=first_row_df, frequency=frequency, threshold=threshold)
    else:
        # Add frequency attribute
        freq = pd.infer_freq(first_row_df.index)
        first_row_df.index.freq = pd.tseries.frequencies.to_offset(freq)
    return first_row_df


def error_numbers_from_df(df):
    """
    Fetches error numbers of time series from data frame.

    """
    error_numbers = []
    for column_name in list(df):
        if 'error_number' in column_name:
            error_numbers.extend(df[column_name].unique())
    sorted_error_numbers = pd.Series(
        pd.Series(error_numbers).unique()).sort_values()
    sorted_error_numbers.index = np.arange(len(sorted_error_numbers))
    return sorted_error_numbers


def get_error_numbers(year):
    """
    Fetches error numbers of time series and sorts them.

    """
    df = get_greenwind_data(year=year, resample=False,
                            pickle_load=False, pickle_dump=False)
    sorted_error_numbers = error_numbers_from_df(df)
    return sorted_error_numbers


def handle_negative_values(df, columns, limit):
    """
    Sets negative values up to `limit` to zero, values below `limit` to nan.

    """
    if columns is None:
        columns = [column for column in list(df)]
    for column in columns:
        indices = df.loc[df[column] < 0.0].index
        indices_2 = df[column].loc[indices].loc[df[column] >= limit].index
        df[column].loc[indices_2] = 0.0
        indices_3 = indices[~indices.isin(indices_2)]
        df[column].loc[indices_3] = np.nan
    return df

if __name__ == "__main__":
    csv_dump = True
    # Select cases: (parameters below in section)
    load_data = True
    evaluate_first_row_turbine = True
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
        frequency = 'H'
        threshold = 3  # Original resolution is 10 min
        # Decide whether to filter out time steps with error codes
        # (error code 0 and error codes that are not an error but a warning are
        # not filtered) and whether to print the amount of time steps being
        # filtered
        filter_errors = True
        zero_row_to_nan = True  # Filter time steps where all measured values
                                # of a wind farm are zero.
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
                    path_to(where='errors'),
                    'filtered_error_amount_{}.csv'.format(year))
                df = get_greenwind_data(
                    year=year, resample=resample,
                    frequency=frequency, threshold=threshold,
                    filename=filename, filter_errors=filter_errors,
                    print_error_amount=False,
                    error_amount_filename=error_amount_filename,
                    zero_row_to_nan=zero_row_to_nan, csv_dump=csv_dump)


    # ----- First row turbine -----#
    if evaluate_first_row_turbine:
        # Parameters
        cases = [
            # 'wind_dir_real',
            'wind_speed_1',
            # 'weather_wind_speed_3',
            # 'weather_wind_speed_3_real'
        ]
        first_row_resample = True
        first_row_frequency = 'H'
        first_row_threshold = 3
        first_row_filter_errors = True
        first_row_print_error_amount = False
        first_row_print_error_amount_total = False # only with pickle_load_raw_data False!
        pickle_load_raw_data = True
        exact_degrees = False
        mean_wind_dir = False  # Use mean wind direction (of correlating wind directions) instead of single turbine wind directions
        bias = False
        add_info = False  # Add info about which turbines were used for the respective time steps
        if add_info:
            resample = False
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
                if add_info:
                    pickle_filename = pickle_filename.replace('.p', 'with_info.p')
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
                    exact_degrees=exact_degrees, mean_wind_dir=mean_wind_dir,
                    add_info=add_info, csv_dump=csv_dump)

        if (first_row_print_error_amount_total and
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

    # Evaluation of error numbers - decide whether to execute:
    if error_numbers:
        error_numbers_total = []
        for year in years:
            error_numbers = get_error_numbers(year)
            error_numbers.to_csv(
                os.path.join(path_to(where='errors'),
                             'error_numbers_{}.csv'.format(year)))
            error_numbers_total.extend(error_numbers)
        sorted_error_numbers_total = pd.Series(
            pd.Series(error_numbers_total).unique()).sort_values()
        sorted_error_numbers_total.index = np.arange(
            len(sorted_error_numbers_total))
        sorted_error_numbers_total.to_csv(
            os.path.join(path_to(where='errors'),
                         'error_numbers_total.csv'.format(year)))
