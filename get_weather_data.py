import xarray
import os
import pandas as pd
from os.path import expanduser

import tools


# ToDo: get upper and lower time bounds
def get_of_weather_data_from_netcdf(year, lat_min, lat_max, lon_min, lon_max,
                                    parameter_list,
                                    data_path=os.path.join(
                                        expanduser("~"), 'rli-daten',
                                        'open_FRED_Wetterdaten'),
                                    csv_directory=''):
    r"""
    Gets open_FRED weather data from netcdf files for the specified year, area
    and parameters and writes it to csv files.

    Parameters
    ----------
    year : int
        Year to get weather data for.
    lat_min : float
        Lower latitude bound to define area for which to get weather data.
    lat_max : float
        Upper latitude bound to define area for which to get weather data.
    lon_min : float
        Lower longitude bound to define area for which to get weather data.
    lon_max : float
        Upper longitude bound to define area for which to get weather data.
    parameter_list : list
        List of parameters to get, e.g. ['wss_10m', 'dni']. See keys of
        helper_dict for possible options.
    data_path : String
        Path to open_FRED netcdf files.
        Default: '~/rli-daten/open_FRED_Wetterdaten'.
    csv_directory : String
        Directory to store csv files into. Default: ''.

    """

    # set up helper dictionary for path to netcdf files and name to save the
    # dataframes under
    main_startswith = 'oF_00625_MERRA2_expC17.'
    helper_dict = {
        # wind speed 10 m
        'wss_10m': {
            'path': os.path.join(data_path, 'WSS_zlevel'),
            'startswith': main_startswith + 'WSS_10M.' + str(year),
            'filename': 'wind_speed-10m.csv'
        },
        # wind speed 80 m
        'wss_80m': {
            'path': os.path.join(data_path, 'WSS_zlevel'),
            'startswith': main_startswith + 'WSS_80M.' + str(year),
            'filename': 'wind_speed-80m.csv'
        },
        # wind speed 100 m
        'wss_100m': {
            'path': os.path.join(data_path, 'WSS_zlevel'),
            'startswith': main_startswith + 'WSS_100M.' + str(year),
            'filename': 'wind_speed-100m.csv'
        },
        # wind speed 120 m
        'wss_120m': {
            'path': os.path.join(data_path, 'WSS_zlevel'),
            'startswith': main_startswith + 'WSS_120M.' + str(year),
            'filename': 'wind_speed-120m.csv'
        },
        # temperature 10 m
        'temp_10m': {
            'path': os.path.join(data_path, 'T_zlevel'),
            'startswith': main_startswith + 'T_10M.' + str(year),
            'filename': 'temperature-10m.csv'
        },
        # temperature 80 m
        'temp_80m': {
            'path': os.path.join(data_path, 'T_zlevel'),
            'startswith': main_startswith + 'T_80M.' + str(year),
            'filename': 'temperature-80m.csv'
        },
        # temperature 100 m
        'temp_100m': {
            'path': os.path.join(data_path, 'T_zlevel'),
            'startswith': main_startswith + 'T_100M.' + str(year),
            'filename': 'temperature-100m.csv'
        },
        # temperature 120 m
        'temp_120m': {
            'path': os.path.join(data_path, 'T_zlevel'),
            'startswith': main_startswith + 'T_120M.' + str(year),
            'filename': 'temperature-120m.csv'
        },
        # pressure 10 m
        'pressure_10m': {
            'path': os.path.join(data_path, 'P_zlevel'),
            'startswith': main_startswith + 'P_10M.' + str(year),
            'filename': 'pressure-10m.csv'
        },
        # pressure 80 m
        'pressure_80m': {
            'path': os.path.join(data_path, 'P_zlevel'),
            'startswith': main_startswith + 'P_80M.' + str(year),
            'filename': 'pressure-80m.csv'
        },
        # pressure 100 m
        'pressure_100m': {
            'path': os.path.join(data_path, 'P_zlevel'),
            'startswith': main_startswith + 'P_100M.' + str(year),
            'filename': 'pressure-100m.csv'
        },
        # pressure 120 m
        'pressure_120m': {
            'path': os.path.join(data_path, 'P_zlevel'),
            'startswith': main_startswith + 'P_120M.' + str(year),
            'filename': 'pressure-120m.csv'
        },
        # z0
        'z0': {
            'path': os.path.join(data_path, 'Z0'),
            'startswith': main_startswith + 'Z0.' + str(year),
            'filename': 'roughness_length-0m.csv'
        },
        # wind_direction 10m
        'wind_direction_10m': {
            'path': os.path.join(data_path, 'WDIRlat_zlevel'),
            'startswith': main_startswith + 'WDIRlat_10M.' + str(year),
            'filename': 'wind_direction-10m.csv'
        },
        # wind_direction 80m
        'wind_direction_80m': {
            'path': os.path.join(data_path, 'WDIRlat_zlevel'),
            'startswith': main_startswith + 'WDIRlat_80M.' + str(year),
            'filename': 'wind_direction-80m.csv'
        },
        # wind_direction 100m
        'wind_direction_100m': {
            'path': os.path.join(data_path, 'WDIRlat_zlevel'),
            'startswith': main_startswith + 'WDIRlat_100M.' + str(year),
            'filename': 'wind_direction-100m.csv'
        },
        # wind_direction 120m
        'wind_direction_120m': {
            'path': os.path.join(data_path, 'WDIRlat_zlevel'),
            'startswith': main_startswith + 'WDIRlat_120M.' + str(year),
            'filename': 'wind_direction-120m.csv'
        },
        # DHI
        'dhi': {
            'path': os.path.join(data_path, 'ASWDIFD_S'),
            'startswith': main_startswith + 'ASWDIFD_S.' + str(year),
            'filename': 'dhi.csv'
        },
        # DIRHI
        'dirhi': {
            'path': os.path.join(data_path, 'ASWDIR_S'),
            'startswith': main_startswith + 'ASWDIR_S.' + str(year),
            'filename': 'dirhi.csv'
        },
        # DNI
        'dni': {
            'path': os.path.join(data_path, 'ASWDIR_NS2'),
            'startswith': main_startswith + 'ASWDIR_NS2.' + str(year),
            'filename': 'dni.csv'
        }
    }

    # read netcdf files
    df = pd.DataFrame()
    for i in parameter_list:
        for file in os.listdir(helper_dict[i]['path']):
            if file.startswith(helper_dict[i]['startswith']):
                print(file)
                data = xarray.open_dataset(os.path.join(helper_dict[i]['path'],
                                                        file))
                # select area
                data_sel = data.where((data.lat<=lat_max) &
                                      (data.lat>=lat_min) &
                                      (data.lon<=lon_max) &
                                      (data.lon>=lon_min),
                                      drop=True)
                # convert to dataframe and reset index
                data_month = data_sel.to_dataframe().drop(
                    columns=['time_bnds'])
                try:
                    data_month.drop(columns=['rotated_pole'], inplace=True)
                except:
                    pass
                data_month = data_month.set_index(
                    data_month.index.get_level_values('time'))
                df = df.append(data_month)

        del data, data_sel, data_month
        # drop duplicates
        df = df.reset_index().drop_duplicates().set_index('time')
        # set datetime index
        df.index.to_datetime()
        # sort columns
        data_col = [i for i in df.columns if i not in ['lat', 'lon']][0]
        df = df.reindex_axis([data_col, 'lat', 'lon'], axis=1)

        df.to_csv(os.path.join(csv_directory, helper_dict[i]['filename']))
        df = pd.DataFrame()


