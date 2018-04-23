"""
The ``argenetz_data`` module contains functions to read and dump measured
feed-in time series from ArgeNetz wind farms.

The following data is available for 5 wind farms (year 2015) or 4 wind farms
(year 2016):
- measured feed-in (power) [kW]
- wind speed [m/s]
- wind direction
- theoretical power [kW]
- installed power [kW]

The time stamps are in local time 'Europe/Berlin'.

"""

# Imports from Windpowerlib
from windpowerlib import wind_turbine as wt
from windpowerlib import power_output

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
import sys


# for other validation data modules, too
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
    if 'datapath' not in kwargs:
        kwargs['datapath'] = os.path.join(os.path.dirname(__file__),

                                          'data/ArgeNetz')
    if 'usecols' not in kwargs:
        kwargs['usecols'] = None

    df = pd.read_csv(os.path.join(kwargs['datapath'], filename), sep=';',
                     decimal=',', thousands='.', index_col=0,
                     usecols=kwargs['usecols'])
    return df


def restructure_data(filename, filename_column_names=None, filter_cols=False,
                     drop_na=False, **kwargs):
    r"""
    Restructures data read from a csv file.

    Creates a DataFrame. Data is filtered (if filter_cols is True) and
    Nan's are dropped (if drop_na is True).

    Parameters:
    -----------
    filename : string
        Name of data file.
    filename_column_names : string, optional
        Name of file that contains column names to be filtered for.
        Default: None.
    filter_cols : list
        Column names to filter for. Default: None.
    drop_na : boolean
        If True: Nan's are dropped from DataFrame with method how='any'.
        Default: None.

    Other Parameters
    ----------------
    datapath : string, optional
        Path to the location of the data file. Needed for read_data().
        Default: './data'

    """
    df = read_data(filename, **kwargs)
    if filter_cols:
        cols = read_file_to_list(filename_column_names)
        df = df.filter(items=cols, axis=1)
    if drop_na:
        df = df.dropna(axis='columns', how='all')
    return df


def read_file_to_list(filename):
    list = []
    with open(filename) as file:
        for line in file:
            line = line.strip()
            list.append(line)
    return list

def new_column_names(year):
    """
    Returns column names for ArgeNetz data depending on the year as list.

    """
    if year == 2015:
        new_column_names = [
            'wf_1_power_output', 'wf_1_theoretical_power', 'wf_1_wind_speed',
            'wf_1_wind_dir', 'wf_1_installed_power', 'wf_2_power_output',
            'wf_2_theoretical_power', 'wf_2_installed_power',
            'wf_3_power_output', 'wf_3_theoretical_power', 'wf_4_power_output',
            'wf_4_theoretical_power', 'wf_4_wind_speed', 'wf_5_power_output',
            'wf_5_installed_power', 'wf_5_theoretical_power']
#        new_column_names = [
#           'wf_1_power_output', 'wf_1_wind_speed', 'wf_1_installed_power',
#           'wf_2_power_output', 'wf_2_installed_power', 'wf_3_power_output',
#           'wf_3_wind_speed', 'wf_4_power_output', 'wf_4_wind_speed',
#           'wf_5_power_output', 'wf_5_installed_power']
    if (year == 2016 or year == 2017):
        new_column_names = [
            'wf_1_power_output', 'wf_1_theoretical_power', 'wf_1_wind_speed',
            'wf_1_wind_dir', 'wf_1_installed_power', 'wf_3_power_output',
            'wf_3_theoretical_power', 'wf_3_wind_speed', 'wf_3_wind_dir',
            'wf_3_installed_power', 'wf_4_power_output',
            'wf_4_theoretical_power', 'wf_4_wind_speed', 'wf_4_wind_dir',
            'wf_4_installed_power', 'wf_5_power_output',
            'wf_5_theoretical_power', 'wf_5_wind_speed', 'wf_5_wind_dir',
            'wf_5_installed_power']
#        new_column_names = [
#           'wf_1_power_output', 'wf_1_wind_speed', 'wf_1_installed_power',
#           'wf_3_power_output', 'wf_3_wind_speed', 'wf_3_installed_power',
#           'wf_4_power_output', 'wf_4_wind_speed', 'wf_4_installed_power',
#           'wf_5_power_output', 'wf_5_wind_speed', 'wf_5_installed_power']
    return new_column_names


