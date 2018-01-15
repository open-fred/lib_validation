# Imports from lib_validation
import tools

# Other imports
import pandas as pd
import os
import pickle
from scipy.spatial import cKDTree
import numpy as np


def get_weather_data(weather_data_name, pickle_load=None,
                     filename='pickle_dump.p', year=None, coordinates=None):
    r"""
    Helper function to load pickled weather data or retrieve data and dump it.
    Parameters
    ----------
    weather_data_name : String
        String specifying if open_FRED or MERRA data is retrieved in case
        `pickle_load` is False.
    pickle_load : Boolean
        True if data has already been dumped before.
    filename : String
        Name (including path) of file to load data from or if MERRA data is
        retrieved function 'create_merra_df' is used. Default: 'pickle_dump.p'.
    year : int
        Specifies which year the weather data is retrieved for. Default: None.
    coordinates : List
        List of coordinates [lat, lon] of location for loading data.
        Default: None
    Returns
    -------
    weather_df : pandas.DataFrame
        Weather data with datetime index and data like temperature and
        wind speed as columns.
    """
    if pickle_load:
        data_frame = pickle.load(open(filename, 'rb'))
    else:
        data_frame = read_and_dump_csv_weather(weather_data_name, year,
                                               filename)
    # Find closest coordinates to weather data point and create weather_df
    closest_coordinates = get_closest_coordinates(data_frame, coordinates)
    weather_df = create_weather_df(data_frame, closest_coordinates,
                                   weather_data_name)
    # Set index to standardized form
    if weather_data_name == 'MERRA':
        weather_df.index = tools.get_indices_for_series(
            temporal_resolution=60, time_zone='Europe/Berlin', year=year)
    if weather_data_name == 'open_FRED':
        weather_df.index = tools.get_indices_for_series(
            temporal_resolution=30, time_zone='UTC', year=year)
        # weather_df.index = weather_df.index.tz_localize('UTC') TODO: take care: always starts from 00:00?
    return weather_df


def read_and_dump_csv_weather(weather_data_name, year,
                              filename='pickle_dump.p'):
    r"""
    Reads csv file containing weather data and dumps it as data frame.
    Parameters
    ----------
    weather_data_name : String
        String specifying if open_FRED or MERRA data is retrieved in case.
    year : Integer
        Year the weather data is fetched for.
    filename : String
        Name (including path) of file to load data from or if MERRA data is
        retrieved function 'create_merra_df' is used. Default: 'pickle_dump.p'.
    Returns
    -------
    data_frame : pd.DataFrame
        Containins raw weather data (MERRA) or already revised weather data
        (open_FRED).
    """
    if weather_data_name == 'open_FRED':
        # Load data from csv files and join in one data frame
        open_fred_filenames = ['wss_10m.csv', 'wss_80m.csv', 'z0.csv']
        # Initialize data_frame
        data_frame = pd.DataFrame()
        for of_filename in open_fred_filenames:
            df_csv = pd.read_csv(os.path.join( # TODO: generic: csv_filename
                os.path.dirname(__file__), 'data/open_FRED',
                of_filename),
                sep=',', decimal='.', index_col=0, parse_dates=True)
            if (of_filename == 'wss_10m.csv' or
                    of_filename == 'wss_80m.csv'):
                df_part = df_csv.reset_index().drop_duplicates().set_index(
                    'time')  # TODO: delete after fixing csv
                data_frame = pd.concat([data_frame, df_part], axis=1)
            if of_filename == 'z0.csv':
                z0_series = pd.Series()
                for coordinates in df_csv.groupby(
                        ['lat', 'lon']).size().reset_index().drop(
                        [0], axis=1).values.tolist():
                    df = df_csv.loc[(df_csv['lat'] == coordinates[0]) &
                                    (df_csv['lon'] == coordinates[1])]
                    series = df['Z0']
                    series.index = series.index.tz_localize('UTC')
                    z0_series = z0_series.append(upsample_series(series, 30))
                data_frame['roughness_length'] = z0_series.values
        data_frame = data_frame.loc[:, ~data_frame.columns.duplicated()]
        data_frame = data_frame.rename(columns={'WSS_10M': 'wind_speed',
                                                'WSS': 'wind_speed_80m'})
    elif weather_data_name == 'MERRA':
        # Load data from csv
        data_frame = pd.read_csv(os.path.join(
            os.path.dirname(__file__), 'data/Merra',
            'weather_data_GER_{0}.csv'.format(year)),
            sep=',', decimal='.', index_col=0)
    pickle.dump(data_frame, open(filename, 'wb'))
    return data_frame


def create_weather_df(data_frame, coordinates, weather_data_name):
    r"""
    Parameters
    ----------
    data_frame : pd.DataFrame
        Contains weather data in raw form from csv file (MERRA) or already
        altered data (open_FRED).
    coordinates : List
        List of coordinates [lat, lon] of location. For loading data.
        Default: None
    weather_data_name : String
        Specifying the name of the weather data.
    Returns
    -------
    weather_df : pandas.DataFrame
        Weather data with time series as index and data like temperature and
        wind speed as columns.
    """
    # Select coordinates from data frame
    weather_df = data_frame.loc[(data_frame['lat'] == coordinates[0]) &
                                (data_frame['lon'] == coordinates[1])]
    if weather_data_name == 'MERRA':
        weather_df = weather_df.drop(['v1', 'v2', 'h2', 'cumulated hours',
                                      'SWTDN', 'SWGDN'], axis=1)
        weather_df = weather_df.rename(
            columns={'v_50m': 'wind_speed', 'h1': 'temperature_height',
                     'z0': 'roughness_length', 'T': 'temperature',
                     'rho': 'density', 'p': 'pressure'}) # TODO: check units of Merra data
return weather_df
