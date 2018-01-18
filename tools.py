# Imports from Windpowerlib
from windpowerlib import wind_farm as wf
from windpowerlib import (power_output, wind_speed, density, temperature)

# Imports from lib_validation
from merra_weather_data import get_merra_data
from open_fred_weather_data import get_open_fred_data
import tools

# Other imports
import pandas as pd
from scipy.spatial import cKDTree
import numpy as np
import pickle
import os


def get_weather_data(weather_data_name, coordinates, pickle_load=None,
                     filename='pickle_dump.p', year=None,
                     temperature_heights=None):
    r"""
    Gets MERRA-2 or open_FRED weather data for the specified coordinates.

    Parameters
    ----------
    weather_data_name : String
        String specifying if open_FRED or MERRA data is retrieved in case
        `pickle_load` is False.
    coordinates : List
        List of coordinates [lat, lon] of location for loading data.
    pickle_load : Boolean
        True if data has already been dumped before.
    filename : String
        Name (including path) of file to load data from or if MERRA data is
        retrieved function 'create_merra_df' is used. Default: 'pickle_dump.p'.
    year : int
        Specifies which year the weather data is retrieved for. Default: None.
    temperature_heights : List
        Contains heights for which the temperature of the MERRA-2 data shall be
        calculated. Default: None (as not needed for open_FRED data).

    Returns
    -------
    weather_df : pandas.DataFrame
        Weather data with datetime index and data like temperature and
        wind speed as columns.

    """
    if pickle_load:
        data_frame = pickle.load(open(filename, 'rb'))
    else:
        if weather_data_name == 'MERRA':
            data_frame = get_merra_data(
                year, heights=temperature_heights,
                filename=filename, pickle_load=pickle_load)
        if weather_data_name == 'open_FRED':
            fred_path = os.path.join(
                os.path.dirname(__file__), 'data/open_FRED',
                'fred_data_{0}_sh.csv'.format(year))
            data_frame = get_open_fred_data(
                year, filename=fred_path, pickle_filename=filename)
    # Find closest coordinates to weather data point and create weather_df
    closest_coordinates = tools.get_closest_coordinates(data_frame,
                                                        coordinates)
    # Select coordinates from data frame
    weather_df = data_frame.loc[(slice(None),
                                 slice(closest_coordinates['lat']),
                                 slice(closest_coordinates['lon'])),:].reset_index(
                                level=[1,2], drop=True)
    # Set index to standardized form
    if weather_data_name == 'MERRA':
        weather_df.index = tools.get_indices_for_series(
            temporal_resolution=60, time_zone='Europe/Berlin', year=year)
    if weather_data_name == 'open_FRED':
        series = weather_df['roughness_length']
        series.index = series.index.tz_localize('UTC')
        z0_series = tools.upsample_series(
            series, output_resolution=30,
            input_resolution='H')
        weather_df['roughness_length'] = z0_series.values
        weather_df.index = tools.get_indices_for_series(
            temporal_resolution=30, time_zone='UTC', year=year)
        # weather_df.index = weather_df.index.tz_localize('UTC') TODO: take care: always starts from 00:00?
    return weather_df


def return_unique_pairs(df, column_names):
    r"""
    Returns all unique pairs of values of DataFrame `df`.

    Returns
    -------
    pd.DataFrame
        Columns (`column_names`) contain unique pairs of values.

    """
    return df.groupby(column_names).size().reset_index().drop([0], axis=1)


def get_closest_coordinates(df, coordinates, column_names=['lat', 'lon']):
    r"""
    Finds the coordinates of a data frame that are closest to `coordinates`.

    Returns
    -------
    pd.Series
        Contains closest coordinates with `column_names`as indices.

    """
    coordinates_df = return_unique_pairs(df, column_names)
    tree = cKDTree(coordinates_df)
    dists, index = tree.query(np.array(coordinates), k=1)
    return coordinates_df.iloc[index]


