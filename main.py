# Imports from Windpowerlib
from windpowerlib import wind_farm as wf

# Imports from lib_validation
import wind_farm_specifications
import visualization_tools
import analysis_tools
import tools
import latex_tables
import modelchain_usage
from merra_weather_data import get_merra_data
from open_fred_weather_data import get_open_fred_data
from argenetz_data import get_argenetz_data

# Other imports
import os
import pandas as pd
import numpy as np
import pickle

# ----------------------------- Set parameters ------------------------------ #
year = 2015
time_zone = 'Europe/Berlin'
pickle_load_merra = True
pickle_load_open_fred = True
pickle_load_arge = True
pickle_load_wind_farm_data = False
approach_list = [
    'simple',  # logarithmic wind profile, simple aggregation for farm output
#    'density_correction'  # density corrected power curve, simple aggregation
#     'smooth_wf'  # Smoothed power curves at wind farm level
    ]
weather_data_list = [
   'MERRA',
   'open_FRED'
    ]
validation_data_list = [ # TODO: Add other validation data
    'ArgeNetz'
    ]

output_methods = [
    'annual_energy_output',
    'hourly_energy_output',
    'monthly_energy_output',
    'power_output'
    ]
visualization_methods = [
#    'box_plots',
#    'feedin_comparison',
#    'plot_correlation'  # Attention: this takes a long time for high resolution
    ]

# Select time of day you want to observe or None for all day
time_period = (
       8, 20  # time of day to be selected (from h to h)
        # None   # complete time series will be observed
        ) 

# Start and end date for time period to be plotted
# Attention: only for 'feedin_comparison' and not for monthly output
#start = '{0}-10-01 11:00:00+00:00'.format(year)
#end = '{0}-10-01 16:00:00+00:00'.format(year)
#start = '{0}-10-01'.format(year)
#end = '{0}-10-03'.format(year)
start = None
end = None

latex_output = np.array([
    # 'annual_energy_weather',  # Annual energy output of all weather sets
    # 'key_figures_weather',     # Key figures of all weather sets
    # 'key_figures_approaches',  # Key figures of all approaches
    'annual_energy_approaches'  # ...
     ])
extra_plots = np.array([
#    'annual_bars_weather'  # Bar plot of annual energy output for all weather data and years
    ])
# relative path to latex tables folder
latex_tables_folder = '../../../User-Shares/Masterarbeit/Latex/Tables/'

# Other plots
plot_arge_feedin = False  # If True plots each column of ArgeNetz data frame

# Filename specification
arge_pickle_filename = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'dumps/validation_data',
    'arge_netz_data_{0}.p'.format(year)))

# Heights for which temperature of MERRA shall be calculated
temperature_heights = [60, 64, 65, 105, 114]


# -------------------------- Validation Feedin Data ------------------------- #
def get_validation_farms(validation_data_name):
    r"""
    Creates list of farms representing the validation data.

    Farms are initialized and their power output and annual energy output are
    assigned to the respective attributes.

    Parameters
    ----------
    validation_data_name : String
        Name of the validation data. Options: 'ArgeNetz' # TODO: add here

    Returns
    -------
    validation_farms : List
        Contains :class:`windpowerlib.wind_farm.WindFarm` objects representing
        the wind farms with the measured (validation) power output.
    wind_farm_data : List
        Contains descriptions of the wind farms of the valdiation data.

    """
    if validation_data_name == 'ArgeNetz':
        # Get wind farm data
        wind_farm_data = wind_farm_specifications.get_wind_farm_data(
            'farm_specification_argenetz_{0}.p'.format(year),
            os.path.join(os.path.dirname(__file__),
                         'dumps/wind_farm_data'),
            pickle_load_wind_farm_data)
        # Get ArgeNetz Data
        validation_data = get_argenetz_data(
            year, pickle_load=pickle_load_arge, filename=arge_pickle_filename,
            csv_dump=False, plot=plot_arge_feedin)
    if validation_data_name == '...':
        pass  # Add more data

    # Initialise validation wind farms from `wind_farm_data` and add power
    # output and annual energy output
    validation_farms = []
    for description in wind_farm_data:
        # Initialise wind farm
        wind_farm = wf.WindFarm(**description)
        # Power output in MW with DatetimeIndex indices
        wind_farm.power_output = pd.Series(
            data=(validation_data[description['object_name'] +
                                  '_power_output'].values / 1000),
            index=(validation_data[description['object_name'] +
                                   '_power_output'].index))
    #    # Convert DatetimeIndex indices to UTC # TODO: delete or optional
    #    wind_farm.power_output.index = pd.to_datetime(indices).tz_convert('UTC')
        # Annual energy output in MWh
        wind_farm.annual_energy_output = tools.annual_energy_output(
            wind_farm.power_output)
        validation_farms.append(wind_farm)
    # Add a summary of the wind farms to validation_farms
    validation_farms.append(tools.summarize_output_of_farms(validation_farms))
    return validation_farms, wind_farm_data


