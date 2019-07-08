# Imports from Windpowerlib
from windpowerlib import wind_farm as wf
from windpowerlib import (power_output, wind_speed, density, temperature)

# Imports from lib_validation
from merra_weather_data import get_merra_data
from open_fred_weather_data import get_open_fred_data
import matplotlib.pyplot as plt

# Other imports
import pandas as pd
from scipy.spatial import cKDTree
import numpy as np
import pickle
import os


def get_weather_data(weather_data_name, coordinates, pickle_load=False,
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
        True if data has already been dumped before. Default: False.
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
        pickle.dump(data_frame, open(filename, 'rb'))
    # Find closest coordinates to weather data point and create weather_df
    closest_coordinates = get_closest_coordinates(data_frame, coordinates)
    # print(closest_coordinates)
    data_frame = data_frame
    data_frame.sort_index(inplace=True)
    # Select coordinates from data frame
    weather_df = data_frame.loc[(slice(None),
                                 [closest_coordinates['lat']],
                                 [closest_coordinates['lon']]), :].reset_index(
                                    level=[1, 2], drop=True)
    # if weather_data_name == 'open_FRED':
    #     # Localize open_FRED data index
    #     weather_df.index = weather_df.index.tz_localize('UTC')
    # Add frequency attribute
    freq = pd.infer_freq(weather_df.index)
    weather_df.index.freq = pd.tseries.frequencies.to_offset(freq)
    # # Convert index to local time zone
    # weather_df.index = weather_df.index.tz_convert('Europe/Berlin')  # note: all in UTC
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


def annual_energy_output(power_output_series, temporal_resolution=None):
    r"""
    Calculate annual energy output from power output time series.

    Parameters
    ----------
    power_output_series : pd.Series
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
        power_output_series.index.freq.n
        if power_output_series.index.freq.n == 1:
            freq = 60
        else:
            freq = power_output_series.index.freq.n
        energy = power_output_series * freq / 60
    except Exception:
        if temporal_resolution is not None:
            energy = power_output_series * temporal_resolution / 60
        else:
            raise ValueError("`temporal_resolution` needs to be specified " +
                             "as the frequency of the time series cannot be " +
                             "called.")
    return energy.sum()


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
    # Save frequency attribute of `series`
    freq = series.index.freq
    # freq = pd.infer_freq(series.index)
    selected_series = series[(time_period[0] <= series.index.hour) &
                             (series.index.hour <= time_period[1])]
    selected_series.index.freq = pd.tseries.frequencies.to_offset(freq)
    return selected_series


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
    wind_farm_sum = wf.WindFarm(object_name='Sum',
                                wind_turbine_fleet=None, coordinates=None)
    wind_farm_sum.power_output = sum(farm.power_output
                                     for farm in farm_list)
    wind_farm_sum.annual_energy_output = sum(farm.annual_energy_output
                                             for farm in farm_list)
    return wind_farm_sum


def filter_interpolated_data(series, window_size=10, tolerance=0.0011,
                             replacement_character=np.nan, plot=False):
    """

    Parameters
    ----------
    series : pd.Series
    replacement_character : Integer, Float or np.nan

    Returns
    -------
    corrected_df : pd.DataFrame
        Corrected data frame with interpolated values set to
        `replacement_character`.

    """
    data_corrected = series.copy()
    # calculate the sum of the gradient of the feed-in data over |window_size|
    # time steps, if it is about zero over the whole time window the data is
    # assumed to be interpolated
    data_gradient_sum = series.diff().diff().rolling(
        window=window_size, min_periods=window_size).sum()
    for i, v in data_gradient_sum.iteritems():
        # if the sum of the gradient is within the set tolerance and
        if abs(v) <= tolerance:
            if not (series[i - window_size + 1:i + 1] < 0).all():
                data_corrected[i - window_size + 1:i + 1] = (
                    replacement_character)
    if plot:
        series.plot()
        data_corrected.plot()
        plt.show()
    return data_corrected


def resample_with_nan_theshold(df, frequency, threshold):
    if threshold is None:
        resampled_df = df.resample(frequency).mean()
    else:
        resampled_df = pd.DataFrame()
        df2 = df.resample(frequency, how=['mean', 'count'])
        column_list = list(set([item[0] for item in list(df2)]))
        for column in column_list:
            df_part = pd.DataFrame(df2[column])
            df_part[column] = np.nan
            df_part.loc[df_part['count'] >= threshold, column] = df_part[
                'mean']
            df_part.drop(columns=['count', 'mean'], axis=1, inplace=True)
            resampled_df = pd.concat([resampled_df, df_part], axis=1)
    return resampled_df


def negative_values_to_nan(df, columns=None):
    if columns is None:
        columns = [column for column in list(df)]
    for column in columns:
        indices = df.loc[df[column] < 0.0].index
        df[column].loc[indices] = np.nan
    return df


def higher_values_to_nan(df, limit, columns=None):
    if columns is None:
        columns = [column for column in list(df)]
    for column in columns:
        indices = df.loc[df[column] > limit].index
        df[column].loc[indices] = np.nan
    return df