def power_output_simple(wind_turbine_fleet, weather_df, data_height):
    # TODO: add weather_data_name to these functions and use modelchain for 
    #       open_FRED data as there are different heights and this is easier
    #       with the multiindex dataframe
    r"""
    Calculate power output of several wind turbines by a simple method.

    Simplest way to calculate the power output of a wind farm or other
    gathering of wind turbines. For the power_output of the single turbines
    a power_curve without density correction is used. The wind speed at hub
    height is calculated by the logarithmic wind profile. The power output of
    the wind farm is calculated by aggregation of the power output of the
    single turbines.

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

    Returns
    -------
    pd.Series
        Simulated power output of wind farm.

    """
    for turbine_type in wind_turbine_fleet:
        wind_speed_hub = wind_speed.logarithmic_profile(
            weather_df.wind_speed, data_height['wind_speed'],
            turbine_type['wind_turbine'].hub_height,
            weather_df.roughness_length, obstacle_height=0.0)
        turbine_type['wind_turbine'].power_output = (
            power_output.power_curve(
                wind_speed_hub,
                turbine_type['wind_turbine'].power_curve['wind_speed'],
                turbine_type['wind_turbine'].power_curve['values']))
    return power_output_simple_aggregation(wind_turbine_fleet)


def power_output_density_corr(wind_turbine_fleet, weather_df, data_height):
    r"""
#    Calculate power output of several wind turbines ......
#
#    Simplest way to calculate the power output of a wind farm or other
#    gathering of wind turbines. For the power_output of the single turbines
#    a power_curve without density correction is used. The wind speed at hub
#    height is calculated by the logarithmic wind profile.

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

    Returns
    -------
    pd.Series
        Simulated power output of wind farm.

    """
    for turbine_type in wind_turbine_fleet:
        wind_speed_hub = wind_speed.logarithmic_profile(
            weather_df.wind_speed, data_height['wind_speed'],
            turbine_type['wind_turbine'].hub_height,
            weather_df.roughness_length, obstacle_height=0.0)
        temperature_hub = temperature.linear_gradient(
            weather_df.temperature, data_height['temperature'],
            turbine_type['wind_turbine'].hub_height)
        density_hub = density.ideal_gas(
            weather_df.pressure, data_height['pressure'],
            turbine_type['wind_turbine'].hub_height, temperature_hub)
        turbine_type['wind_turbine'].power_output = (
            power_output.power_curve_density_correction(
                wind_speed_hub,
                turbine_type['wind_turbine'].power_curve['wind_speed'],
                turbine_type['wind_turbine'].power_curve['values'],
                density_hub))
    return power_output_simple_aggregation(wind_turbine_fleet, weather_df,
                                           data_height)


def power_output_simple_aggregation(wind_turbine_fleet):
    r"""
    Calulate power output of wind farm by simple aggregation.

    Parameters
    ----------
    wind_turbine_fleet : List of Dictionaries
        Wind turbines of wind farm. Dictionaries must have 'wind_turbine'
        (contains wind turbine object) and 'number_of_turbines' (number of
        turbine type in wind farm) as keys.

    """
    farm_power_output = 0
    for turbine_type in wind_turbine_fleet:
        farm_power_output += (turbine_type['wind_turbine'].power_output *
                              turbine_type['number_of_turbines'])
    return farm_power_output


def annual_energy_output(power_output, temporal_resolution=None):
    r"""
    Calculate annual energy output from power output time series.

    Parameters
    ----------
    power_output : pd.Series
        Power output time series of wind turbine or wind farm.
    temporal_resolution : Integer
        Temporal resolution of `power_output` time series in minutes. If the
        temporal resolution can be called by `power_output.index.freq.n` this
        parameter is not needed. Default: None

    Return
    ------
    Float
        Annual energy output in Wh, kWh or MWh depending on the
        unit of `power_output`.

    """
    try:
        energy = power_output * power_output.index.freq.n / 60
    except Exception:
        if temporal_resolution is not None:
            energy = power_output * temporal_resolution / 60
        else:
            raise ValueError("`temporal_resolution` needs to be specified " +
                             "as the frequency of the time series cannot be " +
                             "called.")
    return energy.sum()