def get_data(filename_files, year, filename_pickle='pickle_dump.p',
             pickle_load=False, filter_interpolated_data=True):
    r"""
    Fetches data of the requested files and renames columns.

    Parameters
    ----------
    filename_files : String
        Filename of file containing filenames of csv file to be read.
    year : Integer
        Year of data to be fetched.

    Returns
    -------
    df : pandas.DataFrame
        Data of ArgeNetz wind farms with readable column names.

    """
    path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        'dumps/validation_data',
                                        filename_pickle))
    if pickle_load:
        df = pickle.load(open(path, 'rb'))
    else:
        if year == 2015:
            filename_column_names = 'helper_files/column_names_2015.txt'
            replace = 'PT5M'
        if (year == 2016 or year == 2017):
            filename_column_names = 'helper_files/column_names_2016_2017.txt'
            replace = 'PT1M'
        with open(filename_files) as file:
            df = pd.DataFrame()
            for line in file:
                name = line.strip()
                df_part = restructure_data(name, filename_column_names,
                                           filter_cols=True)
                df_part.rename(columns={
                    old_name: new_name for old_name, new_name in
                    zip(read_file_to_list(filename_column_names),
                        new_column_names(year))},
                               inplace=True)
                df = pd.concat([df, df_part])
        # Convert string index to Datetime index
        df.index = [
            pd.to_datetime(index.replace(replace, ''), utc=True) for
            index in df.index]
        # Convert to local time zone
        df.index = df.index.tz_convert('Europe/Berlin')
        if year == 2016:
            # Get one wind farm from different data set
            file_dir = os.path.join(os.path.dirname(__file__),
                                'data/ArgeNetz/single_turbines/wf_2')
            df_wf_2 = pd.DataFrame()
            filenames = [filename for filename in os.listdir(
                            os.path.join(sys.path[0], file_dir)) if
                         filename.startswith('2016')]
            for filename in filenames:
                df_part = restructure_data(
                    filename, filter_cols=True,
                    filename_column_names='helper_files/column_names_2016_wf_2.txt',
                    datapath=file_dir)
                df_wf_2 = pd.concat([df_wf_2, df_part])
            # Rename columns
            old_names = list(df_wf_2)
            new_names = []
            for old_name in old_names:
                if ('Elektrische Wirkleistung' in old_name and
                            'Nordstrand ::' in old_name):
                    string = 'power_output'
                elif ('Windgeschwindigkeit' in old_name and
                              'Nordstrand ::' in old_name):
                    string = 'wind_speed'
                elif ('Windrichtung (' in old_name and
                              'Nordstrand ::' in old_name):
                    # Bracket is necessary as also 'Windrichtung relativ zur
                    # Gondelposition' exists
                    string = 'wind_dir'
                else:
                    string = 'drop_col'
                new_names.append('wf_2_{}'.format(string))
            df_wf_2.rename(columns={
                old_name: new_name for old_name, new_name in
                zip(old_names, new_names)},
                           inplace=True)
            df_wf_2.drop([col for col in list(df_wf_2) if 'drop_col' in col],
                         inplace=True)
            # Convert string index to Datetime index
            df_wf_2.index = [pd.to_datetime(index.replace(replace, ''), utc=True) for
                             index in df_wf_2.index]
            # Set time zone
            df_wf_2.index = df_wf_2.index.tz_convert('Europe/Berlin')
            df = pd.concat([df, df_wf_2], axis=1)
        # Add frequency attribute
        freq = pd.infer_freq(df.index)
        df.index.freq = pd.tseries.frequencies.to_offset(freq)
        if filter_interpolated_data:
            print('---- The interpolated data of ArgeNetz data in {0} '.format(
                      year) + 'is being filtered. ----')
            df_corrected = df.copy()
            for column_name in list(df):
                if 'power_output' in column_name:
                    df_corrected[column_name] = tools.filter_interpolated_data(
                        df[column_name], window_size=10, tolerance=0.0011,
                        replacement_character=np.nan, plot=False)
            df = df_corrected
            print('---- Filtering of {0} Done. ----'.format(year))
        pickle.dump(df, open(path, 'wb'))
    return df


