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
            'filename': 'wind_speed-10m.csv'
        },
        # wind speed 80 m
        'wss_80m': {
            'path': os.path.join(main_path, 'WSS_zlevel'),
            'startswith': main_startswith + 'WSS_80M.' + str(year),
            'filename': 'wind_speed-80m.csv'
        },
        # wind speed 100 m
        'wss_100m': {
            'path': os.path.join(main_path, 'WSS_zlevel'),
            'startswith': main_startswith + 'WSS_100M.' + str(year),
            'filename': 'wind_speed-100m.csv'
        },
        # wind speed 120 m
        'wss_120m': {
            'path': os.path.join(main_path, 'WSS_zlevel'),
            'startswith': main_startswith + 'WSS_120M.' + str(year),
            'filename': 'wind_speed-120m.csv'
        },
        # temperature 10 m
        'temp_10m': {
            'path': os.path.join(main_path, 'T_zlevel'),
            'startswith': main_startswith + 'T_10M.' + str(year),
            'filename': 'temperature-10m.csv'
        },
        # temperature 80 m
        'temp_80m': {
            'path': os.path.join(main_path, 'T_zlevel'),
            'startswith': main_startswith + 'T_80M.' + str(year),
            'filename': 'temperature-80m.csv'
        },
        # temperature 100 m
        'temp_100m': {
            'path': os.path.join(main_path, 'T_zlevel'),
            'startswith': main_startswith + 'T_100M.' + str(year),
            'filename': 'temperature-100m.csv'
        },
        # temperature 120 m
        'temp_120m': {
            'path': os.path.join(main_path, 'T_zlevel'),
            'startswith': main_startswith + 'T_120M.' + str(year),
            'filename': 'temperature-120m.csv'
        },
        # pressure 10 m
        'pressure_10m': {
            'path': os.path.join(main_path, 'P_zlevel'),
            'startswith': main_startswith + 'P_10M.' + str(year),
            'filename': 'pressure-10m.csv'
        },
        # pressure 80 m
        'pressure_80m': {
            'path': os.path.join(main_path, 'P_zlevel'),
            'startswith': main_startswith + 'P_80M.' + str(year),
            'filename': 'pressure-80m.csv'
        },
        # pressure 100 m
        'pressure_100m': {
            'path': os.path.join(main_path, 'P_zlevel'),
            'startswith': main_startswith + 'P_100M.' + str(year),
            'filename': 'pressure-100m.csv'
        },
        # pressure 120 m
        'pressure_120m': {
            'path': os.path.join(main_path, 'P_zlevel'),
            'startswith': main_startswith + 'P_120M.' + str(year),
            'filename': 'pressure-120m.csv'
        },
        # z0
        'z0': {
            'path': os.path.join(main_path, 'Z0'),
            'startswith': main_startswith + 'Z0.' + str(year),
            'filename': 'roughness_length-0m.csv'
        },
        # wind_direction 10m
        'wind_direction_10m': {
            'path': os.path.join(main_path, 'WDIRlat_zlevel'),
            'startswith': main_startswith + 'WDIRlat_10M.' + str(year),
            'filename': 'wind_direction-10m.csv'
        },
        # wind_direction 80m
        'wind_direction_80m': {
            'path': os.path.join(main_path, 'WDIRlat_zlevel'),
            'startswith': main_startswith + 'WDIRlat_80M.' + str(year),
            'filename': 'wind_direction-80m.csv'
        },
        # wind_direction 100m
        'wind_direction_100m': {
            'path': os.path.join(main_path, 'WDIRlat_zlevel'),
            'startswith': main_startswith + 'WDIRlat_100M.' + str(year),
            'filename': 'wind_direction-100m.csv'
        },
        # wind_direction 120m
        'wind_direction_120m': {
            'path': os.path.join(main_path, 'WDIRlat_zlevel'),
            'startswith': main_startswith + 'WDIRlat_120M.' + str(year),
            'filename': 'wind_direction-120m.csv'
        },
        # DHI
        'dhi': {
            'path': os.path.join(main_path, 'ASWDIFD_S'),
            'startswith': main_startswith + 'ASWDIFD_S.' + str(year),
            'filename': 'dhi.csv'
        },
        # DIRHI
        'dirhi': {
            'path': os.path.join(main_path, 'ASWDIR_S'),
            'startswith': main_startswith + 'ASWDIR_S.' + str(year),
            'filename': 'dirhi.csv'
        },
        # DNI
        'dni': {
            'path': os.path.join(main_path, 'ASWDIR_NS'),
            'startswith': main_startswith + 'ASWDIR_NS.' + str(year),
            'filename': 'dni.csv'
        },
        # DNI_2
        'dni_2': {
            'path': os.path.join(main_path, 'ASWDIR_NS2'),
            'startswith': main_startswith + 'ASWDIR_NS2.' + str(year),
            'filename': 'dni_2.csv'
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

        df.to_csv(helper_dict[i]['filename'])
        df = pd.DataFrame()


if __name__ == '__main__':

    # choose year and area
    # SH lat_min = 54.4, lat_max = 54.7, lon_min = 8.9, lon_max = 9.1
    # Berlin NW: 52.661962, 13.102158
    # Berlin SO: 52.255534, 13.866914
    # SH bis BB NW: 54.991143, 7.496458
    # SH bis BB SO: 51.288288, 15.176050
    # BB NW: 52.905026, 11.982852
    # BB SO: 51.517393, 14.860673
    year = 2015
    lat_min = 51.517393
    lat_max = 52.905026
    lon_min = 11.982852
    lon_max = 14.860673
    # year = 2016
    # lat_min = 54.4
    # lat_max = 54.7
    # lon_min = 8.9
    # lon_max = 9.1

    # choose keys from helper_dict for which you want to load open_FRED
    # weather_data
    # wind data for Sabine
    load_data_list = [#'wss_10m',
                      #'wss_80m', 'wss_100m', 'wss_120m',
                      #'temp_10m',
                      #'temp_80m', 'temp_100m', 'temp_120m',
                      # 'pressure_10m', 'pressure_80m', 'pressure_100m',
                      # 'pressure_120m',
                      'z0'
                      #'wind_direction_10m', 'wind_direction_80m',
                      #'wind_direction_100m', 'wind_direction_120m'
                      ]
    # # radiation data
    # load_data_list = ['wss_10m', 'temp_10m',
    #                   'dhi', 'dirhi', 'dni', 'dni_2']

    get_of_weather_data_from_netcdf(year, lat_min, lat_max, lon_min, lon_max,
                                    load_data_list)
