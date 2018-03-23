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

# Other imports
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
                       resample=True, threshold=None, plot=False, x_limit=None,
                       frequency='30T', pickle_dump=True, filter_errors=True,
                       print_error_amount=False,
                       error_amount_filename='error_amount.csv'):
    # TODO: add plots to check data
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
                             'errors.csv'))['error_numbers'].dropna().values  # nans?!
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
        print('---- Error filtering of {0} Done. ----'.format(year))
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
                                      resample=True, threshold=None):
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
        turbine_dict = {
            'wf_6': {
                'wf_6_1': (0, 90), 'wf_6_2': (270, 315), 'wf_6_4': (180, 225),
                'wf_6_5': (90, 180), 'wf_6_6': (315, 360),
                'wf_6_7': (225, 270)
                },
            'wf_7': {
                'wf_7_2': (225, 270), 'wf_7_5': (135, 180),
                'wf_7_7': (270, 360), 'wf_7_10': (180, 225),
                'wf_7_12': (90, 135), 'wf_7_14': (0, 90)
                },
            'wf_8': {
                'wf_8_1': (0, 180), 'wf_8_2': (180, 360)
                }}
        wind_farm_names = list(set(['_'.join(item.split('_')[0:2]) for
                                   item in turbine_dict]))
        first_row_df = pd.DataFrame()
        for wind_farm_name in wind_farm_names:
            for turbine_name in turbine_dict[wind_farm_name]:
                # Get indices of rows where wind direction lies between
                # specified values in `turbine_dict`.
                # Example for 'wf_6_1': 0 <= x < 90.
                indices = green_wind_df.loc[
                    (green_wind_df['{}_wind_dir'.format(
                        turbine_name)] >=
                        float(turbine_dict[wind_farm_name][turbine_name][0])) &
                    (green_wind_df['{}_wind_dir'.format(turbine_name)] <
                     float(
                         turbine_dict[wind_farm_name][turbine_name][1]))].index
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
                # Add wind speed of wind speed column for `indices`
                green_wind_df['power_output_temp_{}'.format(turbine_name)].loc[
                    indices] = green_wind_df['{}_power_output'.format(
                    turbine_name)].loc[indices]
            # Add power output and wind speed as mean from all temp columns
            wind_speed_columns = [
                column_name for column_name in list(green_wind_df) if
                'wind_speed_temp' in column_name]
            power_output_columns = [
                column_name for column_name in list(green_wind_df) if
                'power_output_temp' in column_name]
            green_wind_df['{}_wind_speed'.format(
                wind_farm_name)] = green_wind_df[wind_speed_columns].sum(
                axis=1, skipna=True)
            green_wind_df['{}_power_output'.format(
                wind_farm_name)] = green_wind_df[power_output_columns].sum(
                axis=1, skipna=True)
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


if __name__ == "__main__":
    # ----- Load data -----#
    load_data = True
    if load_data:
        years = [
            2015,
            2016
        ]
        # Decide whether to resample to a certain frequency with a certain
        # threshold
        resample = True
        frequency = '30T'
        threshold = 2
        # Decide whether to filter out time steps with error codes (not
        # filtered is: error code 0 and error codes that are not an error but
        # information) and whether to print the amount of time steps being
        # filtered
        filter_errors = True
        print_error_amount = True
        print_erroer_amount_total = True
        for year in years:
            filename = os.path.join(os.path.dirname(__file__),
                                    'dumps/validation_data',
                                    'greenwind_data_{0}.p'.format(year))
            error_amount_filename = os.path.join(
                os.path.dirname(__file__),
                '../../../User-Shares/Masterarbeit/Daten/Twele/',
                'filtered_error_amount_{}.csv'.format(year))
            df = get_greenwind_data(
                year=year, resample=resample,
                frequency=frequency, threshold=threshold,
                filename=filename, filter_errors=filter_errors,
                print_error_amount=print_error_amount)

        if print_erroer_amount_total and print_error_amount:
            filenames = [os.path.join(
                os.path.dirname(__file__),
                '../../../User-Shares/Masterarbeit/Daten/Twele/',
                'filtered_error_amount_{}.csv'.format(year)) for year in years]
            dfs = [pd.read_csv(filename, index_col=0).rename(
                columns={'amount': year}) for
                   filename, year in zip(filenames, years)]
            df = pd.concat(dfs, axis=1)
            error_amout_df = df.loc[['wf_6', 'wf_7', 'wf_8']]
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
    evaluate_first_row_turbine = True
    if evaluate_first_row_turbine:
        # Parameters
        years = [
            2015,
            2016
        ]
        first_row_resample = True
        first_row_frequency = '30T'
        first_row_threshold = 2
        first_row_filter_errors = True
        first_row_print_error_amount = False
        first_row_print_erroer_amount_total = False # only with pickle_load_raw_data False!
        pickle_load_raw_data = True
        for year in years:
            filename_raw_data = os.path.join(
                os.path.dirname(__file__), 'dumps/validation_data',
                'greenwind_data_{0}.p'.format(year))
            pickle_filename = os.path.join(
                os.path.dirname(__file__), 'dumps/validation_data',
                'greenwind_data_first_row_{0}.p'.format(year))
            error_amount_filename = os.path.join(
                os.path.dirname(__file__),
                '../../../User-Shares/Masterarbeit/Daten/Twele/',
                'filtered_error_amount__first_row{}.csv'.format(year))
            df = get_first_row_turbine_time_series(
                year=year, filename_raw_data=filename_raw_data,
                pickle_load_raw_data=pickle_load_raw_data,
                filter_errors=first_row_filter_errors,
                print_error_amount=first_row_print_error_amount,
                pickle_filename=pickle_filename, frequency=first_row_frequency,
                resample=first_row_resample, threshold=first_row_threshold)

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
            error_amout_df = df.loc[['wf_6', 'wf_7', 'wf_8']]
            error_amout_df.rename(index={ind: ind.replace('wf_', 'WF ') for
                                         ind in error_amout_df.index})
            error_amout_df.to_csv(os.path.join(
                os.path.dirname(__file__),
                '../../../User-Shares/Masterarbeit/Daten/Twele/',
                'filtered_error_amount_years_first_row.csv'))


    # Evaluation of nans
    nans_evaluation = False
    if nans_evaluation:
        years = [
            2015,
            2016
        ]
        nans_df = evaluate_nans(years)
        nans_df.to_csv(os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Daten/Twele/',
            'nans_evaluation.csv'))

    # Evaluation of duplicates
    duplicates_evaluation = False
    if duplicates_evaluation:
        years = [
            2015,
            2016
        ]
        duplicates_dict = evaluate_duplicates(years)

    # Evaluation of error numbers - decide whether to execute:
    error_numbers = False
    if error_numbers:
        years = [
            2015,
            2016
        ]
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
