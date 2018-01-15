# Imports from Windpowerlib
from windpowerlib import wind_farm as wf

# Imports from lib_validation
import wind_farm_specifications
import visualization_tools
import analysis_tools
import tools
from argenetz_data import get_argenetz_data

# Other imports
import os
import pandas as pd
import numpy as np
import pickle

# ----------------------------- Set parameters ------------------------------ #
year = 2016
time_zone = 'Europe/Berlin'
pickle_load_merra = True
pickle_load_open_fred = True
pickle_load_arge = True
pickle_load_wind_farm_data = True
approach_list = [
    'simple',  # logarithmic wind profile, simple aggregation for farm output
    'density_correction'  # density corrected power curve, simple aggregation
    ]
weather_data_list = [
    'MERRA',
#    'open_FRED' # TODO: not implemented yet
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
#        12, 15  # time of day to be selected (from h to h)
        None   # complete time series will be observed
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
    'annual_energy_weather',  # Annual energy output of all weather sets
#    'key_figures_weather'     # Key figures of all weather sets
    ])
extra_plots = np.array([
#    'annual_bars_weather'  # Bar plot of annual energy output for all weather data and years
    ])
# relative path to latex tables folder
latex_tables_folder = '../../../User-Shares/Masterarbeit/Latex/Tables/'

# Other plots
plot_arge_feedin = False  # If True plots each column of ArgeNetz data frame


