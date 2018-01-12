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
import os
import pickle


# TODO: move read_data and restructure_data to tools module to be free to use
# for other validation data modules, too
def read_data(filename, **kwargs):
    r"""
    Fetches data from a csv file.

    Parameters
    ----------
    filename : string, optional
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
                                          'data')
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
        filter_cols = []
        with open(filename_column_names) as file:
            for line in file:
                line = line.strip()
                filter_cols.append(line)
        df2 = df.filter(items=filter_cols, axis=1)
    if drop_na:
        df2 = df.dropna(axis='columns', how='all')
    return df2


def get_data(filename_files, filename_column_names, new_column_names,
             filename_pickle='pickle_dump.p', pickle_load=False):
    r"""
    Fetches data of the requested files and renames columns.

    Parameters
    ----------
    filename_files : String
        Filename of file containing filenames of csv file to be read.
    filename_column_names : string, optional
        Name of file that contains column names to be filtered for.
        Default: None.
    new_column_names : List
        Contains new column names (Strings) for the data frame.

    Returns
    -------
    data : pandas.DataFrame
        Data of ArgeNetz wind farms with readable column names.

    """
    path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        'dumps/validation_data',
                                        filename_pickle))
    if not pickle_load:
        with open(filename_files) as file:
            data = pd.DataFrame()
            for line in file:
                name = line.strip()
                df = restructure_data(name, filename_column_names,
                                      filter_cols=True)
                df.columns = new_column_names
                data = pd.concat([data, df])  # data could also be dictionary
        pickle.dump(data, open(path, 'wb'))
    if pickle_load:
        data = pickle.load(open(path, 'rb'))
    return data


def data_evaluation(filename, csv_print=True):
    """
    Evaluate the data in terms of which variables are given for each dataset.

    Parameters:
    -----------
    filename : string
        Name of file that contains names of files to be evaluated.
    csv_print : boolean
        Decision whether to print resultating data frame to csv file.

    """
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

#new_column_names_2016_2017 = [
#    'wf_1_P_W', 'wf_1_v_wind', 'wf_1_P_W_inst', 'wf_3_P_W', 'wf_3_v_wind',
#    'wf_3_P_W_inst', 'wf_4_P_W', 'wf_4_v_wind', 'wf_4_P_W_inst', 'wf_5_P_W',
#    'wf_5_v_wind', 'wf_5_P_W_inst']
#
#new_column_names_2015 = [
#    'wf_1_P_W', 'wf_1_v_wind', 'wf_1_P_W_inst', 'wf_2_P_W', 'wf_2_P_W_inst',
#    'wf_3_P_W', 'wf_3_v_wind', 'wf_4_P_W', 'wf_4_v_wind', 'wf_5_P_W',
#    'wf_5_P_W_inst']
#df_compare = data_evaluation('helper_files/filenames_all.txt')

new_column_names_2016_2017 = [
    'wf_1_P_W', 'wf_1_P_W_theo', 'wf_1_v_wind', 'wf_1_wind_dir',
    'wf_1_P_W_inst', 'wf_3_P_W', 'wf_3_P_W_theo', 'wf_3_v_wind',
    'wf_3_wind_dir', 'wf_3_P_W_inst', 'wf_4_P_W', 'wf_4_P_W_theo',
    'wf_4_v_wind', 'wf_4_wind_dir', 'wf_4_P_W_inst', 'wf_5_P_W',
    'wf_5_P_W_theo', 'wf_5_v_wind', 'wf_5_wind_dir', 'wf_5_P_W_inst']

new_column_names_2015 = [
    'wf_1_P_W', 'wf_1_P_W_theo', 'wf_1_v_wind', 'wf_1_wind_dir',
    'wf_1_P_W_inst', 'wf_2_P_W', 'wf_2_P_W_theo', 'wf_2_P_W_inst', 'wf_3_P_W',
    'wf_3_P_W_theo', 'wf_4_P_W', 'wf_4_P_W_theo', 'wf_4_v_wind', 'wf_5_P_W',
    'wf_5_P_W_inst', 'wf_5_P_W_theo']


def get_argenetz_data(year, pickle_load=False, plot=False, x_limit=None):
    r"""
    Fetches ArgeNetz data for specified year and plots feedin.

    Returns
    -------
    argenetz_df : pandas.DataFrame
        Data of ArgeNetz wind farms with readable column names (see function
        get_data()).
    """
    if year == 2015:
        filename_column_names = 'helper_files/column_names_2015.txt'
        new_column_names = new_column_names_2015
    if (year == 2016 or year == 2017):
        filename_column_names = 'helper_files/column_names_2016_2017.txt'
        new_column_names = new_column_names_2016_2017
    argenetz_df = get_data('helper_files/filenames_{0}.txt'.format(year),
                           filename_column_names, new_column_names,
                           'arge_data_{0}.p'.format(year),
                           pickle_load=pickle_load)
    if plot:
        plot_argenetz_data(
            argenetz_df, save_folder='ArgeNetz_power_output/Plots_{0}'.format(
                year), x_limit=x_limit)
    return argenetz_df


def check_arge_netz_data(df, year, start=None, end=None):
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
        power_output_theo = df[name + '_P_W_theo'] / 1000
        power_output_theo = pd.Series(data=power_output_theo.values,
                                      index=indices)
        power_output_by_wind_speed = (turbine_amount[0] * power_output.power_curve(
            df[name + '_v_wind'], e66.power_curve['wind_speed'],
            e66.power_curve['values']) +
            turbine_amount[1] * power_output.power_curve(
            df[name + '_v_wind'], e70.power_curve['wind_speed'],
            e70.power_curve['values'])) / (1*10**6)
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

if __name__ == "__main__":
    check_theo_power = False  # theoretical power against wind speed if True
    if check_theo_power:
        year = 2016  # dont use 2015 - no wind speed!
        start = None
        end = None
        # Get ArgeNetz Data
        arge_netz_data = get_argenetz_data(
            year, pickle_load=True, plot=False)
        check_arge_netz_data(arge_netz_data, year, start, end)
        print("Plots for comparing theoretical power with simulated power " +
              "(measured wind speed) are saved in 'Plots/Test_Arge'")

# Get the data of 2015 (and 2016/2017) and plot the results
#x_limit = None
#data_2015 = get_data('filenames_2015.txt', new_column_names_2015,
#                     'arge_data_2015.p', pickle_load=True)
#plot_argenetz_data(data_2015, save_folder='ArgeNetz_power_output/Plots_2015',
#          x_limit=x_limit)
#data_2016_2017 = get_data('filenames_2016_2017.txt',
#                          'column_names_2016_2017.txt',
#                          new_column_names_2016_2017, 'arge_data_2016_2017.p',
#                          pickle_load=True)
#plot_argenetz_data(data_2016_2017, save_folder='ArgeNetz_power_output/Plots_2016_2017',
#          x_limit=x_limit)

# Sample for period of 2015 (possible mistakes in data)
#data = get_data('filenames.txt', 'column_names_2015.txt',
#                 new_column_names_2015, 'arge_data_2015.p', pickle_load=True)
#x_limit = [10, 50]
#plot_argenetz_data(data, save_folder='Plots_2015_period', x_limit=x_limit)
