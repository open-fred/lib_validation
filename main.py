# Imports from Windpowerlib
from windpowerlib import wind_farm as wf

# Imports from lib_validation
import visualization_tools
import analysis_tools
import tools
import latex_tables
import modelchain_usage
from wind_farm_specifications import (get_joined_wind_farm_data,
                                      get_wind_farm_data)
from merra_weather_data import get_merra_data
from open_fred_weather_data import get_open_fred_data
from argenetz_data import get_argenetz_data
from enertrag_data import get_enertrag_data
from analysis_tools import ValidationObject

# Other imports
import os
import pandas as pd
import numpy as np
import pickle

# ----------------------------- Set parameters ------------------------------ #
year = 2015
time_zone = 'Europe/Berlin'
min_periods_pearson = None  # Integer
# TODO: add logging info ?!

# Pickle load time series data frame - if one of the above pickle_load options
# is set to False, `pickle_load_time_series_df` is automatically set to False
pickle_load_time_series_df = True

pickle_load_merra = True
pickle_load_open_fred = True
pickle_load_arge = True
pickle_load_enertrag = True
pickle_load_wind_farm_data = True

csv_load_time_series_df = False  # Load time series data frame from csv dump
csv_dump_time_series_df = False  # Dump df as csv

approach_list = [
    'simple',  # logarithmic wind profile, simple aggregation for farm output
    'density_correction',  # density corrected power curve, simple aggregation
    'smooth_wf'  # Smoothed power curves at wind farm level
    ]
weather_data_list = [
    'MERRA',
    'open_FRED'
    ]
validation_data_list = [
    'ArgeNetz',
    # 'Enertrag',
    # 'GreenWind'
    ]

output_methods = [
    'no_resample',  # Time series stay in the given temporal resolution
    'hourly',
    'monthly'
    ]

visualization_methods = [
#    'box_plots',
#    'feedin_comparison',
#    'plot_correlation'  # Attention: this takes a long time for high resolution
    ]

feedin_comparsion_all_in_one = False  # Plots all calculated series for one
                                      # wind farm in one plot

latex_output = np.array([
     'annual_energy_weather',  # Annual energy output of all weather sets
#     'annual_energy_approaches',  # ...
#     'annual_energy_weather_approaches',  # ...
    # 'key_figures_weather',     # Key figures of all weather sets
     'key_figures_approaches'  # Key figures of all approaches
     ])

# Select time of day you want to observe or None for all day
time_period = (
#       6, 22  # time of day to be selected (from h to h)
         None   # complete time series will be observed
        ) 

# Start and end date for time period to be plotted when 'feedin_comparison' is
# selected. (not for monthly output)
start_end_list = [
    (None, None),
#    ('{0}-10-01 11:00:00+00:00'.format(year), '{0}-10-01 16:00:00+00:00'.format(year)),
    ('{0}-10-01'.format(year), '{0}-10-03'.format(year))
    ]

extra_plots = np.array([
#    'annual_bars_weather'  # Bar plot of annual energy output for all weather data and years
    ])
# relative path to latex tables folder
latex_tables_folder = '../../../User-Shares/Masterarbeit/Latex/Tables/automatic/'

# Other plots
plot_arge_feedin = False  # If True plots each column of ArgeNetz data frame

# Filename specifications
validation_pickle_folder = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'dumps/validation_data'))
wind_farm_pickle_folder = os.path.join(os.path.dirname(__file__),
                                       'dumps/wind_farm_data')
time_series_df_folder = os.path.join(os.path.dirname(__file__),
                                     'dumps/time_series_dfs')

# Heights for which temperature of MERRA shall be calculated
temperature_heights = [60, 64, 65, 105, 114]

# Wind farms that will not be examined also if they are in the time series df
restriction_list = ['wf_3']

# If pickle_load options not all True:
if (not pickle_load_merra or not pickle_load_open_fred or not pickle_load_arge
        or not pickle_load_enertrag or not pickle_load_wind_farm_data):
    pickle_load_time_series_df = False