def wf_2_single_data(pickle_filename='single_data.p', pickle_load=False,
                     filter_interpolated_data=True):
    year = 2016
    if pickle_load:
        df_wf_2 = pickle.load(open(pickle_filename, 'rb'))
    else:
        # Get data
        file_dir = os.path.join(os.path.dirname(__file__),
                                'data/ArgeNetz/single_turbines/wf_2')
        df_wf_2 = pd.DataFrame()
        filenames = [filename for filename in os.listdir(
            os.path.join(sys.path[0], file_dir)) if
                     filename.startswith('2016')]
        for filename in filenames:
            df_part = restructure_data(
                filename, filter_cols=True,
                filename_column_names='helper_files/column_names_2016_wf_2.txt',
                datapath=file_dir)
            df_wf_2 = pd.concat([df_wf_2, df_part])
        # Rename columns
        old_names = [col for col in list(df_wf_2) if 'Nordstrand ::' not in col]
        new_names = []
        aliases = {'NordstranderWind_E21897010000000000000000000100001': '1',
                   'Morsumkoog_E21897010000000000000000000100002': '2',
                   'Uthlander_WP_E21897010000000000000000000100003': '3',
                   'Uthlander_WP_2_E21897010000000000000000000100004': '4',
                   'Uthlander_WP_3_E21897010000000000000000000100005': '5',
                   'Botterkooger_WP_E21897010000000000000000000100006': '6'}
        for old_name in old_names:
            turbine_name = old_name.split(' ')[0]
            if 'Elektrische Wirkleistung' in old_name:
                string = 'power_output'
            elif 'Windgeschwindigkeit' in old_name:
                string = 'wind_speed'
            elif 'Windrichtung (' in old_name:
                # Bracket is necessary as also 'Windrichtung relativ zur
                # Gondelposition' exists
                string = 'wind_dir'
            else:
                string = 'drop_col'
            new_names.append('wf_2_{}_{}'.format(aliases[turbine_name], string))
        df_wf_2.rename(columns={
            old_name: new_name for old_name, new_name in
            zip(old_names, new_names)},
                       inplace=True)
        df_wf_2.drop([col for col in list(df_wf_2) if 'drop_col' in col],
                     inplace=True)
        # Convert string index to Datetime index
        df_wf_2.index = [pd.to_datetime(index.replace('PT1M', ''), utc=True) for
                         index in df_wf_2.index]
        # Set time zone
        df_wf_2.index = df_wf_2.index.tz_convert('Europe/Berlin')
        if filter_interpolated_data:
            print('---- The interpolated data of ArgeNetz data in {0} '.format(
                      year) + 'is being filtered. ----')
            df_corrected = df_wf_2.copy()
            for column_name in list(df_wf_2):
                if 'power_output' in column_name:
                    df_corrected[column_name] = tools.filter_interpolated_data(
                        df_wf_2[column_name], window_size=10, tolerance=0.0011,
                        replacement_character=np.nan, plot=False)
            df_wf_2 = df_corrected
            print('---- Filtering of {0} Done. ----'.format(year))
        pickle.dump(df_wf_2, open(pickle_filename, 'wb'))
    return df_wf_2

def data_evaluation(filename, csv_print=True):
    """
    Evaluate the data in terms of which data series exist of which farm for
    which year.

    Parameters:
    -----------
    filename : string
        Name of file that contains names of files to be evaluated.
    csv_print : boolean
        Decision whether to print resulting data frame to csv file.

    """
    ########## ATTENTION: not working at the moment!!! ##########
    # Initialise pandas.DataFrame
    df_compare = pd.DataFrame()
    # Read file and add to DataFrame for each line (= filenames)
    with open(filename) as file:
            for line in file:
                name = line.strip()
                df = restructure_data(name, drop_na=True)
                df2 = pd.DataFrame(data=df, index=list(df),
                                   columns=[name])
                df_compare = pd.concat([df_compare, df2], axis=1)
    if csv_print:
        df_compare.to_csv('evaluation.csv')
    return df_compare


