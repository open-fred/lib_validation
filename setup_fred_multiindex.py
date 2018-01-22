import pandas as pd

import tools

#############################################################################
# set up multiindex dataframe from fred weather data
#############################################################################


def fred_irradiance_df_from_csv():

    coordinates = [52.456032, 13.525282]
    file_directory = 'data/Fred/BB_2015/'

    filename_list = ['wind_speed-10m.csv', 'temperature-10m.csv',
                     'dhi.csv', 'dirhi.csv', 'dni.csv', 'dni_2.csv',
                     'pressure-10m.csv']

    fred_data = pd.DataFrame()
    counter = 0
    for file_name in filename_list:

        # get variable name and height from file name
        col_name = file_name.split('.')[0]
        file_path = file_directory + file_name

        data = pd.read_csv(file_path, header=[0], index_col=[0, 2, 3],
                           parse_dates=True)

        data.sortlevel(inplace=True)
        data = data.tz_localize('UTC', level=0)

        # filter coordinates
        lat_lon = tools.get_closest_coordinates(
            data, [coordinates[0], coordinates[1]])
        data = data.loc[(slice(None), [lat_lon['lat']], [lat_lon['lon']]),
               :].reset_index(level=[1, 2], drop=True)

        # join
        if counter == 0:
            fred_data = data
        else:
            fred_data = fred_data.join(data, how='outer')
        counter += 1
        print(fred_data.shape)

    fred_data.rename(columns={'T': 'temp_air', 'WSS_10M': 'wind_speed',
                              'ASWDIFD_S': 'dhi', 'ASWDIR_S': 'dirhi',
                              'ASWDIR_NS': 'dni', 'ASWDIR_NS2': 'dni_2'},
                     inplace=True)
    fred_data.to_csv(file_directory + 'fred_data_2015_htw.csv')

#############################################################################
# set up multiindex dataframe from fred weather data
#############################################################################


def fred_multiindex_df_from_csv():

    file_directory = 'data/Fred/SH_2015/'

    filename_list = ['wind_speed-10m.csv', 'wind_speed-80m.csv',
                     'wind_speed-100m.csv', 'wind_speed-120m.csv',
                     'wind_direction-10m.csv', 'wind_direction-80m.csv',
                     'wind_direction-100m.csv', 'wind_direction-120m.csv',
                     'pressure-10m.csv', 'pressure-80m.csv',
                     'pressure-100m.csv', 'pressure-120m.csv',
                     'temperature-10m.csv', 'temperature-80m.csv',
                     'temperature-100m.csv', 'temperature-120m.csv',
                     'roughness_length-0m.csv']

    fred_data = pd.DataFrame()
    counter = 0
    for file_name in filename_list:

        # get variable name and height from file name
        col_name = file_name.split('-')[0]
        col_height = int(file_name.split('-')[1].split('.')[0][0:-1])
        file_path = file_directory + file_name

        data = pd.read_csv(file_path, header=[0], index_col=[0, 2, 3],
                           parse_dates=True)

        data.sortlevel(inplace=True)
        # set column multiindex
        data.columns = [[col_name],[col_height]]
        print(data.shape)

        data = data.tz_localize('UTC', level=0)

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
            data.sortlevel(inplace=True)

        # join
        if counter == 0:
            fred_data = data
        else:
            fred_data = fred_data.join(data, how='outer')
        counter += 1
        print(fred_data.shape)

    fred_data.to_csv(file_directory + 'fred_data_2015_sh.csv')

#############################################################################
# read multiindex dataframe from csv
#############################################################################


def read_fred_multiindex_from_csv():

    file_directory = 'data/Merra/'
    fred_data = pd.read_csv(file_directory + 'weather_data_GER_2015.csv',
                            header=[0], index_col=[0, 2, 3], parse_dates=True)


    lat_lon = tools.get_closest_coordinates(fred_data, [54.516, 8.96])
    fred_data_park = fred_data.loc[(slice(None), [lat_lon['lat']],
                                    [lat_lon['lon']]), :].reset_index(
        level=[1,2], drop=True)


if __name__ == '__main__':
    #fred_multiindex_df_from_csv()
    fred_irradiance_df_from_csv()
    #read_fred_multiindex_from_csv()
    #a = fred_data.loc[fred_data.isnull().iloc[:,1]==True]