# ------------------------- Power output simulation ------------------------- #
def get_simulation_farms(weather_data_name, validation_data_name,
                         wind_farm_data, approach, validation_farms=None):
    r"""
    Creates list of farms containing the simulated power/energy output.

    The weather data set specified by `weather_data_name` is loaded, farms are
    initialised and their power output and annual energy output are assigned to
    the respective attributes.

    Parameters
    ----------
    weather_data_name : String
        Name of the weather data. Option: 'MERRA', 'open_FRED'
    validation_data_name : String
        Name of the validation data the output is simulated for.
        Options: 'ArgeNetz' # TODO: add here
    wind_farm_data : List
        Contains descriptions of the wind farms for the simulation.
    approach : String
        Approach of calculating the power output of a wind turbine / wind farm.
        Options: 'simple', # TODO: add options

    Returns
    -------
    simulation_farms : List
        Contains :class:`windpowerlib.wind_farm.WindFarm` objects representing
        the simulated wind farms.

    """
    # Generate filename (including path) for pickle dumps (and loads)
    filename_weather = os.path.join(os.path.dirname(__file__), 'dumps/weather',
                                    'weather_df_{0}_{1}.p'.format(
                                        weather_data_name, year))
    if weather_data_name == 'MERRA':
        if not pickle_load_merra:
            # Read csv file that contains weather data (pd.DataFrame is dumped)
            # to save time below
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

    # Initialise simulaton wind farms from `wind_farm_data` and calculate power
    # output and annual energy output
    simulation_farms = []
    for description in wind_farm_data:
        # Initialise wind farm
        wind_farm = wf.WindFarm(**description)
        # Get weather data for specific coordinates
        weather = tools.get_weather_data(
            weather_data_name, wind_farm.coordinates, pickle_load=True,
            filename=filename_weather, year=year,
            temperature_heights=temperature_heights)
        if (validation_data_name == 'ArgeNetz' and year == 2015):
            # For ArgeNetz data in 2015 only data from May on is needed (local)
            weather, converted = tools.convert_time_zone_of_index(
                weather, 'local', local_time_zone='Europe/Berlin')
            weather = weather.loc[weather.index >= '2015-05-01']
            if converted:
                weather.index = weather.index.tz_convert('UTC')
                weather = weather.drop(weather.index[
                                       int(-60 / weather.index.freq.n):])
        # Power output in MW
        if approach == 'simple':
            wind_farm.power_output = modelchain_usage.power_output_simple(
                wind_farm.wind_turbine_fleet, weather) / (1*10**6)
