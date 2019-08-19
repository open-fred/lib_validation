# Imports from Windpowerlib
from windpowerlib import wind_farm as wf

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
import logging
import settings


def get_weather_data(weather_data_name, coordinates, pickle_load=False,
                     filename='pickle_dump.p', year=None,
                     temperature_heights=None):
    r"""
    Gets MERRA-2 or open_FRED weather data for the specified coordinates.

    Parameters
    ----------
    weather_data_name : String
        String specifying if open_FRED, MERRA or 'ERA5' data is retrieved in
        case `pickle_load` is False.
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
        settings.init()
        # if weather_data_name == 'MERRA':
        #     data_frame = get_merra_data(
        #         year, heights=temperature_heights,
        #         filename=filename, pickle_load=pickle_load)
        if weather_data_name == 'open_FRED':
            fred_path = '~/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_{0}_sh.csv'.format(year) # todo adapt
            data_frame = get_open_fred_data(filename=fred_path, pickle_filename=filename)
        if weather_data_name == 'ERA5':
            era5_path = os.path.join(settings.weather_data_path,
                                     'era5_wind_bb_{}.csv'.format(year))
            data_frame = preload_era5_weather(
                filename=era5_path, pickle_filename=filename, pickle_load=False)

    # Find closest coordinates to weather data point and create weather_df
    closest_coordinates = get_closest_coordinates(data_frame, coordinates)
    data_frame = data_frame
    data_frame.sort_index(inplace=True)
    # Select coordinates from data frame
    weather_df = data_frame.loc[(slice(None),
                                 [closest_coordinates['lat']],
                                 [closest_coordinates['lon']]), :].reset_index(
                                    level=[1, 2], drop=True)
    if (weather_data_name == 'open_FRED' or weather_data_name == 'ERA5'):
        # Localize open_FRED data index
        weather_df.index = weather_df.index.tz_localize('UTC')
    # Add frequency attribute
    freq = pd.infer_freq(weather_df.index)
    weather_df.index.freq = pd.tseries.frequencies.to_offset(freq)
    # # Convert index to local time zone
    # weather_df.index = weather_df.index.tz_convert('Europe/Berlin')  # note: all in UTC
    return weather_df


def preload_era5_weather(filename, pickle_filename, pickle_load=False):
    r"""
    Reads csv file containing weather data and dumps it as data frame.

    Parameters
    ----------
    filename : string
        Name (including path) of file to load ERA5 data from.
    pickle_filename : string
        Name (including path) of file of pickle dump.
    pickle_load : boolean
        If True data is loaded from the pickle dump. Default: False.
    Returns
    -------
    data_frame : pd.DataFrame
        Contains ERA5 weather data.

    """
    if pickle_load:
        weather_df = pickle.load(open(pickle_filename, 'rb'))
    else:
        # Load data from csv file
        weather_df = pd.read_csv(filename,
                                 header=[0, 1], index_col=[0, 1, 2],
                                 parse_dates=True)
        # change type of height from str to int by resetting columns
        l0 = [_[0] for _ in weather_df.columns]
        l1 = [int(_[1]) for _ in weather_df.columns]
        weather_df.columns = [l0, l1]

        weather_df.rename(columns={'wind speed': 'wind_speed'}, inplace=True)  # todo delete after fix in era5
        pickle.dump(weather_df, open(pickle_filename, 'wb'))
        weather_df.to_csv(pickle_filename.replace('.p', '.csv'))
    return weather_df


def return_unique_pairs(df, column_names):
    r"""
    Returns all unique pairs of `column_names` of DataFrame `df`.

    Parameters
    ----------
    df : pd.DataFrame

    column_names : list
        Contains column names to get unique pairs for.

    Returns
    -------
    pd.DataFrame
        Columns (`column_names`) contain unique pairs of values.

    """
    return df.groupby(column_names).size().reset_index().drop([0], axis=1)


def get_closest_coordinates(df, coordinates, column_names=['lat', 'lon']):
    r"""
    Finds the coordinates of a data frame that are closest to `coordinates`.

    Parameters
    ----------
    df : pd.DataFrame

    coordinates : list of floats
        Contains coordinates in order ['lat', 'lon'].
    column_names : list of str
        Contains column names of coordinates in `df`. Default: ['lat', 'lon'].

    Returns
    -------
    pd.Series
        Contains closest coordinates with `column_names`as indices.

    """
    # get unique coordinate pairs
    coordinates_df = return_unique_pairs(df, column_names)
    # get coordinate clostest to `coordinates`
    tree = cKDTree(coordinates_df)
    dists, index = tree.query(np.array(coordinates), k=1)
    return coordinates_df.iloc[index]


# def select_certain_time_steps(series, time_period):
#     r"""
#     Selects certain time steps from series by a specified time period.
#
#     Parameters
#     ----------
#     series : pd.Series
#         Time series of which will be selected certain time steps.
#     time_period : Tuple (Int, Int)
#         Indicates time period for selection. Format (h, h) example (9, 12) will
#         select all time steps whose time lies between 9 and 12 o'clock.
#
#     """
#     # Save frequency attribute of `series`
#     freq = series.index.freq
#     # freq = pd.infer_freq(series.index)
#     selected_series = series[(time_period[0] <= series.index.hour) &
#                              (series.index.hour <= time_period[1])]
#     selected_series.index.freq = pd.tseries.frequencies.to_offset(freq)
#     return selected_series


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


def add_weather_locations_to_register(register, weather_coordinates):
    r"""
    Parameters
    ------------
    register : pd.DataFrame
        Contains location of each power plant in columns 'lat' (latitude) and
        'lon' (longitude).
    weather_coordinates : pd.DataFrame
        Contains columns specified in `column_names` with coordinates of the
        weather data grid point locations. Columns with other column names are
        ignored.

    Returns
    -------
    register : gpd.GeoDataFrame
        Input `register` data frame containing additionally the locations of
        the closest weather data grid points in 'weather_lat' (latitude of
        weather location) and 'weather_lon' (longitude of weather location).

    """
    if register[['lat', 'lon']].isnull().values.any():
        logging.warning("Missing coordinates in power plant register are "
                        "dropped.")
        register = register[np.isfinite(register['lon'])]
        register = register[np.isfinite(register['lat'])]
    closest_coordinates =  get_closest_coordinates(
        weather_coordinates, register[['lat', 'lon']]).set_index(
        register.index)
    register = register.assign(weather_lat=closest_coordinates['lat'].values,
                    weather_lon=closest_coordinates['lon'].values)

    return register


def example_weather_wind(filename):
    # loading weather data
    try:
        weather_df = pd.read_csv(filename,
                                 header=[0, 1], index_col=[0, 1, 2],
                                 parse_dates=True)
    except FileNotFoundError:
        raise FileNotFoundError("Please adjust the filename incl. path.")
    # change type of height from str to int by resetting columns
    l0 = [_[0] for _ in weather_df.columns]
    l1 = [int(_[1]) for _ in weather_df.columns]
    weather_df.columns = [l0, l1]
    return weather_df


def join_lib_validation_time_series(time_series_folder, files):
    df = pd.DataFrame()
    for file_ in files:
        data = pd.read_csv(os.path.join(time_series_folder, file_),
                           index_col=0, parse_dates=True)
        df = pd.concat([df, data], axis=0)
    return df