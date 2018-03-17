import pandas as pd
import os
from datetime import timedelta


def setup_converter_dataframe(converter, weather_data):
    r"""
    Reads HTW converter data from original files for given converter and sets
    up a dataframe.

    Parameters
    ----------
    converter : String
        Converter to set up the dataframe for. Possible choices are 'wr1',
        'wr2', 'wr3', 'wr4' and 'wr5'.
    weather_data : String
        Weather data that is used for calculated feed-in. The HTW data
        is resampled depending on the weather data. Possible choices are
        'open_FRED' and 'MERRA'.

    Returns
    --------
    pandas.DataFrame
        DataFrame with time series for feed-in etc..

    """
    file_directory = 'data/htw_2015/einleuchtend_data_2015'
    data = pd.read_csv(
        os.path.join(file_directory,
                     'einleuchtend_wrdata_2015_{}.csv'.format(converter)),
        sep=';', header=[0], index_col=[0], parse_dates=True)
    # resample to same resolution as weather data
    if weather_data == 'open_FRED':
        data = data.resample('30Min', loffset=timedelta(hours=0.25)).mean()
    elif weather_data == 'MERRA':
        data = data.resample('60Min', base=30,
                             loffset=timedelta(hours=0.5)).mean()
    data = data.tz_localize('Etc/GMT-1')
    data = data.tz_convert('Europe/Berlin')
    return data


def setup_weather_dataframe(weather_data):
    r"""
    Reads HTW weather data from original file and sets up a dataframe.

    Parameters
    ----------
    weather_data : String
        Weather data that is used for calculated feed-in. The HTW data
        is resampled depending on the weather data. Possible choices are
        'open_FRED' and 'MERRA'.

    Returns
    --------
    pandas.DataFrame
        DataFrame with time series for GHI and GNI in W/m², wind speed in m/s
        and air temperature in °C.

    """
    file_directory = 'data/htw_2015/einleuchtend_data_2015'
    data = pd.read_csv(
        os.path.join(file_directory, 'htw_wetter_weatherdata_2015.csv'),
        sep=';', header=[0], index_col=[0], parse_dates=True)
    # select and rename columns
    columns = {'G_hor_CMP6': 'ghi',
               'G_gen_CMP11': 'gni',
               'v_Wind': 'wind_speed',
               'T_Luft': 'temp_air'}
    data = data[list(columns.keys())]
    data.rename(columns=columns, inplace=True)
    # resample to same resolution as weather data
    if weather_data == 'open_FRED':
        data = data.resample('30Min', loffset=timedelta(hours=0.25)).mean()
    elif weather_data == 'MERRA':
        data = data.resample('60Min', base=30,
                             loffset=timedelta(hours=0.5)).mean()
    data = data.tz_localize('Etc/GMT-1')
    data = data.tz_convert('Europe/Berlin')
    return data