# -------------------------- Validation Feedin Data ------------------------- #
def get_validation_data(frequency):
    r"""
    Writes all measured power output time series into one DataFrame.

    All time series are resampled to the given frequency.

    Parameters
    ----------
    frequency : ...
        TODO add

    Returns
    -------
    validation_df : pd.DataFrame
        Measured power output in MW. Column names are as follows:
        'wf_1_measured', 'wf_2_measured', etc.

    """
    validation_df_list = []
    if 'ArgeNetz' in validation_data_list:
        # Get wind farm data
        wind_farm_data_arge = get_wind_farm_data(
            'farm_specification_argenetz_{0}.p'.format(year),
            wind_farm_pickle_folder, pickle_load_wind_farm_data)
        # Get ArgeNetz Data
        arge_data = get_argenetz_data(
            year, pickle_load=pickle_load_arge,
            filename=os.path.join(validation_pickle_folder,
                                  'arge_netz_data_{0}.p'.format(year)),
            csv_dump=False, plot=plot_arge_feedin)
        # Select only columns containing the power output and rename them
        arge_data = arge_data[['{0}_power_output'.format(data['object_name'])
                               for data in wind_farm_data_arge]].rename(
            columns={col: col.replace('power_output', 'measured') for col in
                     arge_data.columns})
        # Resample the DataFrame columns with `frequency` and add to list
        validation_df_list.append(arge_data.resample(frequency).mean())
    if ('Enertrag' in validation_data_list and year == 2016):
        # Get Enertrag Data
        enertrag_data = get_enertrag_data(
            pickle_load=pickle_load_enertrag,
            filename=os.path.join(validation_pickle_folder, 'enertrag_data.p'),
            resample=True, plot=False, x_limit=None)
        # Select aggregated power output of wind farm and rename
        enertrag_data = enertrag_data[['wf_9_power_output']].rename(
            columns={'wf_9_power_output': 'wf_9_measured'})
        # Resample the DataFrame columns with `frequency` and add to list
        validation_df_list.append(enertrag_data.resample(frequency).mean())
    if 'GreenWind' in validation_data_list:
        # Get GreenWind data
        pass
    # Join DataFrames - power output in MW
    validation_df = pd.concat(validation_df_list, axis=1) / 1000
    return validation_df


# ------------------------------ Wind farm data ----------------------------- #
def return_wind_farm_data():
        r"""
        Get wind farm data of all validation data.

        Returns
        -------
        List of Dictionaries
            Contains information about the wind farm.

        """
        filenames = ['farm_specification_{0}_{1}.p'.format(
            validation_data_name.replace('ArgeNetz', 'argenetz'), year)
            for validation_data_name in validation_data_list if
            validation_data_name is not 'Enertrag']
        if (year == 2016 and 'Enertrag' in validation_data_list):
            filenames += ['farm_specification_enertrag_2016.p']
        return get_joined_wind_farm_data(filenames, wind_farm_pickle_folder,
                                         pickle_load_wind_farm_data)


# ------------------------- Power output simulation ------------------------- #
def get_calculated_data(weather_data_name):
    r"""
    Calculates time series with different approaches.

    Data is saved in a DataFrame that can later be joined with the validation
    data frame.

    Parameters
    ----------
    weather_data_name : String
        Weather data for which the feed-in is calculated.

    Returns
    -------
    calculation_df : pd.DataFrame
        Calculated power output in MW. Column names are as follows:
        'wf_1_calculated_{0}'.format(approach) etc.

    """
    # Get weather data
    # Generate weather filename (including path) for pickle dumps (and loads)
    filename_weather = os.path.join(os.path.dirname(__file__), 'dumps/weather',
                                    'weather_df_{0}_{1}.p'.format(
                                        weather_data_name, year))
    # Read csv files that contains weather data (pd.DataFrame is dumped)
    # to save time below
    if weather_data_name == 'MERRA':
        if not pickle_load_merra:
            get_merra_data(year, heights=temperature_heights,
                           filename=filename_weather)
    if weather_data_name == 'open_FRED':
        if not pickle_load_open_fred:
            fred_path = os.path.join(
                os.path.dirname(__file__), 'data/open_FRED',
                'fred_data_{0}_sh.csv'.format(year))
            get_open_fred_data(
                filename=fred_path, pickle_filename=filename_weather,
                pickle_load=False)

    # Get wind farm data
    wind_farm_data_list = return_wind_farm_data()
    # Initialise calculation_df_list and calculate power output
    calculation_df_list = []
    for wind_farm_data in wind_farm_data_list:
        # Initialise wind farm
        wind_farm = wf.WindFarm(**wind_farm_data)
        # Get weather data for specific coordinates
        weather = tools.get_weather_data(
            weather_data_name, wind_farm.coordinates, pickle_load=True,
            filename=filename_weather, year=year,
            temperature_heights=temperature_heights)
        # Calculate power output and store in list
        if 'simple' in approach_list:
            calculation_df_list.append(modelchain_usage.power_output_simple(
                wind_farm.wind_turbine_fleet, weather).to_frame(
                    name='{0}_calculated_simple'.format(
                        wind_farm.object_name)))
        if 'density_correction' in approach_list:
            calculation_df_list.append(modelchain_usage.power_output_simple(
                wind_farm.wind_turbine_fleet, weather,
                density_correction=True).to_frame(
                    name='{0}_calculated_density_correction'.format(
                        wind_farm.object_name)))
        if 'smooth_wf' in approach_list:
            calculation_df_list.append(modelchain_usage.power_output_smooth_wf(
                wind_farm, weather, cluster=False, density_correction=False,
                wake_losses=False, smoothing=True, block_width=0.5,
                standard_deviation_method='turbulence_intensity').to_frame(
                    name='{0}_calculated_smooth_wf'.format(
                        wind_farm.object_name)))

    # Join DataFrames - power output in MW
    calculation_df = pd.concat(calculation_df_list, axis=1) / (1 * 10 ** 6)
    return calculation_df