#            wind_farm.power_output = tools.power_output_simple(
#                wind_farm.wind_turbine_fleet, weather, data_height) / (1*10**6)
        if approach == 'density_correction':
            wind_farm.power_output = modelchain_usage.power_output_simple(
                wind_farm.wind_turbine_fleet, weather,
                density_correction=True) / (1*10**6)
        if approach == 'smooth_wf':
            wind_farm.power_output = modelchain_usage.power_output_smooth_wf(
                wind_farm, weather, cluster=False, density_correction=False,
                wake_losses=False, smoothing=True, block_width=0.5,
                standard_deviation_method='turbulence_intensity')
            # wind_farm.power_output = tools.power_output_density_corr(
            #     wind_farm.wind_turbine_fleet, weather, data_height) / (1*10**6)
    #    # Convert DatetimeIndex indices to UTC  # TODO: delete or optional
    #    wind_farm.power_output.index = pd.to_datetime(
    #        wind_farm.power_output.index).tz_convert('UTC')
        if validation_data_name == 'ArgeNetz':
            # Set power output to nan where power output of ArgeNetz is nan
            for farm in validation_farms:
                if farm.object_name == description['object_name']:
                    # df = pd.DataFrame([farm.power_output,
                    #                    wind_farm.power_output]).transpose()
                    a = farm.power_output.loc[farm.power_output.isnull() == True]
                    indices = a.index.tz_convert('UTC')
                    # indices = farm.power_output.index[farm.power_output.apply(np.isnan)]
                    # pd.DataFrame([farm.power_output,
                                  # wind_farm.power_output]).transpose()
                    nan_amount = 0
                    for index in indices:
                        try:
                            wind_farm.power_output[index]
                            wind_farm.power_output[index] = np.nan
                            nan_amount += 1
                        except Exception:
                            pass
                    # print('numbers of nans filtered: {0}'.format(nan_amount))
                # s.isnull().sum() # TODO how many values are nan
        # Annual energy output in MWh
        wind_farm.annual_energy_output = tools.annual_energy_output(
            wind_farm.power_output)
        simulation_farms.append(wind_farm)
    # Add a summary of the wind farms to simulation_farms
    simulation_farms.append(tools.summarize_output_of_farms(simulation_farms))
    return simulation_farms


