import pandas as pd
import numpy as np
import os
import pickle
from windpowerlib import (power_output, wind_speed)


def get_weather_data(pickle_load=None, filename='pickle_dump.p',
                     weather_data=None, year=None, coordinates=None,
                     data_frame=None):
    r"""
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
        List of coordinates [lat, lon] of location for loading data.
        Default: None
    data_frame : pandas.DataFrame
        Contains MERRA or open_FRED data. Makes function faster if it is used
        in a loop. Default: None.

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
            # TODO: add open_FRED weather data
            filename = 'weather_df_open_FRED_{0}.p'.format(year)
        elif weather_data == 'merra':
            if data_frame is None:
                # Load data from csv
                data_frame = pd.read_csv(os.path.join(
                    os.path.dirname(__file__), 'data/Merra', # TODO: make folder individua
                    'weather_data_GER_{0}.csv'.format(year)),
                    sep=',', decimal='.', index_col=0)
            data = create_merra_df(data_frame, coordinates)
            filename = 'weather_df_merra_{0}.p'.format(year)
        pickle.dump(data, open(os.path.join(os.path.dirname(__file__),
                               'dumps/weather', filename), 'wb'))
    return data


def create_merra_df(dataframe, coordinates):
    r"""
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
    merra_df = dataframe.loc[(dataframe['lat'] == coordinates[0]) &
                             (dataframe['lon'] == coordinates[1])]
    merra_df = merra_df.drop(['v1', 'v2', 'h2', 'cumulated hours',
                              'SWTDN', 'SWGDN'], axis=1)
    merra_df = merra_df.rename(
        columns={'v_50m': 'wind_speed', 'h1': 'temperature_height',
                 'z0': 'roughness_length', 'T': 'temperature',
                 'rho': 'density', 'p': 'pressure'}) # TODO: check units of Merra data
    return merra_df


def power_output_sum(wind_turbine_fleet, weather_df, data_height):
    r"""
    Calculate power output of several wind turbines by summation.

    Simplest way to calculate the power output of a wind farm or other
    gathering of wind turbines. For the power_output of the single turbines
    a power_curve without density correction is used. The wind speed at hub
    height is calculated by the logarithmic wind profile.

    Parameters
    ----------
    wind_turbine_fleet : List of Dictionaries
        Wind turbines of wind farm. Dictionaries must have 'wind_turbine'
        (contains wind turbine object) and 'number_of_turbines' (number of
        turbine type in wind farm) as keys.
    weather_df : pandas.DataFrame
        DataFrame with time series for wind speed `wind_speed` in m/s and
        roughness length `roughness_length` in m.
    data_height : Dictionary
        Contains the heights of the weather measurements or weather
        model in meters with the keys of the data parameter.

    """
    farm_power_output = 0
    for turbine_type in wind_turbine_fleet:
        wind_speed_hub = wind_speed.logarithmic_profile(
            weather_df.wind_speed, data_height['wind_speed'],
            turbine_type['wind_turbine'].hub_height,
            weather_df.roughness_length, obstacle_height=0.0)
        farm_power_output += (power_output.power_curve(
            wind_speed_hub,
            turbine_type['wind_turbine'].power_curve['wind_speed'],
            turbine_type['wind_turbine'].power_curve['values'])
            * turbine_type['number_of_turbines'])
    return farm_power_output


def annual_energy_output(power_output, temporal_resolution):
    r"""
    Calculate annual energy output from power output time series.

    Parameters
    ----------
    power_output : pd.Series
        Power output time series of wind turbine or wind farm.
    temporal_resolution : Integer
        Temporal resolution of power output time series in minutes.

    Return
    ------
    Float
        Annual energy output in Wh, kWh or MWh depending on the
        unit of `power_output`.

    """
    energy = power_output * temporal_resolution / 60
    return energy.sum()


def hourly_energy_output(power_output, temporal_resolution):
    # NOTE: This function could be enhanced to different output temporal resolutions
    r"""
    Converts power output time series to hourly energy output time series.

    Power output time series of different temporal resolutions are converted to
    energy output time series with a temporal resolution of one hour.

    Parameters
    ----------
    power_output : pd.Series
        Power output of wind turbine or wind farm.
    temporal_resolution : Integer
        Temporal resolution of time series in minutes.

    Returns
    -------
    energy_output : pd.Series
        Energy output time series with a temporal resolution of one hour.

    """
    energy_output_series = power_output * temporal_resolution / 60
    energy_output = pd.Series()
    start = 0
#    for i in range(len(power_output) - int(60 / temporal_resolution) * 2):
    while start < len(power_output):
        entry = pd.Series(energy_output_series.iloc[
                          start:int(start + 60 / temporal_resolution)].sum(),
                          index=[power_output.index[start]])
        energy_output = energy_output.append(entry)
        start = int(start + 60 / temporal_resolution)
    return energy_output


def standard_deviation(data_series):
    r"""
    Calculate standard deviation of a data series.

    Parameters
    ----------
    data_series : list or pandas.Series
        Input data series of which the standard deviation will be calculated.

    Return
    ------
    float
        Standard deviation of the input data series.

    """
    average = sum(data_series) / len(data_series)
    variance = sum((data_series[i] - average)**2
                   for i in range(len(data_series))) / len(data_series)
    return np.sqrt(variance)


def compare_series_std_deviation(series_measured, series_simulated):
    r"""
    Compare two series concerning their standard deviation.
    
    Parameters
    ----------
    series_measured : pandas.Series
        Validation power output time series.
    series_simulated : pandas.Series
        Simulated power output time series.
    
    Returns
    -------
    std_deviation : float
        Standard deviation of simulated series concerning vaildation series.

    """
    differences = pd.Series.subtract(series_measured, series_simulated)
    print(differences)
    std_deviation = standard_deviation(differences)
    # Add box plots
    # Add visualization
    return std_deviation

#dev = standard_deviation([6,7,7.5,6.5,7.5,8,6.5])  # Test
#dev = standard_deviation(pd.Series(data=[6,7,7.5,6.5,7.5,8,6.5]))  # Test
# TODO: possible: split tools module to power_output, weather, comparison...
