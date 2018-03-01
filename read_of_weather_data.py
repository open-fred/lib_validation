import xarray
import os
import pandas as pd


def get_of_weather_data_from_netcdf(year, lat_min, lat_max, lon_min, lon_max,
                                    load_data_list):

    # set up helper dictionary for path to netcdf files and name to save the
    # dataframes under
    main_path = os.path.join('/home', 'Birgit.Schachler', 'rli-daten',
                             'open_FRED_Wetterdaten')
    main_startswith = 'oF_00625_MERRA2_expC17.'
    helper_dict = {
        # wind speed 10 m
        'wss_10m': {
            'path': os.path.join(main_path, 'WSS_zlevel'),
            'startswith': main_startswith + 'WSS_10M.' + str(year),
            'filename': 'wss_10m.csv'
        },
        # wind speed 80 m
        'wss_80m': {
            'path': os.path.join(main_path, 'WSS_zlevel'),
            'startswith': main_startswith + 'WSS_80M.' + str(year),
            'filename': 'wss_80m.csv'
        },
        # temperature 10 m
        'temp_10m': {
            'path': os.path.join(main_path, 'T_zlevel'),
            'startswith': main_startswith + 'T_10M.' + str(year),
            'filename': 'temp_10m.csv'
        },
        # temperature 80 m
        'temp_80m': {
            'path': os.path.join(main_path, 'T_zlevel'),
            'startswith': main_startswith + 'T_80M.' + str(year),
            'filename': 'temp_80m.csv'
        },
        # pressure 10 m
        'pressure_10m': {
            'path': os.path.join(main_path, 'P_zlevel'),
            'startswith': main_startswith + 'P_10M.' + str(year),
            'filename': 'pressure_10m.csv'
        },
        # pressure 80 m
        'pressure_80m': {
            'path': os.path.join(main_path, 'P_zlevel'),
            'startswith': main_startswith + 'P_80M.' + str(year),
            'filename': 'pressure_80m.csv'
        },
        # z0
        'z0': {
            'path': os.path.join(main_path, 'Z0'),
            'startswith': main_startswith + 'Z0.' + str(year),
            'filename': 'z0.csv'
        }
    }

    # read netcdf files
    df = pd.DataFrame()
    for i in load_data_list:
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
                    columns=['rotated_pole', 'time_bnds'])
                data_month = data_month.set_index(
                    data_month.index.get_level_values('time'))
                df = df.append(data_month)

        del data, data_sel, data_month
        # drop duplicates
        df = df.reset_index().drop_duplicates().set_index('time')
        # set datetime index
        df.index.to_datetime()
        df.to_csv(helper_dict[i]['filename'])


if __name__ == '__main__':

    # choose year and area
    year = 2015
    lat_min = 54.4
    lat_max = 54.7
    lon_min = 8.9
    lon_max = 9.1

    # choose keys from helper_dict for which you want to load open_FRED
    # weather_data
    load_data_list = ['wss_10m', 'wss_80m']

    get_of_weather_data_from_netcdf(year, lat_min, lat_max, lon_min, lon_max,
                                    load_data_list)