# ------------------------------ Data Evaluation ---------------------------- #
# Initialise array for filenames of pickle dumped validation objects
filenames_validation_objects = []
# Iterate through all approaches, validation data and weather data, dump
# validation sets and utilize visualization methods
for approach in approach_list:
    for validation_data_name in validation_data_list:
        validation_farms, wind_farm_data = get_validation_farms(
            validation_data_name)
        for weather_data_name in weather_data_list:
            simulation_farms = get_simulation_farms(
                weather_data_name, validation_data_name,
                wind_farm_data, approach, validation_farms)

            if (weather_data_name == 'open_FRED' and year == 2016):
                # For open_FRED data in 2016 data does not exist for december
                # validation_data, converted = tools.convert_time_zone_of_index(
                #     validation_data, 'local', local_time_zone='Europe/Berlin')
                for validation_farm in validation_farms:
                    validation_farm.power_output = (
                        validation_farm.power_output.loc[
                            validation_farm.power_output.index <= '2016-11-30'])
                # if converted:
                #     weather.index = weather.index.tz_convert('UTC')
                #     weather = weather.drop(weather.index[
                #                            int(-60 / weather.index.freq.n):])
            # Produce validation sets
            # (one set for each farms list and output method)
            validation_sets = []
            if 'annual_energy_output' in output_methods:
                validation_sets.append(
                    analysis_tools.evaluate_feedin_time_series(
                        validation_farms, simulation_farms,
                        'annual_energy_output', validation_data_name,
                        weather_data_name, time_period, time_zone, 'A'))
            if 'hourly_energy_output' in output_methods:
                validation_sets.append(
                    analysis_tools.evaluate_feedin_time_series(
                        validation_farms, simulation_farms,
                        'hourly_energy_output', validation_data_name,
                        weather_data_name, time_period, time_zone, 'H'))
            if 'monthly_energy_output' in output_methods:
                validation_sets.append(
                    analysis_tools.evaluate_feedin_time_series(
                        validation_farms, simulation_farms,
                        'monthly_energy_output', validation_data_name,
                        weather_data_name, time_period, time_zone, 'M'))
            if 'power_output' in output_methods:
                for farm in simulation_farms:
                    farm.power_output = tools.upsample_series(
                        farm.power_output,
                        validation_farms[0].power_output.index.freq.n)
                validation_sets.append(
                    analysis_tools.evaluate_feedin_time_series(
                        validation_farms, simulation_farms, 'power_output',
                        validation_data_name, weather_data_name, time_period,
                        time_zone))

            # Dump validation_sets
            # TODO: dump could be in function evaluate....()
            if latex_output.size or extra_plots.size:
                for validation_set in validation_sets:
                    filename = os.path.join(
                        os.path.dirname(__file__),
                        'dumps/validation_objects',
                        'validation_sets_{0}_{1}_{2}_{3}_{4}.p'.format(
                            year, weather_data_name,
                            validation_data_name, approach,
                            validation_set[0].output_method))
                    pickle.dump(validation_set, open(filename, 'wb'))
                    filenames_validation_objects.append(filename)

            # --------------- Visualization of data evaluation -------------- #
            # Specify folder and title add on for saving the plots
            if time_period is not None:
                save_folder = (
                    '../Plots/{0}/{1}_{2}/{3}/time_period/{4}_{5}/'.format(
                        year, weather_data_name, validation_data_name,
                        approach, time_period[0], time_period[1]))
                title_add_on = ' time of day: {0}:00 - {1}:00'.format(
                    time_period[0], time_period[1])
            else:
                save_folder = '../Plots/{0}/{1}_{2}/{3}/'.format(
                    year, weather_data_name, validation_data_name, approach)
                title_add_on = ''
            # Use visualization methods for each validation set
            for validation_set in validation_sets:
                if (validation_set[0].output_method is not
                        'annual_energy_output'):
                    if 'box_plots' in visualization_methods:
                        # Store all bias time series of a validation set in one
                        # DataFrame for Boxplot
                        bias_df = pd.DataFrame()
                        for validation_object in validation_set:
                            if 'all' not in validation_object.object_name:
                                df_part = pd.DataFrame(
                                    data=validation_object.bias,
                                    columns=[validation_object.object_name])
                                bias_df = pd.concat([bias_df, df_part], axis=1)
                        # Specify filename
                        filename = (save_folder +
                                    '{0}_Boxplot_{1}_{2}_{3}_{4}.pdf'.format(
                                        validation_set[0].output_method, year,
                                        validation_data_name,
                                        weather_data_name, approach))
                        title = (
                            'Deviation of ' +
                            '{0} {1} from {2}\n in {3} ({4} approach)'.format(
                                weather_data_name,
                                validation_set[0].output_method.replace('_',
                                                                        ' '),
                                validation_data_name, year, approach) +
                            title_add_on)
                        visualization_tools.box_plots_bias(
                            bias_df, filename=filename, title=title)

                    if 'feedin_comparison' in visualization_methods:
                    # TODO: rename this method for better understanding
                        if (start is None and end is None and
                                validation_set[0].output_method
                                is not 'monthly_energy_output'):
                            filename_add_on = ''
                        else:
                            filename_add_on = '_{0}_{1}'.format(start, end)
                        for validation_object in validation_set:
                            filename = (
                                save_folder +
                                '{0}_{1}_Feedin_{2}_{3}_{4}_{5}{6}.png'.format(
                                    validation_set[0].output_method,
                                    validation_object.object_name, year,
                                    validation_data_name, weather_data_name,
                                    approach, filename_add_on))
                            title = (
                                '{0} of {1} and {2} in {3}\n {4} ({5} '.format(
                                    validation_set[0].output_method.replace(
                                        '_', ' '),
                                    weather_data_name, validation_data_name,
                                    validation_object.object_name, year,
                                    approach) + 'approach)' + title_add_on)
                            visualization_tools.plot_feedin_comparison(
                                validation_object, filename=filename,
                                title=title, start=start, end=end)

                    if 'plot_correlation' in visualization_methods:
                        for validation_object in validation_set:
                            filename = (
                                save_folder +
                                '{0}_{1}_Correlation_{2}_{3}_{4}_{5}.png'.format(
                                    validation_set[0].output_method,
                                    validation_object.object_name, year,
                                    validation_data_name, weather_data_name,
                                    approach))
                            title = (
                                '{0} of {1} and {2} in {3}\n {4} ({5} '.format(
                                    validation_set[0].output_method.replace(
                                        '_', ' '),
                                    weather_data_name, validation_data_name,
                                    validation_object.object_name, year,
                                    approach) + 'approach)' + title_add_on)
                            visualization_tools.plot_correlation(
                                validation_object, filename=filename,
                                title=title)


# ---------------------------------- LaTeX Output --------------------------- #
path_latex_tables = os.path.join(os.path.dirname(__file__),
                                 latex_tables_folder)
if time_period is not None:
    filename_add_on = '_{0}_{1}'.format(time_period[0], time_period[1])
else:
    filename_add_on = ''

