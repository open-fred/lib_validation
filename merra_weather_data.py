# Imports from Windpowerlib
from windpowerlib import temperature

# Other imports
import pandas as pd
import os
import pickle


def get_merra_data(year, raw_data=False, multi_index=True, heights=None,
                   filename='pickle_dump.p', pickle_load=False):
    r"""
    Reads csv file containing MERRA weather data and dumps it as data frame.

    Data is revised: unnecessary columns are droped, columns are renamed - if
    `raw_data` is False (default). The data will be dumped as a MultiIndex
    pandas DataFrame if `multi_index` is True (default).

    Parameters
    ----------
    year : Integer
        Year the weather data is fetched for.
    raw_data : Boolean
        If True only the raw weather data will be returned and dumped. Set
        `pickle_load` to False if you do not know whether the pickle dump
        contains raw data or revised data. Default: False.
    multi_index : Boolean
        True if the data shall be dumped as a MultiIndex pandas DataFrame.
        Default: True.
    heights : List, optional
        Contains heights for which the temperature shall be calculated (only
        for MultiIndex DataFrame). Default: None.
    filename : String
        Name (including path) of file to load data from or if MERRA data is
        retrieved function 'create_merra_df' is used. Default: 'pickle_dump.p'.
    pickle_load : Boolean
        True if data has already been dumped before. Default: False.

    Returns
    -------
    weather_df : pd.DataFrame
        Containins raw or already revised MERRA-2 weather data.

    """
    if pickle_load:
        weather_df = pickle.load(open(filename, 'rb'))
    else:
        # Load data from csv
        data_frame = pd.read_csv(os.path.join(
            os.path.dirname(__file__), 'data/Merra',
            'weather_data_GER_{0}.csv'.format(year)),
            sep=',', decimal='.', index_col=0)
        if not raw_data:
            if multi_index:
                if heights is not None:
                    # Calculate temperature at special heights (hub_heights)
                    # and add to multiindex dataframe
                    temp = data_frame['T']
                    temp_height = data_frame['h1']
                    second_level_columns = [50, 0, 0, 0]
                    first_level_columns = ['wind_speed', 'roughness_length',
                                           'density', 'pressure']
                    for height in heights:
                        second_level_columns.append(height)
                        first_level_columns.append('temperature')
                        df_part = pd.DataFrame(
                            data=temperature.linear_gradient(
                                temp, temp_height, height),
                            index=data_frame.index,
                            columns=['temperature_{0}'.format(height)])
                        data_frame = pd.concat([data_frame, df_part], axis=1)
                index = [data_frame.index, data_frame['lat'], data_frame['lon']]
                data_frame_2 = rename_columns(data_frame, ['T', 'h1', 'lat', 'lon'])
                data_frame_2.index = index
                weather_df = data_frame_2
                weather_df.columns = [first_level_columns,
                                      second_level_columns]
            else:
                weather_df = rename_columns(data_frame)
        else:
            weather_df = data_frame
        pickle.dump(weather_df, open(filename, 'wb'))
    return weather_df


def rename_columns(weather_df, additional_columns_drop=None):
    r"""
    Renames columns and drops unnecessary columns.

    Parameters
    ----------
    weather_df : pd.DataFrame
        Contains MERRA-2 weather data.

    Returns
    -------
    weather_df : pandas.DataFrame
        Renamed MERRA-2 weather data frame.

    """
    drop_columns = ['v1', 'v2', 'h2', 'cumulated hours', 'SWTDN', 'SWGDN']
    for item in additional_columns_drop:
        drop_columns.append(item)
    df = weather_df.drop(drop_columns, axis=1)
    df = df.rename(
        columns={'v_50m': 'wind_speed', 'z0': 'roughness_length',
                 'rho': 'density', 'p': 'pressure'}) # TODO: check units of Merra data
    return df


if __name__ == "__main__":
    years = [
        2015,
        2016
    ]
    # Heights for which the temperature shall be calculated (hub heights)
    heights = [60, 64, 65, 105, 114]
    for year in years:
        filename_weather = os.path.join(
            os.path.dirname(__file__), 'dumps/weather',
            'weather_df_MERRA_{0}.p'.format(year))
        weather_df = get_merra_data(year, raw_data=False, multi_index=True,
                                    heights=heights, filename=filename_weather,
                                    pickle_load=False)
    # print(weather_df)
    # print(len(weather_df))