def energy_output_series(power_output, output_resolution,
                         time_zone=None, temporal_resolution_intput=None):
    r"""
    Converts power output time series to hourly energy output time series.

    Power output time series of different temporal resolutions are converted to
    energy output time series with a temporal resolution of the parameter
    `output_resolution`. For correct resampling UCT-format `power_output` time
    series will be converted to the original time zone but converted back
    before the return. Set to `time_zone` to 'UTC' if resampling is wanted in
    UTC time zone.

    # TODO: Check if this is necessary for hourly resampling. if not: don't
    convert then!

    Parameters
    ----------
    power_output : pd.Series
        Power output of wind turbine or wind farm.
    output_resolution : String
        Intended resolution of output series: 'H' for hourly, 'M' for monthly,
        etc. see http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases
    time_zone : String
        Time zone information of the location of `power_output`. Not necessary
        if the `power_output` carries this information. Set to 'UTC' if
        resampling is wanted in UTC time zone. Default: None.
    temporal_resolution_intput : Integer
        Temporal resolution of `power_output` time series in minutes. If the
        temporal resolution can be called by `power_output.index.freq.n` this
        parameter is not needed. Default: None

    Returns
    -------
    energy_output : pd.Series
        Energy output time series with a temporal resolution of one hour.
        Time zone is the time zone of `power_output`.

    """
    # Convert time series to local time zone if necessary
    power_output, converted = convert_time_zone_of_index(
        power_output, 'local', local_time_zone=time_zone)
    try:
        energy_output_series = power_output * power_output.index.freq.n / 60
    except Exception:
        if temporal_resolution_intput is not None:
            energy_output_series = (power_output *
                                    temporal_resolution_intput / 60)
        else:
            raise ValueError("`temporal_resolution_intput` needs to be " +
                             "specified as the frequency of the time " +
                             "series cannot be called.")
    energy_output = energy_output_series.resample(output_resolution).sum()
    energy_output = energy_output.dropna()
    if converted:
        power_output.index = power_output.index.tz_convert('UTC')
    return energy_output


def upsample_series(series, output_resolution, input_resolution=None):
    r"""
    Change temporal resolution of a series by filling with pad().

    The input time series (`series`) is for calculations converted to UTC
    and back to the original time zone before the return. Consequently, if
    `series` time series is not in UTC form it needs to carry a time zone
    information.

    Parameters
    ----------
    series : pd.Series
        Series to be upsampled.
    output_resolution : Integer
        Temporal resolution of output time series in minutes.
    input_resolution : Integer
        Temporal resolution of `series` in minutes. If the temporal resolution
        can be called by `series.index.freq.n` this parameter is not needed.
        Default: None

    Returns
    -------
    output_series : pd.Series
        `series` in the temporal resolution of `output_resolution`.
        Time zone is the time zone of `series`.

    """
    # Convert time series to UTC
    if str(series.index.tz) is not 'UTC':
        time_zone = series.index.tz
        series.index = series.index.tz_convert('UTC')
    else:
        time_zone = None
    try:
        index = pd.date_range(series.index[-1], periods=2,
                              freq=series.index.freq)
    except Exception:
        if input_resolution is not None:
            index = pd.date_range(series.index[-1], periods=2,
                                  freq=input_resolution)
        else:
            raise ValueError("`input_resolution` needs to be specified as " +
                             "the frequency of the time " +
                             "series cannot be called.")
    output_series = pd.concat([series, pd.Series(10, index=[index[1]])])
    output_series = output_series.resample(
        '{0}min'.format(output_resolution)).pad()  #TODO: this does not work because of duplicates!!!!!
    output_series = output_series.drop(output_series.index[-1])
    if time_zone:
        # Convert back to original time zone
        output_series.index = output_series.index.tz_convert(str(time_zone))
    return output_series