if 'annual_energy_weather' in latex_output:
    if 'annual_energy_output' not in output_methods:
        raise ValueError("'annual_energy_output' not in `output_methods` - " +
                         "cannot generate 'annual_energy_weather' table")
    # TODO: check create_dataframe() of outputlib!
    for approach in approach_list:
        validation_sets = []
        # Initialise DataFrame for latex output
        latex_df = pd.DataFrame()
        for filename in filenames_validation_objects:
            if (approach in filename and str(year) in filename and
                    'annual_energy_output' in filename):
                val_sets = pickle.load(open(filename, 'rb'))
                validation_sets.append(val_sets)
        for validation_data_name in validation_data_list:
            validation_sets_part = [
                val_set for val_set in validation_sets
                if val_set[0].validation_name == validation_data_name]
            # Initialise DataFrame for latex output
            df_part = pd.DataFrame()
            i = 0 # TODO: check: maybe first part not necessary
            for validation_set in validation_sets:
                index = [val_obj.object_name for val_obj in validation_set]
                if i == 0:
                    # Add measured data (validation data) to DataFrame
                    data = [round(val_obj.validation_series.values[0], 2)
                            for val_obj in validation_set]
                    columns = [['Measured'], ['[MWh]']]
                    df_temp = pd.DataFrame(data=data, index=index,
                                           columns=columns)
                    df_part = pd.concat([df_part, df_temp], axis=1)
                # Add simulated data and its deviaton from validation data
                data_1 = [round(val_obj.simulation_series.values[0], 2)
                          for val_obj in validation_set]
                data_2 = [round(val_obj.bias.values[0] /
                                val_obj.validation_series.values[0] * 100, 2)
                          for val_obj in validation_set]
                data = np.array([data_1, data_2]).transpose()
                columns = [np.array([validation_set[0].weather_data_name,
                                     validation_set[0].weather_data_name]),
                           np.array(['[MWh]', '[%]'])]
                df_temp = pd.DataFrame(data=data, index=index, columns=columns)
                df_part = pd.concat([df_part, df_temp], axis=1)
                i += 1
            latex_df = pd.concat([latex_df, df_part])
        filename_table = os.path.join(
            path_latex_tables,
            'Annual_energy_weather_{0}_{1}{2}.tex'.format(
                year, approach, filename_add_on))
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


if 'annual_energy_approaches' in latex_output:
    if 'annual_energy_output' not in output_methods:
        raise ValueError("'annual_energy_output' not in `output_methods` - " +
                         "cannot generate 'annual_energy_weather' table")
    # TODO: check create_dataframe() of outputlib!
    for weather_data_name in weather_data_list:
        validation_sets = []
        # Initialise DataFrame for latex output
        latex_df = pd.DataFrame()
        for filename in filenames_validation_objects:
            if (weather_data_name in filename and str(year) in filename and
                    'annual_energy_output' in filename):
                val_sets = pickle.load(open(filename, 'rb'))
                validation_sets.append(val_sets)
        for validation_data_name in validation_data_list:
            validation_sets_part = [
                val_set for val_set in validation_sets
                if val_set[0].validation_name == validation_data_name]
            # Initialise DataFrame for latex output
            df_part = pd.DataFrame()
            i = 0 # TODO: check: maybe first part not necessary
            for validation_set in validation_sets:
                index = [val_obj.object_name for val_obj in validation_set]
                if i == 0:
                    # Add measured data (validation data) to DataFrame
                    data = [round(val_obj.validation_series.values[0], 2)
                            for val_obj in validation_set]
                    columns = [['Measured'], ['[MWh]']]
                    df_temp = pd.DataFrame(data=data, index=index,
                                           columns=columns)
                    df_part = pd.concat([df_part, df_temp], axis=1)
                # Add simulated data and its deviaton from validation data
                data_1 = [round(val_obj.simulation_series.values[0], 2)
                          for val_obj in validation_set]
                data_2 = [round(val_obj.bias.values[0] /
                                val_obj.validation_series.values[0] * 100, 2)
                          for val_obj in validation_set]
                data = np.array([data_1, data_2]).transpose()
                columns = [np.array([approach_list[0], approach_list[0]]),
                           np.array(['[MWh]', '[%]'])]
                df_temp = pd.DataFrame(data=data, index=index, columns=columns)
                df_part = pd.concat([df_part, df_temp], axis=1)
                i += 1
            latex_df = pd.concat([latex_df, df_part])
        filename_table = os.path.join(
            path_latex_tables,
            'Annual_energy_approach_{0}_{1}{2}.tex'.format(
                year, weather_data_name, filename_add_on))
        latex_df.to_latex(buf=filename_table,
                          column_format=latex_tables.create_column_format(len(
                              latex_df.columns), 'c'),
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