def setup_of_weather_df_pvlib(coordinates, csv_directory,
                              filename='pvlib_weather_data.csv'):
    r"""
    Gets open_FRED weather data from csv files (csv files can be set up using
    the function `get_of_weather_data_from_netcdf`) for the specified
    location and sets up a weather dataframe as needed in the pvlib. The
    dataframe is returned and stored to a csv file.

    Parameters
    ----------
    coordinates : list or None
        List with latitude and longitude. If not None data for closest
        coordinates to the given location are filtered.
    csv_directory : String
        Path to the directory containing the csv files with the weather data.
    filename : String
        Filename of csv file containing the pvlib weather dataframe.
        Default: 'pvlib_weather_data.csv'.

    Returns
    --------
    pandas.DataFrame
        DataFrame with time series for wind speed `wind_speed` in m/s,
        temperature `temp_air` in C, direct normal irradiation 'dni' in W/m²,
        direct horizontal irradiation 'dirhi' in W/m²,
        diffuse horizontal irradiation 'dhi' in W/m²,
        global horizontal irradiation 'ghi' in W/m². The row index is a
        MultiIndex with levels time, latitude and longitude.

    Notes
    ------
    The csv directory must contain the following csv files:
    'wind_speed-10m.csv', 'temperature-10m.csv', 'dhi.csv', 'dirhi.csv',
    'dni.csv', 'pressure-10m.csv'.

    """
    filename_list = ['wind_speed-10m.csv', 'temperature-10m.csv',
                     'dhi.csv', 'dirhi.csv', 'dni.csv', 'pressure-10m.csv']

    fred_data = pd.DataFrame()
    counter = 0
    for file_name in filename_list:

        # read data from csv
        file_path = os.path.join(csv_directory, file_name)
        data = pd.read_csv(file_path, header=[0], index_col=[0, 2, 3],
                           parse_dates=True)
        data.sort_index(inplace=True)

        # set time zone
        data = data.tz_localize('UTC', level=0)

        # filter coordinates
        if coordinates:
            lat_lon = tools.get_closest_coordinates(
                data, [coordinates[0], coordinates[1]])
            data = data.loc[(slice(None), [lat_lon['lat']],
                             [lat_lon['lon']]), :]

        # join to one dataframe
        if counter == 0:
            fred_data = data
        else:
            fred_data = fred_data.join(data, how='outer')
        counter += 1
        print(fred_data.shape)

    fred_data.rename(columns={'T': 'temp_air', 'WSS_10M': 'wind_speed',
                              'ASWDIFD_S': 'dhi', 'ASWDIR_S': 'dirhi',
                              'ASWDIR_NS2': 'dni'},
                     inplace=True)
    # add column with GHI
    fred_data['ghi'] = fred_data['dhi'] + fred_data['dirhi']
    # convert temperature from K to °C
    fred_data['temp_air'] = fred_data['temp_air'] - 273.15
    # shift time index by half an hour to have mean values for the following
    # half hour instead of the previous (this is then also consistent with
    # pandas resample)
    fred_data.reset_index(inplace=True)
    fred_data['time'] = fred_data.time - pd.Timedelta(minutes=15)
    fred_data.set_index(['time', 'lat', 'lon'], drop=True, inplace=True)
    # save as csv
    fred_data.to_csv(os.path.join(csv_directory, filename))
    return fred_data