def get_time_series_df(weather_data_name):
    r"""

    If there are any values in restriction_list, the columns containing these
    strings are dropped. This takes place after dumping.

    """
    time_series_filename = os.path.join(time_series_df_folder,
                                        'time_series_df_{0}_{1}.p'.format(
                                            weather_data_name, year))
    if pickle_load_time_series_df:
        time_series_df = pickle.load(open(time_series_filename, 'rb'))
    elif csv_load_time_series_df:
        time_series_df = pd.read_csv(time_series_filename.replace('.p',
                                                                  '.csv'))
        pickle.dump(time_series_df, open(time_series_filename, 'wb'))
    else:
        # Get validation and calculated data
        calculation_df = get_calculated_data(weather_data_name)
        validation_df = get_validation_data(calculation_df.index.freq)
        # Join data frames
        time_series_df = pd.concat([validation_df, calculation_df], axis=1)
        # Set value of measured series to nan if respective calculated value
        # is nan and the other way round
        column_name_lists = [
            [name for name in list(time_series_df) if wf_name in name] for
            wf_name in wind_farm_names]
        for column_name in column_name_lists:
            # Nans of calculated data to measured data
            time_series_df.loc[:, column_name[0]].loc[
                time_series_df.loc[:, column_name[1]].loc[
                    time_series_df.loc[
                        :, column_name[1]].isnull() == True].index] = np.nan
            # Nans of calculated data to measured data
            for i in range(len(column_name) - 1):
                time_series_df.loc[:, column_name[i+1]].loc[
                    time_series_df.loc[:, column_name[0]].loc[
                        time_series_df.loc[
                        :, column_name[0]].isnull() == True].index] = np.nan
        pickle.dump(time_series_df, open(time_series_filename, 'wb'))
    if csv_dump_time_series_df:
        time_series_df.to_csv(time_series_filename.replace('.p', '.csv'))
    # Drop columns that contain at least one item of `restriction_list` in
    # their name
    drop_list = []
    for restriction in restriction_list:
        drop_list.extend([column_name for column_name in list(time_series_df)
                          if restriction in column_name])
    time_series_df.drop([column_name for column_name in drop_list],
                        axis=1, inplace=True)
    return time_series_df


# ------------------------------ Helper functions --------------------------- #
def initialize_dictionary(dict_type, time_series_pairs=None):
    if dict_type == 'validation_objects':
        dictionary = {weather_data_name: {method: {approach: []
                                                   for approach in
                                                   approach_list}
                                          for method in output_methods}
                      for weather_data_name in weather_data_list}
    if dict_type == 'annual_energy':
        if (time_series_pairs is None):
            raise ValueError("`time_series_pairs` has to be given.")
        wf_strings = ['_'.join(list(time_series_pair)[0].split('_')[:2])
                      for time_series_pair in time_series_pairs]
        dictionary = {
            wf_string: {approach: {'energy': None,
                                   'deviation': None}
            # wf_string: {approach: {'energy [MWh]': None,
            #                        'deviation [%]': None}
                        for approach in approach_list}
            for wf_string in wf_strings}
    return dictionary


def join_dictionaries(list_of_dicts):
    # Start with copy of first entry
    z = list_of_dicts[0].copy()
    # Update with the remaining dictionaries
    for i in range(len(list_of_dicts) - 1):
        z.update(list_of_dicts[i + 1])
    return z


