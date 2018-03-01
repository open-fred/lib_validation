"""
The ``open_fred_weather_data`` module contains functions to read and dump the
open_FRED weather data from csv files.

TODO: The time stamps are in UTC. in the tools module a function converts them.
Try is this would work with the whole dataframe (with all locations) - took lots of time

"""

# Imports
import pandas as pd
import os
import pickle


def get_open_fred_data(filename='fred_data_2015_sh.csv',
                       pickle_filename='pickle_dump.p', pickle_load=False):
    r"""
    Reads csv file containing weather data and dumps it as data frame.

    Parameters
    ----------
    filename : String
        Name (including path) of file to load open_FRED data from.
        Default: 'fred_data_2015_sh.csv'.
    pickle_filename : String
        Name (including path) of file of pickle dump. Default: 'pickle_dump.p'.

    Returns
    -------
    data_frame : pd.DataFrame
        Contains open_FRED weather data.

    """
    if pickle_load:
        weather_df = pickle.load(open(pickle_filename, 'rb'))
    else:
        # Load data from csv file
        weather_df = pd.read_csv(filename,
                                 header=[0, 1], index_col=[0, 1, 2],
                                 parse_dates=True)
        # change type of height from str to int by resetting columns
        weather_df.columns = [weather_df.axes[1].levels[0][
                                  weather_df.axes[1].labels[0]],
                              weather_df.axes[1].levels[1][
                                  weather_df.axes[1].labels[1]].astype(int)]
        pickle.dump(weather_df, open(pickle_filename, 'wb'))
    return weather_df

if __name__ == "__main__":
    years = [
        2015,
        2016
    ]
    for year in years:
        pickle_path = os.path.join(
            os.path.dirname(__file__), 'dumps/weather',
            'weather_df_open_FRED_{0}.p'.format(year))
        fred_path = os.path.join(
            os.path.dirname(__file__), 'data/open_FRED',
            'fred_data_{0}_sh.csv'.format(year))
        # Get data
        weather_df = get_open_fred_data(filename=fred_path,
                                        pickle_filename=pickle_path)