def setup_of_weather_df_windpowerlib(coordinates, csv_directory,
                                     parameter_list,
                                     filename='windpowerlib_weather_data.csv'):
    r"""
    Gets open_FRED weather data from csv files (csv files can be set up using
    the function `get_of_weather_data_from_netcdf`) for the specified
    location and sets up a weather dataframe as needed in the windpowerlib. The
    dataframe is returned and stored to a csv file.

    Parameters
    ----------
    coordinates : list or None
        List with latitude and longitude. If not None data for closest
        coordinates to the given location are filtered.
    csv_directory : String
        Path to the directory containing the csv files with the weather data.
    parameter_list : list
        List with csv file names of files where the needed weather parameters
        are stored in, e.g. ['wind_speed-10m.csv', 'wind_speed-80m.csv'].
    filename : String
        Filename of csv file containing the pvlib weather dataframe.
        Default: 'weather_data.csv'.

    Returns
    --------
    pandas.DataFrame
        DataFrame with time series for wind speed `wind_speed` in m/s and
        optionally temperature `temperature` in K, roughness length
        `roughness_length in m, pressure `pressure` in Pa and wind direction
        `wind direction`, depending on what is specified in `parameter_list`.
        The columns of the DataFrame are a MultiIndex where the first level
        contains the variable name as string (e.g. 'wind_speed') and the
        second level contains the height as integer in m at which it applies
        (e.g. 10, if it was measured at a height of 10 m). The row index is a
        MultiIndex with levels time, latitude and longitude.

    """

    fred_data = pd.DataFrame()
    counter = 0
    for file_name in parameter_list:

        # get variable name and height from file name
        col_name = file_name.split('-')[0]
        col_height = int(file_name.split('-')[1].split('.')[0][0:-1])
        file_path = os.path.join(csv_directory, file_name)

        data = pd.read_csv(file_path, header=[0], index_col=[0, 2, 3],
                           parse_dates=True)

        data.sort_index(inplace=True)
        # set column multiindex
        data.columns = [[col_name],[col_height]]

        data = data.tz_localize('UTC', level=0)

        if coordinates:
            # get weather data for location closest to the given location
            lat_lon = tools.get_closest_coordinates(
                data, [coordinates[0], coordinates[1]])
            data = data.loc[(slice(None), [lat_lon['lat']],
                             [lat_lon['lon']]), :]

        # roughness length is given as hourly values and resampled to
        # half-hourly values to have the same resolution as the other
        # parameters
        if col_name == 'roughness_length':
            coordinates_list = data.reset_index(level=[1, 2]).groupby(
                ['lat', 'lon']).size().reset_index().drop(
                [0], axis=1).values.tolist()
            df_point_all = pd.DataFrame()
            for coordinates in coordinates_list:
                df_point = data.loc[(slice(None), [coordinates[0]],
                                     [coordinates[1]]), :].reset_index(
                    level=[1, 2])
                df_point = df_point.asfreq('30Min', method='pad')
                df_point_all = df_point_all.append(df_point)
            # reset index
            data = df_point_all.reset_index().set_index(
                ['time', 'lat', 'lon'])
            data.sort_index(inplace=True)

        # join to one dataframe
        if counter == 0:
            fred_data = data
        else:
            fred_data = fred_data.join(data, how='outer')
        counter += 1
        print(fred_data.shape)
    # shift time index by half an hour to have mean values for the following
    # half hour instead of the previous (this is then also consistent with
    # pandas resample)
    fred_data.reset_index(inplace=True)
    fred_data['time'] = fred_data.time - pd.Timedelta(minutes=30)
    fred_data.set_index(['time', 'lat', 'lon'], drop=True, inplace=True)
    # save as csv
    fred_data.to_csv(os.path.join(csv_directory, filename))
    return fred_data