# ------------------------------ Data Evaluation ---------------------------- #
# Create list of wind farm names
wind_farm_names = [data['object_name'] for data in return_wind_farm_data()]
# Initialize dictionary for validation objects
val_obj_dict = initialize_dictionary(dict_type='validation_objects')
# Initialize dict for annual energy output of each weather data set
annual_energy_dicts = {weather_data_name: None
                       for weather_data_name in weather_data_list}
for weather_data_name in weather_data_list:
    time_series_df = get_time_series_df(weather_data_name)
    if (pickle_load_time_series_df or csv_load_time_series_df):
        # Check if all needed data exists
        pass  # TODO: add
    # Create list of time series data frames (for each wind farm for each
    # approach) - measured and calculated data
    time_series_df_parts = [
        time_series_df.loc[:, [
            column_name for column_name in list(time_series_df)
            if wf_name in column_name]] for wf_name in wind_farm_names
            if wf_name not in restriction_list]
    time_series_pairs = [time_series_df.loc[:, ['{0}_measured'.format(wf_name),
                                                '{0}_calculated_{1}'.format(
                                                    wf_name, approach)]]
                         for wf_name in wind_farm_names
                         for approach in approach_list
                         if '{0}_calculated_{1}'.format(
                             wf_name, approach) in list(time_series_df)]
    # Initialize dictionary for annual energy output
    annual_energy_dict_weather = initialize_dictionary(
        dict_type='annual_energy', time_series_pairs=time_series_pairs)
    if ('annual_energy_approaches' in latex_output
            or 'annual_energy_weather' in latex_output):
        # Write annual energy outputs and deviations into `annual_energy_dict`
        for time_series_df_part in time_series_df_parts:
            wf_string = '_'.join(list(time_series_df_part)[0].split('_')[:2])
            # Measured annual energy output
            measured_output = tools.annual_energy_output(
                time_series_df_part.loc[:, '{0}_measured'.format(wf_string)])
            annual_energy_dict_weather[
                wf_string]['measured_annual_energy'] = measured_output
            # Calculated annual energy output and deviation from measured in %
            for column_name in list(time_series_df_part):
                if column_name != '{0}_measured'.format(wf_string):
                    approach_string = '_'.join(column_name.split('_')[3:])
                    calculated_output = tools.annual_energy_output(
                        time_series_df_part.loc[:,'{0}_calculated_{1}'.format(
                            wf_string, approach_string)])
                    annual_energy_dict_weather[wf_string][
                        approach_string]['energy'] = (
                            calculated_output)
                    annual_energy_dict_weather[wf_string][
                        approach_string]['deviation'] = (
                            (calculated_output - measured_output) /
                            measured_output * 100)
                # annual_energy_dict_weather[wf_string][
                #     approach_string]['energy [MWh]'] = (
                #     calculated_output)
                # annual_energy_dict_weather[wf_string][
                #     approach_string]['deviation [%]'] = (
                #     (calculated_output - measured_output) /
                #     measured_output * 100)
        # Add dictionary to `annual_energy_dicts`
        annual_energy_dicts[weather_data_name] = annual_energy_dict_weather
    for time_series_pair in time_series_pairs:
        wf_string = '_'.join(list(time_series_pair)[0].split('_')[:2])
        approach_string = '_'.join(list(time_series_pair)[1].split('_')[3:])
        if 'no_resample' in output_methods:
            val_obj_dict[weather_data_name]['no_resample'][
                approach_string].append(ValidationObject(
                    object_name=wf_string, data=time_series_pair,
                    output_method='no_resample',
                    weather_data_name=weather_data_name,
                    approach=approach_string,
                    min_periods_pearson=min_periods_pearson))
        if 'hourly' in output_methods:
            hourly_series = time_series_pair.resample('H').mean()
            val_obj_dict[weather_data_name]['hourly'][
                approach_string].append(ValidationObject(
                    object_name=wf_string, data=time_series_pair,
                    output_method='hourly',
                    weather_data_name=weather_data_name,
                    approach=approach_string,
                    min_periods_pearson=min_periods_pearson))
        if 'monthly' in output_methods:
            monthly_series = time_series_pair.resample('M').mean()
            val_obj_dict[weather_data_name]['monthly'][
                approach_string].append(ValidationObject(
                    object_name=wf_string, data=time_series_pair,
                    output_method='monthly',
                    weather_data_name=weather_data_name,
                    approach=approach_string,
                    min_periods_pearson=min_periods_pearson))

    # Visualization #
    if 'feedin_comparison' in visualization_methods:
        # Specify folder and title add on for saving the plots
        if feedin_comparsion_all_in_one:
           plot_dfs = time_series_df_parts # TODO: test
           approach_string = 'multiple'
        else:
            plot_dfs = time_series_pairs
            approach_string = None
        for plot_df in plot_dfs:
            if time_period is not None:
                save_folder_add_on = (
                    '{0}_{1}/'.format(time_period[0], time_period[1]))
                title_add_on = ' time of day: {0}:00 - {1}:00'.format(
                    time_period[0], time_period[1])
            else:
                save_folder_add_on = 'None/'
                title_add_on = ''
            save_folder = 'Plots/{0}/{1}/{2}/time_period/{3}'.format(
                year, weather_data_name,
                '_'.join(list(plot_df)[1].split('_')[3:]),
                save_folder_add_on)
            for method in output_methods:
                method_string = (method if method is not 'no_resample'
                                 else 'hourly' if weather_data_name is 'MERRA'
                                 else 'half-hourly')
                if approach_string is None:
                    approach_string = '_'.join(list(plot_df)[1].split(
                        '_')[3:])
                wf_string = '_'.join(list(plot_df)[0].split(
                    '_')[:2])
                for start_end in start_end_list:
                    if (method == 'monthly' and start_end[0] is not None):
                        # Do not plot
                        pass
                    else:
                        visualization_tools.plot_feedin_comparison(
                            data=plot_df, method=method,
                            filename=(
                                save_folder +
                                '{0}_feedin_{1}_{2}_{3}_{4}_{5}{6}.png'.format(
                                    method_string,
                                    list(plot_df)[0].split('_')[0],
                                    weather_data_name, year, approach_string,
                                    (start_end[0].split(':')[0] if start_end[0]
                                     else ''), (start_end[1].split(':')[0]
                                                if start_end[0] else ''))),
                            title=(
                                '{0} power output of {1} calculated with {2} data\n in {3} ({4} approach)'.format(
                                    method_string, wf_string,
                                    weather_data_name, year, approach_string) +
                                title_add_on),
                            tick_label=None, start=start_end[0], end=start_end[1])