def plot_argenetz_data(df, save_folder, y_limit=None, x_limit=None):
    r"""
    Plot all data from DataFrame to single plots and save them.

    Parameters:
    -----------
    df : pandas.DataFrame
        Contains data to be plotted.
    y_limit, x_limit : list of floats or integers
        Values for ymin, ymax, xmin and xmax

    """
    for column in df.columns:
        fig = plt.figure(figsize=(8, 6))
        df[column].plot()
        plt.title(column, fontsize=20)
        plt.xticks(rotation='vertical')
        if y_limit:
            plt.ylim(ymin=x_limit[0], ymax=y_limit[1])
        if x_limit:
            plt.xlim(xmin=x_limit[0], xmax=x_limit[1])
        plt.tight_layout()
        fig.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 '../Plots', save_folder,
                                                 str(column) + '.pdf')))
    plt.close()


def get_argenetz_data(year, pickle_load=False, filename='pickle_dump.p',
                      csv_load=False, csv_dump=True,
                      filter_interpolated_data=True, plot=False, x_limit=None):
    r"""
    Fetches ArgeNetz data for specified year and plots feedin.

    year : Integer
        Desired year to get the data for.
    pickle_load : Boolean
        If True data frame is loaded from the pickle dump if False the data is
        loaded from the original csv files (or from smaller csv file that was
        created in an earlier run if `csv_load` is True).
        Either set `pickle_load` or `csv_load` to True. Default: False.
    filename : String
        Filename including path of pickle dump. Default: 'pickle_dump.p'.
    csv_load : Boolean
        If True the data is loaded from a csv file that was created in an
        earlier run, if False the data is loaded from the original csv files
        from ArgeNetz (or loaded by pickle if `pickle_load` is True).
        Either set `pickle_load` or `csv_load` to True. Default: False
    csv_dump : Boolean
        If True the data is written into a csv file. Default: True
    filter_interpolated_data : Boolean
        If True the interpolated data (indicator for missing data) is filtered.
        The missing values are set to None. Default: True.
    plot : Boolean
        If True each column of the data farme is plotted into a seperate
        figure. Default: False
    x_limit : list of floats or integers
        Values for xmin and xmax in case of `plot` being True and x limits
        wanted. Default: None.

    Returns
    -------
    argenetz_df : pandas.DataFrame
        Data of ArgeNetz wind farms with readable column names (see function
        get_data()).
    """
    if pickle_load:
        argenetz_df = pickle.load(open(filename, 'rb'))
    elif csv_load:
        argenetz_df = pd.read_csv(filename.replace('.p', '.csv'))
    else:
        # Load data with get_data(); data frame is dumped in this function
        argenetz_df = get_data('helper_files/filenames_{0}.txt'.format(year),
                               year, filename, pickle_load=pickle_load,
                               filter_interpolated_data=filter_interpolated_data)
    if csv_dump:
        argenetz_df.to_csv(filename.replace('.p', '.csv'))
    if plot:
        plot_argenetz_data(
            argenetz_df, save_folder='ArgeNetz/Plots_{0}'.format(
                year), x_limit=x_limit)
    return argenetz_df