def read_of_weather_df_pvlib_from_csv(path, filename, coordinates=None):
    r"""
    Reads open_FRED weather dataframe created with function
    `setup_of_weather_df_pvlib` from csv file.

    Parameters
    ----------
    path : String
        Path to the directory containing the csv file.
    filename : String
        Filename of csv file containing the multiindex weather dataframe.
    coordinates : list or None
        List with latitude and longitude. If not None data for closest
        coordinates to the given location are filtered.

    Returns
    --------
    pandas.DataFrame
        DataFrame with time series for wind speed `wind_speed` in m/s,
        temperature `temp_air` in C, direct normal irradiation 'dni' in W/m²,
        direct horizontal irradiation 'dirhi' in W/m²,
        diffuse horizontal irradiation 'dhi' in W/m²,
        global horizontal irradiation 'ghi' in W/m².

    """

    weather_df = pd.read_csv(os.path.join(path, filename),
                             header=[0], index_col=[0, 1, 2],
                             parse_dates=True)

    if coordinates:
        # get weather data for location closest to the given location
        lat_lon = tools.get_closest_coordinates(weather_df, coordinates)
        weather_df = weather_df.loc[(slice(None), [lat_lon['lat']],
                                     [lat_lon['lon']]), :].reset_index(
            level=[1,2])
    else:
        weather_df = weather_df.reset_index(level=[1, 2])

    # set time zone
    weather_df = weather_df.tz_localize('UTC')
    return weather_df


def read_of_weather_df_windpowerlib_from_csv(path, filename, coordinates=None):
    r"""
    Reads open_FRED multiindex weather dataframe created with function
    `setup_of_weather_df_windpowerlib` from csv file.

    Parameters
    ----------
    path : String
        Path to the directory containing the csv file.
    filename : String
        Filename of csv file containing the multiindex weather dataframe.
    coordinates : list or None
        List with latitude and longitude. If not None data for closest
        coordinates to the given location are filtered.

    Returns
    --------
    pandas.DataFrame
        The columns of the DataFrame are a MultiIndex where the first level
        contains the variable name as string (e.g. 'wind_speed') and the
        second level contains the height as integer in m at which it applies
        (e.g. 10, if it was measured at a height of 10 m).

    """

    weather_df = pd.read_csv(os.path.join(path, filename),
                             header=[0, 1], index_col=[0, 1, 2],
                             parse_dates=True)

    # change type of height from str to int by resetting columns
    weather_df.columns = [weather_df.axes[1].levels[0][
                              weather_df.axes[1].labels[0]],
                          weather_df.axes[1].levels[1][
                              weather_df.axes[1].labels[1]].astype(int)]

    if coordinates:
        lat_lon = tools.get_closest_coordinates(weather_df, coordinates)
        weather_df = weather_df.loc[(slice(None), [lat_lon['lat']],
                                     [lat_lon['lon']]), :].reset_index(
            level=[1,2])
    else:
        weather_df = weather_df.reset_index(level=[1, 2])

    # set time zone
    weather_df = weather_df.tz_localize('UTC')
    return weather_df