# --------------- OLD OLD OLD  Visualization of data evaluation -------------- #
# # Specify folder and title add on for saving the plots
# if time_period is not None:
#     save_folder = (
#         '../Plots/{0}/{1}_{2}/{3}/time_period/{4}_{5}/'.format(
#             year, weather_data_name, validation_data_name,
#             approach, time_period[0], time_period[1]))
#     title_add_on = ' time of day: {0}:00 - {1}:00'.format(
#         time_period[0], time_period[1])
# else:
#     save_folder = '../Plots/{0}/{1}_{2}/{3}/'.format(
#         year, weather_data_name, validation_data_name, approach)
#     title_add_on = ''
# # Use visualization methods for each validation set
# for validation_set in validation_sets:
#     if (validation_set[0].output_method is not
#             'annual_energy_output'):
#         if 'box_plots' in visualization_methods:
#             # Store all bias time series of a validation set in one
#             # DataFrame for Boxplot
#             bias_df = pd.DataFrame()
#             for validation_object in validation_set:
#                 if 'all' not in validation_object.object_name:
#                     df_part = pd.DataFrame(
#                         data=validation_object.bias,
#                         columns=[validation_object.object_name])
#                     bias_df = pd.concat([bias_df, df_part], axis=1)
#             # Specify filename
#             filename = (save_folder +
#                         '{0}_Boxplot_{1}_{2}_{3}_{4}.pdf'.format(
#                             validation_set[0].output_method, year,
#                             validation_data_name,
#                             weather_data_name, approach))
#             title = (
#                 'Deviation of ' +
#                 '{0} {1} from {2}\n in {3} ({4} approach)'.format(
#                     weather_data_name,
#                     validation_set[0].output_method.replace('_',
#                                                             ' '),
#                     validation_data_name, year, approach) +
#                 title_add_on)
#             visualization_tools.box_plots_bias(
#                 bias_df, filename=filename, title=title)
#
#         if 'feedin_comparison' in visualization_methods:
#         # TODO: rename this method for better understanding
#             if (start is None and end is None and
#                     validation_set[0].output_method
#                     is not 'monthly_energy_output'):
#                 filename_add_on = ''
#             else:
#                 filename_add_on = '_{0}_{1}'.format(start, end)
#             for validation_object in validation_set:
#                 filename = (
#                     save_folder +
#                     '{0}_{1}_Feedin_{2}_{3}_{4}_{5}{6}.png'.format(
#                         validation_set[0].output_method,
#                         validation_object.object_name, year,
#                         validation_data_name, weather_data_name,
#                         approach, filename_add_on))
#                 title = (
#                     '{0} of {1} and {2} in {3}\n {4} ({5} '.format(
#                         validation_set[0].output_method.replace(
#                             '_', ' '),
#                         weather_data_name, validation_data_name,
#                         validation_object.object_name, year,
#                         approach) + 'approach)' + title_add_on)
#                 visualization_tools.plot_feedin_comparison(
#                     validation_object, filename=filename,
#                     title=title, start=start, end=end)
#
#         if 'plot_correlation' in visualization_methods:
#             for validation_object in validation_set:
#                 filename = (
#                     save_folder +
#                     '{0}_{1}_Correlation_{2}_{3}_{4}_{5}.png'.format(
#                         validation_set[0].output_method,
#                         validation_object.object_name, year,
#                         validation_data_name, weather_data_name,
#                         approach))
#                 title = (
#                     '{0} of {1} and {2} in {3}\n {4} ({5} '.format(
#                         validation_set[0].output_method.replace(
#                             '_', ' '),
#                         weather_data_name, validation_data_name,
#                         validation_object.object_name, year,
#                         approach) + 'approach)' + title_add_on)
#                 visualization_tools.plot_correlation(
#                     validation_object, filename=filename,
#                     title=title)