# -------------------------- Validation Feedin Data ------------------------- #
def get_validation_farms(validation_data_name):
    r"""
    Creates list of farms representing the validation data.

    Farms are initialised and their power output and annual energy output are
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
        # Create DatetimeIndex indices for DataFrame depending on the year
        if year == 2015:
            indices = tools.get_indices_for_series(
                temporal_resolution=5, time_zone='Europe/Berlin',
                start='5/1/2015', end='1/1/2016')
        if year == 2016:
            indices = tools.get_indices_for_series(
                temporal_resolution=1, time_zone='Europe/Berlin', year=year)
        # Get wind farm data
        wind_farm_data = wind_farm_specifications.get_wind_farm_data(
            'farm_specification_argenetz_{0}.p'.format(year),
            os.path.join(os.path.dirname(__file__),
                         'dumps/wind_farm_data'),
            pickle_load_wind_farm_data)
        # Get ArgeNetz Data
        validation_data = get_argenetz_data(
            year, only_get_power=True, pickle_load=pickle_load_arge,
            plot=plot_arge_feedin)
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
            data=(validation_data[description['wind_farm_name'] +
                                  '_power_output'].values / 1000),
            index=indices)
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
                         wind_farm_data, approach):
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
    if weather_data_name == 'MERRA':
        filename_weather = 'weather_df_merra_{0}.p'.format(year)
        pickle_load_weather = pickle_load_merra
    if weather_data_name == 'open_FRED':
        filename_weather = 'weather_df_open_FRED_{0}.p'.format(year)
        pickle_load_weather = pickle_load_open_fred
        data_height = {'wind_speed': 10,
                       'roughness_length': 0, # TODO: only for wind speed exact!
                       'temperature': 0,
                       'density': 0,
                       'pressure': 0}

    # Generate filename (including path) for pickle dumps (and loads)
    filename_weather = os.path.join(os.path.dirname(__file__), 'dumps/weather',
                                    filename_weather)
    if not pickle_load_weather:
        # Read csv file that contains weather data (pd.DataFrame is dumped)
        # and turn pickle_load_weather to True
        tools.read_and_dump_csv_weather(weather_data_name, year,
                                        filename_weather)
        pickle_load_weather = True
    # Initialise simulaton wind farms from `wind_farm_data` and calculate power
    # output and annual energy output
    simulation_farms = []
    for description in wind_farm_data:
        # Initialise wind farm
        wind_farm = wf.WindFarm(**description)
        # Get weather data
        weather = tools.get_weather_data(
            weather_data_name, pickle_load_weather, filename_weather, year,
            wind_farm.coordinates)
        if (validation_data_name == 'ArgeNetz' and year == 2015):
            # For ArgeNetz data in 2015 only data from May is needed
            weather, converted = tools.convert_time_zone_of_index(
                weather, 'local', local_time_zone='Europe/Berlin')
            weather = weather.loc[weather.index >= '2015-05-01']
            if converted:
                weather.index = weather.index.tz_convert('UTC')
                if weather.index.freq == '30T': # TODO: make more generic
                    weather = weather.drop(weather.index[-2:])
                if weather.index.freq == 'H':
                    weather = weather.drop(weather.index[-1])
        if weather_data_name == 'MERRA':
            # Temperature height is time series (different for each location)
            data_height = {'wind_speed': 50,  # Source: https://data.open-power-system-data.org/weather_data/2017-07-05/
                           'roughness_length': 0,  # TODO: is this specified?
                           'temperature': weather.temperature_height,
                           'density': 0,
                           'pressure': 0}
        if approach == 'simple':
            wind_farm.power_output = tools.power_output_simple(
                wind_farm.wind_turbine_fleet, weather, data_height) / (1*10**6)
        if approach == 'density_correction':
            wind_farm.power_output = tools.power_output_density_corr(
                wind_farm.wind_turbine_fleet, weather, data_height) / (1*10**6)
    #    # Convert DatetimeIndex indices to UTC  # TODO: delete or optional
    #    wind_farm.power_output.index = pd.to_datetime(
    #        wind_farm.power_output.index).tz_convert('UTC')
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
                wind_farm_data, approach)
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
                        for validation_object in validation_set:
                            filename = (
                                save_folder +
                                '{0}_{1}_Feedin_{2}_{3}_{4}_{5}.pdf'.format(
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
                            visualization_tools.plot_feedin_comparison(
                                validation_object, filename=filename,
                                title=title, start=start, end=end)

                    if 'plot_correlation' in visualization_methods:
                        for validation_object in validation_set:
                            filename = (
                                save_folder +
                                '{0}_{1}_Correlation_{2}_{3}_{4}_{5}.pdf'.format(
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
def create_column_format(number_of_columns, position):
        r"""
        Creates column format for pd.DataFrame.to_latex() function.

        Parameters
        ----------
        number_of_columns : Integer
            Number of columns of the table to be created without index column.
        position : String
            Position of text in columns. For example: 'c', 'l', 'r'.

        """
        column_format = 'l'
        for i in range(number_of_columns):
            column_format = column_format.__add__(position)
        return column_format

path_latex_tables = os.path.join(os.path.dirname(__file__),
                                 latex_tables_folder)


def get_columns(column_names, multiplikator):
    r"""
    Produces columns for pd.DataFrame needed for latex output.

    Parameters
    ----------
    column_names : List
        Contains column names (String).
    multiplikator : Integer
        Frequency of column names.

    Returns
    -------
    columns : List
        Column names for pd.DataFrame needed for latex output.

    """
    columns = []
    for column_name in column_names:
        columns.extend([column_name for i in range(multiplikator)])
    return columns


def get_data(validation_sets, data_names, object_position):
    r"""
    Retruns list containing data for pd.DataFrame needed for latex output.

    Paramters
    ---------
    validation_sets : List
        Contains lists of :class:`~.analysis_tools.ValidationObject` objects.
    data_names : List
        Contains specification of data (Strings) to be displayed.
    object_position : Integer
        Position of object in lists in `validation_sets`.

    Returns
    -------
    data : List
        Data for pd.DataFrame needed for latex output.

    """
    data = []
    if 'RMSE' in data_names:
        data.extend([round(validation_sets[j][object_position].rmse, 2)
                     for j in range(len(weather_data_list))])
    if 'Pr' in data_names:
        data.extend([round(validation_sets[j][object_position].pearson_s_r, 2)
                     for j in range(len(weather_data_list))])
    if 'mean bias' in data_names:
        data.extend([round(validation_sets[j][object_position].mean_bias, 2)
                     for j in range(len(weather_data_list))])
    if 'std. dev.' in data_names:
        data.extend([round(
            validation_sets[j][object_position].standard_deviation, 2)
            for j in range(len(weather_data_list))])
    return data


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
            if (approach in filename and str(year) in filename
                    and 'annual_energy_output' in filename):
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
            path_latex_tables, 'Annual_energy_weather_{0}_{1}.tex'.format(
                year, approach))
        latex_df.to_latex(buf=filename_table,
                          column_format=create_column_format(len(
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
                if (approach in filename and str(year) in filename
                        and validation_data_name in filename):
                    validation_sets.append(pickle.load(open(filename, 'rb')))
            # Initialize df parts for each wind farm
            df_parts = [pd.DataFrame() for j in range(len(validation_sets[0]))]
            for output_method in ouput_methods_modified:
                validation_sets_part = [
                    val_set for val_set in validation_sets
                    if val_set[0].output_method == output_method]
                for i in range(len(validation_sets_part[0])):
                    data = np.array([get_data(
                        validation_sets_part,
                        ['RMSE', 'Pr', 'mean bias', 'std. dev.'], i)])
                    column_names = ['RMSE [MW]/[MWh]', "Pearson's r",
                                    'mean bias [MW]/[MWh]',
                                    'standard deviation [MW]/[MWh]']
                    columns_2 = [
                        validation_sets_part[j][0].weather_data_name
                        for j in range(len(weather_data_list))] * len(
                        column_names)
                    columns = [np.array(get_columns(column_names,
                                                    len(weather_data_list))),
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
            path_latex_tables, 'Key_figures_weather_{0}_{1}.tex'.format(
                year, approach))
        latex_df.to_latex(buf=filename_table,
                          column_format=create_column_format(
                              len(latex_df.columns), 'c'),
                          multicolumn_format='c')

# ------------------------------- Extra plots ------------------------------- #
if 'annual_bars_weather' in extra_plots:
    years = [2015, 2016]
    if 'annual_energy_output' not in output_methods:
        raise ValueError("'annual_energy_output' not in `output_methods` - " +
                         "cannot generate 'annual_bars_weather' plot")
    for approach in approach_list:
        for validation_data_name in validation_data_list:
            filenames = []
            for year in years:
                validation_sets = []
                filenames.extend(['validation_sets_{0}_{1}_{2}_{3}'.format(
                    year, weather_data_name,
                    validation_data_name, approach) +
                             '_annual_energy_output.p'
                             for weather_data_name in weather_data_list])
                for filename in filenames:
                    if (approach in filename and 'annual_energy_output' in filename
                            and validation_data_name in filename
                            and str(year) in filename):
                        validation_sets.append(pickle.load(open(filename, 'rb')))
                    index = [year]
                    columns = [validation_data_name]
                    columns.extend([name for name in weather_data_list])
                    data = []
        

print('# ----------- Done ----------- #')