if __name__ == '__main__':

    ##########################################################################
    # read open_FRED netcdf files
    ##########################################################################

    # # choose year and area
    # # SH lat_min = 54.4, lat_max = 54.7, lon_min = 8.9, lon_max = 9.1
    # # Berlin NW: 52.661962, 13.102158
    # # Berlin SO: 52.255534, 13.866914
    # # BB NW: 52.905026, 11.982852
    # # BB SO: 51.517393, 14.860673
    # year = 2015
    # lat_min = 54.4
    # lat_max = 54.7
    # lon_min = 8.9
    # lon_max = 9.1
    #
    # # choose keys from helper_dict for which you want to load open_FRED
    # # weather_data
    # # wind data for Sabine
    # parameter_list = ['wss_10m',
    #                   'wss_80m', 'wss_100m', 'wss_120m',
    #                   'temp_10m',
    #                   'temp_80m', 'temp_100m', 'temp_120m',
    #                   'pressure_10m', 'pressure_80m', 'pressure_100m',
    #                   'pressure_120m',
    #                   'z0',
    #                   'wind_direction_10m', 'wind_direction_80m',
    #                   'wind_direction_100m', 'wind_direction_120m'
    #                   ]
    # # # radiation data
    # # parameter_list = ['wss_10m', 'temp_10m', 'dhi', 'dirhi', 'dni']
    #
    # get_of_weather_data_from_netcdf(year, lat_min, lat_max, lon_min, lon_max,
    #                                 parameter_list,
    #                                 csv_directory='data/Fred/SH_2015')

    ##########################################################################
    # set up weather dataframe for pvlib from open_FRED csv files
    ##########################################################################

    # coordinates = [52.456032, 13.525282]
    # csv_directory = 'data/Fred/BB_2015'
    # pvlib_weather_df = setup_of_weather_df_pvlib(
    #     coordinates, csv_directory, filename='fred_data_htw_2015.csv')

    ##########################################################################
    # set up multiindex weather dataframe for windpowerlib from open_FRED csv
    # files
    ##########################################################################

    # # coordinates_wf_1 = [52.407386, 13.966889]
    # # coordinates_wf_2 = [51.775147, 13.560156]
    # # coordinates_wf_3 = [52.860588, 13.070485]
    # coordinates = None
    # csv_directory = 'data/Fred/SH_2015'
    # parameter_list = ['wind_speed-10m.csv', 'wind_speed-80m.csv',
    #                   'wind_speed-100m.csv', 'wind_speed-120m.csv',
    #                   'wind_direction-10m.csv', 'wind_direction-80m.csv',
    #                   'wind_direction-100m.csv', 'wind_direction-120m.csv',
    #                   'pressure-10m.csv', 'pressure-80m.csv',
    #                   'pressure-100m.csv', 'pressure-120m.csv',
    #                   'temperature-10m.csv', 'temperature-80m.csv',
    #                   'temperature-100m.csv', 'temperature-120m.csv',
    #                   'roughness_length-0m.csv']
    # windpowerlib_weather_df = setup_of_weather_df_windpowerlib(
    #     coordinates, csv_directory, parameter_list,
    #     filename='fred_data_2015_SH.csv')

    ##########################################################################
    # read multiindex weather dataframe for windpowerlib from csv
    ##########################################################################

    # coordinates = [54.516, 8.96]
    # path = 'data/Fred/SH_2015'
    # filename = 'fred_data_2015_sh.csv'
    # read_of_weather_df_windpowerlib_from_csv(path, filename, coordinates)

    ##########################################################################
    # read weather dataframe for pvlib from csv
    ##########################################################################

    coordinates = [54.516, 8.96]
    path = 'data/Fred/Berlin_2015'
    filename = 'fred_data_2015_sh.csv'
    read_of_weather_df_pvlib_from_csv(path, filename, coordinates)