# ---------------------------------- LaTeX Output --------------------------- #
path_latex_tables = os.path.join(os.path.dirname(__file__),
                                 latex_tables_folder)
if time_period is not None:
    filename_add_on = '_{0}_{1}'.format(time_period[0], time_period[1])
else:
    filename_add_on = ''

if 'annual_energy_approaches' in latex_output:
    for weather_data_name in weather_data_list:
        latex_df = pd.DataFrame()
        for outerKey, innerDict in annual_energy_dicts[
                weather_data_name].items():
            df_part = pd.DataFrame({(innerKey, innerstKey): [values] for
                                    innerKey, innerstDict in
                                    innerDict.items() if
                                    innerKey != 'measured_annual_energy' for
                                    innerstKey, values in innerstDict.items()},
                                   index=[outerKey]).round(2)
            df_part['measured', '[MWh]'] = round(
                annual_energy_dicts[weather_data_name][outerKey][
                    'measured_annual_energy'], 2)
            latex_df = pd.concat([latex_df, df_part], axis=0)
        latex_df.sort_index(axis=1, ascending=False, inplace=True)
        # TODO put simple method to front
        filename_table = os.path.join(
            path_latex_tables, 'annual_energy_approach_{0}_{1}{2}.tex'.format(
                year, weather_data_name, filename_add_on))
        latex_df.to_latex(buf=filename_table,
                          column_format=latex_tables.create_column_format(len(
                              latex_df.columns), 'c'),
                          multicolumn_format='c')

if 'annual_energy_weather' in latex_output:
    for approach in approach_list:
        latex_df = pd.DataFrame()
        for weather_data_name in weather_data_list:
            df_part_weather = pd.DataFrame()
            for outerKey, innerDict in annual_energy_dicts[
                    weather_data_name].items():
                df_part = pd.DataFrame(
                    {(weather_data_name, innerstKey): [values] for
                     innerKey, innerstDict in innerDict.items() if
                     (innerKey == approach and innerKey not in
                      restriction_list) for
                     innerstKey, values in innerstDict.items()},
                    index=[outerKey]).round(2)
                if weather_data_name == weather_data_list[0]:
                    df_part['measured', '[MWh]'] = round(
                        annual_energy_dicts[weather_data_name][outerKey][
                            'measured_annual_energy'], 2)
                df_part_weather = pd.concat([df_part_weather, df_part], axis=0)
            latex_df = pd.concat([latex_df, df_part_weather], axis=1)
        # Sort columns and index
        latex_df.sort_index(axis=1, ascending=False, inplace=True)
        latex_df.sort_index(axis=0, inplace=True)
        filename_table = os.path.join(
            path_latex_tables,
            'annual_energy_weather_{0}_{1}{2}.tex'.format(
                year, approach, filename_add_on))
        latex_df.to_latex(buf=filename_table,
                          column_format=latex_tables.create_column_format(len(
                              latex_df.columns), 'c'),
                          multicolumn_format='c')