def check_theoretical_power(df, year, start=None, end=None):
    r"""
    This function was used to compare the theoretical power of ArgeNetz wind
    farms with the simulated power when the measured wind speed (of ArgeNetz
    data) is used.

    As no wind speed is added to the data of 2015 this function can only be
    used for the year 2015.

    """
    wind_farm_names = ['wf_1', 'wf_3', 'wf_4', 'wf_5']
    wind_turbine_amount = [(0, 16), (4, 13), (0, 22), (0, 14)]
    # Turbine data
    enerconE70 = {
        'turbine_name': 'ENERCON E 70 2300',
        'hub_height': 64,  # in m
        'rotor_diameter': 71  # in m
    }
    enerconE66 = {
        'turbine_name': 'ENERCON E 66 1800',
        'hub_height': 65,  # in m
        'rotor_diameter': 70  # in m
        }
    # Initialize WindTurbine objects
    e70 = wt.WindTurbine(**enerconE70)
    e66 = wt.WindTurbine(**enerconE66)
    for name, turbine_amount in zip(wind_farm_names, wind_turbine_amount):
        indices = tools.get_indices_for_series(1, 'Europe/Berlin', year)
        power_output_theo = df[name + '_theoretical_power'] / 1000
        power_output_theo = pd.Series(data=power_output_theo.values,
                                      index=indices)
        power_output_by_wind_speed = (
            turbine_amount[0] * power_output.power_curve(
                df[name + '_wind_speed'], e66.power_curve['wind_speed'],
                e66.power_curve['power']) +
            turbine_amount[1] * power_output.power_curve(
                df[name + '_wind_speed'], e70.power_curve['wind_speed'],
                e70.power_curve['power'])) / (1*10**6)
        power_output_by_wind_speed = pd.Series(
            data=power_output_by_wind_speed.values, index=indices)
        val_obj = analysis_tools.ValidationObject(
            'validate_arge_4919', power_output_theo,
            power_output_by_wind_speed,
            weather_data_name='calculated by wind speed',
            validation_name='P_W theoretical')
        val_obj.output_method = 'power_output'
        visualization_tools.plot_feedin_comparison(
            val_obj, filename='../Plots/Test_Arge/{0}_{1}_feedin'.format(
                year, name),
            title='{0}'.format(name), start=start, end=end)
        visualization_tools.plot_correlation(
            val_obj, filename='../Plots/Test_Arge/{0}_{1}_corr'.format(
                year, name),
            title='{0}'.format(name))


def correlation_of_wind_speed_and_power(year):
    # Get ArgeNetz Data
    pickle_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'dumps/validation_data',
                     'arge_netz_data_{0}.p'.format(year)))
    arge_netz_data = get_argenetz_data(year, pickle_load=True,
                                       filename=pickle_path, plot=False)
    if year == 2015:
        wind_farm_names = ['wf_1', 'wf_4']
    if year == 2016:
        wind_farm_names = ['wf_1', 'wf_3', 'wf_4', 'wf_5']
    for wind_farm_name in wind_farm_names:
        df = arge_netz_data[['{0}_power_output'.format(wind_farm_name),
                             '{0}_wind_speed'.format(wind_farm_name)]]
        df.corr().to_csv(os.path.join(os.path.dirname(__file__),
                         'Evaluation/argenetz/',
                         'correlation_wind_speed_power_{0}_{1}.csv'.format(
                             wind_farm_name, year)))

if __name__ == "__main__":
    years = [
        2015,
        2016
        ]  # possible: 2015, 2016, 2017
    # Get Arge Netz data
    for year in years:
        pickle_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'dumps/validation_data',
                         'arge_netz_data_{0}.p'.format(year)))
        get_argenetz_data(
            year,
            pickle_load=False,  # Load power output from former pickle dump
            filename=pickle_path,  # Path and filename for pickle dump and load
            csv_load=False,  # Load saved power output data frame from csv
            csv_dump=True,  # Save power output data frame in csv file
            plot=False)  # Plot each column of dataframe

# Other parameters:
#    evaluate_data = False  # Check which variables are given for which farm
    correlation_wind_power = False
    check_theo_power = False  # theoretical power against wind speed if True
    wf_2_single = True

    if wf_2_single:
        wf_2_single_data(
            pickle_filename=os.path.join(
                os.path.dirname(__file__), 'dumps/validation_data',
                'wf_SH_single.p'), filter_interpolated_data=True)

    if correlation_wind_power:
        years = [2015, 2016]
        for year in years:
            correlation_of_wind_speed_and_power(year)
#    if evaluate_data:
#        # Filenames: filenames_all.txt, filenames_2016.txt,.. see helper_files
#        df_compare = data_evaluation('helper_files/filenames_2016.txt')
#     if check_theo_power:
#         year = 2016  # dont use 2015 - no wind speed!
#         start = None
#         end = None
#         # Get ArgeNetz Data
#         arge_netz_data = get_argenetz_data(
#             year, pickle_load=True, filename=pickle_path, plot=False)
#         check_theoretical_power(arge_netz_data, year, start, end)
#         print("Plots for comparing theoretical power with simulated power " +
#               "(measured wind speed) are saved in 'Plots/Test_Arge'")
