"""
The ``weather_data`` module contains functions to read and dump MERRA-2 and
open_FRED weather data.

"""

# Imports from lib_validation
import tools

# Other imports
import pickle


def get_weather_data(weather_data_name, coordinates, pickle_load=None,
                     filename='pickle_dump.p', year=None):
    r"""
    Helper function to load pickled weather data or retrieve data and dump it.
# TODO: correct
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
                year, heights=[64, 65, 105],
                filename=filename, pickle_load=pickle_load)
        if weather_data_name == 'open_FRED':
#            data_frame = ...
            pass
    # Find closest coordinates to weather data point and create weather_df
    closest_coordinates = tools.get_closest_coordinates(data_frame,
                                                        coordinates)
    # Select coordinates from data frame
    weather_df = data_frame.loc[
        (data_frame['lat'] == closest_coordinates[0]) &
        (data_frame['lon'] == closest_coordinates[1])]
    # Set index to standardized form
    if weather_data_name == 'MERRA':
        weather_df.index = tools.get_indices_for_series(
            temporal_resolution=60, time_zone='Europe/Berlin', year=year)
    if weather_data_name == 'open_FRED':
        weather_df.index = tools.get_indices_for_series(
            temporal_resolution=30, time_zone='UTC', year=year)
        # weather_df.index = weather_df.index.tz_localize('UTC') TODO: take care: always starts from 00:00?
    return weather_df
