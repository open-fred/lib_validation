import pandas as pd
import os
import pickle
from windpowerlib import (wind_turbine, density,
                          power_output, temperature, wind_speed)


def get_weather_data(pickle_load=None, filename='pickle_dump.p',
                     weather_data=None, year=None, coordinates=None):
    """
    Helper function to load pickled weather data or retrieve data and dump it.

    Parameters
    ----------
    pickle_load : Boolean
        True if data has already been dumped before.
    filename : String
        Name (including path) of file to load data from or if MERRA data is
        retrieved function 'create_merra_df' is used. Default: 'pickle_dump.p'.
    weather_data : String
        String specifying if open_FRED or MERRA data is retrieved in case
        `pickle_load` is False. Default: None.
    year : int
        Specifies which year the weather data is retrieved for. Default: None.
    coordinates : List
        List of coordinates [lat, lon] of location. For loading data.
        Default: None

    Returns
    -------
    data : pandas.DataFrame
        Weather data with time series as index and data like temperature and
        wind speed as columns.

    """
    if pickle_load:
        data = pickle.load(open(filename, 'rb'))
    else:
        if weather_data == 'open_FRED':
            # # TODO: add open_FRED weather data
            filename = 'weather_df_open_FRED_{0}.p'.format(year)
        elif weather_data == 'merra':
            data = create_merra_df(os.path.join(
                os.path.dirname(__file__), 'data/Merra',
                'weather_data_GER_{0}.csv'.format(year)), coordinates) # TODO: make folder individual
            filename = 'weather_df_merra_{0}.p'.format(year)
        pickle.dump(data, open(os.path.join(os.path.dirname(__file__),
                               'dumps/weather', filename), 'wb'))
    return data


def create_merra_df(filename, coordinates):
    """
    Parameters
    ----------
    filename : String
        Name (including path) of file to load data from or if MERRA data is
        retrieved function 'create_merra_df' is used. Default: 'pickle_dump.p'.
    coordinates : List
        List of coordinates [lat, lon] of location. For loading data.
        Default: None
    Returns
    -------
    merra_df : pandas.DataFrame
        Weather data with time series as index and data like temperature and
        wind speed as columns.

    """
    merra_df = pd.read_csv(filename, sep=',', decimal='.', index_col=0)
    merra_df = merra_df.loc[(merra_df['lat'] == coordinates[0]) &
                            (merra_df['lon'] == coordinates[1])]
    merra_df = merra_df.drop(['v1', 'v2', 'h2', 'cumulated hours',
                              'SWTDN', 'SWGDN'], axis=1)
    merra_df = merra_df.rename(
        columns={'v_50m': 'wind_speed', 'h1': 'temperature_height',
                 'z0': 'roughness_length', 'T': 'temperature',
                 'rho': 'density', 'p': 'pressure'}) # TODO: check units of Merra data
    return merra_df


def power_output_sum(wind_turbines, number_of_turbines, weather, data_height):
    """
    Calculate power output of several wind turbines by summation.

    Simplest way to calculate the power output of a wind farm or other
    gathering of wind turbines.
    For the power_output of the single turbines a power_curve without density
    correction is used. The wind speed at hub height is calculated by the
    logarithmic wind profile.

    Parameters
    ----------
    wind_turbines : list
        Contains wind turbine objects.
    number_of_turbines : list
        Contains number of turbines in wind farm for each wind turbine object.
    weather :pandas.DataFrame
        Weather data with time series as index and data like temperature and
        wind speed as columns. # TODO: specifiy
    data_height : dictionary
        Contains the heights of the weather measurements or weather
        model in meters with the keys of the data parameter.

    """
    for turbine in wind_turbines:
        wind_speed_hub = wind_speed.logarithmic_profile(
            weather.wind_speed, data_height['wind_speed'], turbine.hub_height,
            weather.roughness_length, obstacle_height=0.0)
        cluster_power_output = power_output.power_curve(
            wind_speed_hub, turbine.power_curve['wind_speed'],
            turbine.power_curve['values']) * number_of_turbines # TODO: this should be in wind farm class..
        
    return




# Bredstedt (54.578219, 8.978092)
br_coor = [55, 8.75]
# Get weather
pickle_path = os.path.join(os.path.dirname(__file__),
                               'dumps/weather', 'weather_df_merra_2015.p')
## Initialise WindTurbine objects
#e70 = wind_turbine.WindTurbine(**enerconE70)
#e66 = wind_turbine.WindTurbine(**enerconE66)
#
#wind_turbines = e70
#number_of_turbines = 16

#mc = ModelChain(wind_turbines).run_model(weather)
#power_output = mc.power_output * number_of_turbines