if 'annual_energy_weather_approaches' in latex_output:
    latex_df = pd.DataFrame()
    for weather_data_name in weather_data_list:
        df_part_weather = pd.DataFrame()
        for outerKey, innerDict in annual_energy_dicts[
                weather_data_name].items():
            df_part = pd.DataFrame(
                {(innerKey, weather_data_name): [values] for
                 innerKey, innerstDict in innerDict.items() if
                 innerKey != 'measured_annual_energy'for
                 innerstKey, values in innerstDict.items() if innerstKey == 'deviation'},
                index=[outerKey]).round(2)
            df_part_weather = pd.concat([df_part_weather, df_part], axis=0)
        latex_df = pd.concat([latex_df, df_part_weather], axis=1)
    # Sort columns and index
    latex_df.sort_index(axis=1, ascending=False, inplace=True)
    latex_df.sort_index(axis=0, inplace=True)
    filename_table = os.path.join(
        path_latex_tables,
        'annual_energy_weather_approaches_{0}{1}.tex'.format(
            year, filename_add_on))
    latex_df.to_latex(buf=filename_table,
                      column_format=latex_tables.create_column_format(len(
                          latex_df.columns), 'c'),
                      multicolumn_format='c')

if 'key_figures_approaches' in latex_output:
    for weather_data_name in weather_data_list:
        latex_df = pd.DataFrame()


            df_part = pd.DataFrame(
                {(header_dict[], innerKey): [values] for
                 innerKey, innerstDict in innerDict.items() if
                 innerKey != 'measured_annual_energy'for
                 innerstKey, values in innerstDict.items() if innerstKey == 'deviation'},
                index=[outerKey + ]).round(2)
            df_part_weather = pd.concat([df_part_weather, df_part], axis=0)
        latex_df = pd.concat([latex_df, df_part_weather], axis=1)


        filename_table = os.path.join(
            path_latex_tables,
            'key_figures_approaches_{0}_{1}{2}.tex'.format(
                year, weather_data_name, filename_add_on))
        latex_df.to_latex(buf=filename_table,
                          column_format=latex_tables.create_column_format(len(
                              latex_df.columns), 'c'),
                          multicolumn_format='c')

if 'key_figures_weather' in latex_output:
    # Do not include data of annual energy output
    ouput_methods_modified = [method for method in output_methods
                              if method is not 'annual_energy_output']
    for approach in approach_list:
        # Initialise DataFrame for latex output
        latex_df = pd.DataFrame()
        # Iteration through validation data
        for validation_data_name in validation_data_list:
            # Initialize validation sets list
            validation_sets = []
            for filename in filenames_validation_objects: # TODO: function?!
                if (approach in filename and str(year) in filename and
                        validation_data_name in filename):
                    validation_sets.append(pickle.load(open(filename, 'rb')))
            # Initialize df parts for each wind farm
            df_parts = [pd.DataFrame() for j in range(len(validation_sets[0]))]
            for output_method in ouput_methods_modified:
                validation_sets_part = [
                    val_set for val_set in validation_sets
                    if val_set[0].output_method == output_method]
                for i in range(len(validation_sets_part[0])):
                    data = np.array([latex_tables.get_data(
                        validation_sets_part,
                        ['RMSE', 'Pr', 'mean bias', 'std. dev.'], i,
                        len(weather_data_list))])
                    column_names = ['RMSE [MW]/[MWh]', "Pearson's r",
                                    'mean bias [MW]/[MWh]',
                                    'standard deviation [MW]/[MWh]']
                    columns_2 = [
                        validation_sets_part[j][0].weather_data_name
                        for j in range(len(weather_data_list))] * len(
                        column_names)
                    columns = [np.array(latex_tables.get_columns(
                        column_names, len(weather_data_list))),
                        np.array(columns_2)]
                    index = ['{0} {1}'.format(
                        validation_sets_part[0][i].object_name,
                        validation_sets_part[0][i].output_method.rsplit(
                            '_')[0])]
                    df_part = pd.DataFrame(data=data, columns=columns,
                                           index=index)
                    df_parts[i] = pd.concat([df_parts[i], df_part], axis=0)
                    if output_method == 'monthly_energy_output':
                        pass
                    for validation_set in validation_sets_part:
                        if (validation_sets_part[0][i].object_name !=
                                validation_set[i].object_name):
                            raise ValueError(
                                "Careful: Object names differ!! " +
                                "{0} and {1}".format(
                                    validation_sets_part[0][i].object_name,
                                    validation_set[i].object_name))
            for df_part in df_parts:
                latex_df = pd.concat([latex_df, df_part], axis=0)
        filename_table = os.path.join(
            path_latex_tables,
            'Key_figures_weather_{0}_{1}{2}.tex'.format(
                year, approach, filename_add_on))
        latex_df.to_latex(buf=filename_table,
                          column_format=latex_tables.create_column_format(
                              len(latex_df.columns), 'c'),
                          multicolumn_format='c')