def get_indices_for_series(temporal_resolution, time_zone, year=None,
                           start=None, end=None):
    r"""
    Create indices for annual time series in a certain frequency and form.

    The indices are created for the time zone of 'Europe/Berlin'.

    Parameters
    ----------
    temporal_resolution : integer
        Intended temporal resolution of time series index in min.
    time_zone : String
        Time zone of output indices ('UTC', 'Europe/Berlin', ...).
    year : integer
        Year of the time series. Either `year` or `start` and `end` have to be
        defined. If all three are given, `start` and `end` will be used.
        Default: None.
    start : String
        Start date of index time series. Either `year` or `start` and `end`
        have to be defined. Format: 'd/m/yyyy'. Default: None.
    end : String
        Defines end date - set `end` to one day after the end date.
        Example: '1/1/2017' for ending in 2016.
        Either `year` or `start` and `end` have to be defined. Default: None.

    Returns
    -------
        Date range index in intended temporal resolution.

    """
    frequency = '{0}min'.format(temporal_resolution)
    if (start is not None and end is not None):
        pass
    else:
        try:
            start = '1/1/{0}'.format(year)
            end = '1/1/{0}'.format(year + 1)
        except TypeError:
            raise TypeError("Either `year` or `start` and `end`" +
                            "have to be defined.")
    return (pd.date_range(start, end, freq=frequency,
                          tz=time_zone, closed='left'))


def select_certain_time_steps(series, time_period):
    r"""
    Selects certain time steps from series by a specified time period.

    Parameters
    ----------
    series : pd.Series
        Time series of which will be selected certain time steps.
    time_period : Tuple (Int, Int)
        Indicates time period for selection. Format (h, h) example (9, 12) will
        select all time steps whose time lies between 9 and 12 o'clock.

    """
    return series[(time_period[0] <= series.index.hour) &
                  (series.index.hour <= time_period[1])]


def convert_time_zone_of_index(data, output_time_zone, local_time_zone=None):
    r"""
    Checks the index time zone of `data` and converts it if necessary.

    The time zone of the index is converted to UTC or a local time zone if
    depending on `output_time_zone`.

    Parameters
    ----------
    data : pd.Series or pd.DataFrame
        Date of which the index has to be checked and/or converted.
    output_time_zone : String
        Desired output time zone. Options: 'UTC', 'local'.
    local_time_zone : String
        Local time zone the index of `series` will be converted to if
        `output_time_zone` is 'local' and the index of `series` is UTC.
        Default: None.

    Returns
    -------
    series : pd.Series
        Time series of `series` with converted or not converted index time
        depending on weather `ouput_time_zone` was already existent.
    converted : Boolean
        True if conversion has taken place.
        False if conversion has not taken place.

    """
    # TODO: if output_time_zone == ... else: convert to this time zone (one parameter less)
    if output_time_zone == 'local':
        if str(data.index.tz) == 'UTC':
            data.index = data.index.tz_convert(local_time_zone)
            converted = True
        else:
            converted = False
    if output_time_zone == 'UTC':
        if str(data.index.tz) is not 'UTC':
            data.index = data.index.tz_convert('UTC')
            converted = True
        else:
            converted = False
    return data, converted


def summarize_output_of_farms(farm_list):
    r"""
    Summarizes the output of several wind farms and initialises a new farm.

    Power output time series and annual energy output are summarized.

    Parameters
    ----------
    farm_list : List
        Contains :class:`~.windpowerlib.wind_farm.WindFarm` objects.

    Returns
    -------
    wind_farm_sum : Object
        A :class:`~.windpowerlib.wind_farm.WindFarm` object representing a
        sum of wind farms needed for validation purposes.

    """
    wind_farm_sum = wf.WindFarm(wind_farm_name='Sum',
                                wind_turbine_fleet=None, coordinates=None)
    wind_farm_sum.power_output = sum(farm.power_output
                                     for farm in farm_list)
    wind_farm_sum.annual_energy_output = sum(farm.annual_energy_output
                                             for farm in farm_list)
    return wind_farm_sum


def filter_interpolated_data(df, replacement_character=np.nan):
    """

    Parameters
    ----------
    df : pd.DataFrame
        Data frame that contains # TODO: add
    replacement_character : Integer, Float or np.nan

    Returns
    -------
    corrected_df : pd.DataFrame
        Corrected data frame with interpolated values set to
        `replacement_character`.

    """
    