if 'key_figures_approaches' in latex_output:
    # Do not include data of annual energy output
    ouput_methods_modified = [method for method in output_methods
                              if method is not 'annual_energy_output']
    for weather_data_name in weather_data_list:
        # Initialise DataFrame for latex output
        latex_df = pd.DataFrame()
        # Iteration through validation data
        for validation_data_name in validation_data_list:
            # Initialize validation sets list
            validation_sets = []
            for filename in filenames_validation_objects: # TODO: function?!
                if (weather_data_name in filename and str(year) in filename and
                        validation_data_name in filename):
                    validation_sets.append(pickle.load(open(filename, 'rb')))
            # Initialize df parts for each wind farm
            df_parts = [pd.DataFrame() for j in range(len(validation_sets[0]))]
            for output_method in ouput_methods_modified:
                validation_sets_part = [
                    val_set for val_set in validation_sets
                    if val_set[0].output_method == output_method]
                for i in range(len(validation_sets_part[0])):
                    data = np.array([latex_tables.get_data(
                        validation_sets_part,
                        ['RMSE', 'Pr', 'mean bias', 'std. dev.'], i,
                        len(weather_data_list))])
                    column_names = ['RMSE [MW]/[MWh]', "Pearson's r",
                                    'mean bias [MW]/[MWh]',
                                    'standard deviation [MW]/[MWh]']
                    columns_2 = [
                        approach for approach in approach_list] * len(
                            column_names)
                    columns = [np.array(latex_tables.get_columns(
                        column_names, len(weather_data_list))),
                        np.array(columns_2)]
                    index = ['{0} {1}'.format(
                        validation_sets_part[0][i].object_name,
                        validation_sets_part[0][i].output_method.rsplit(
                            '_')[0])]
                    df_part = pd.DataFrame(data=data, columns=columns,
                                           index=index)
                    df_parts[i] = pd.concat([df_parts[i], df_part], axis=0)
                    if output_method == 'monthly_energy_output':
                        pass # TODO ?
                    for validation_set in validation_sets_part:
                        if (validation_sets_part[0][i].object_name !=
                                validation_set[i].object_name):
                            raise ValueError(
                                "Careful: Object names differ!! " +
                                "{0} and {1}".format(
                                    validation_sets_part[0][i].object_name,
                                    validation_set[i].object_name))
            for df_part in df_parts:
                latex_df = pd.concat([latex_df, df_part], axis=0)
        filename_table = os.path.join(
            path_latex_tables,
            'Key_figures_approach_{0}_{1}{2}.tex'.format(
                year, weather_data_name, filename_add_on))
        latex_df.to_latex(buf=filename_table,
                          column_format=latex_tables.create_column_format(
                              len(latex_df.columns), 'c'),
                          multicolumn_format='c')

# ------------------------------- Extra plots ------------------------------- #
# if 'annual_bars_weather' in extra_plots:
#     years = [2015, 2016]
#     if 'annual_energy_output' not in output_methods:
#         raise ValueError("'annual_energy_output' not in `output_methods` - " +
#                          "cannot generate 'annual_bars_weather' plot")
#     for approach in approach_list:
#         for validation_data_name in validation_data_list:
#             filenames = []
#             for year in years:
#                 validation_sets = []
#                 filenames.extend(['validation_sets_{0}_{1}_{2}_{3}'.format(
#                     year, weather_data_name,
#                     validation_data_name, approach) +
#                              '_annual_energy_output.p'
#                              for weather_data_name in weather_data_list])
#                 for filename in filenames:
#                     if (approach in filename and 'annual_energy_output' in filename
#                             and validation_data_name in filename
#                             and str(year) in filename):
#                         validation_sets.append(pickle.load(open(filename, 'rb')))
#                     index = [year]
#                     columns = [validation_data_name]
#                     columns.extend([name for name in weather_data_list])
#                     data = []

print('# ----------- Done ----------- #')
