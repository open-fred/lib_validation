# Imports from lib_validation
import tools

# Other imports
import pandas as pd
import os
import pickle


def get_open_fred_data(weather_data_name, year, filename='pickle_dump.p'):
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
                z0_series = z0_series.append(tools.upsample_series(
                    series, output_resolution=30, input_resolution='H'))
            data_frame['roughness_length'] = z0_series.values
    data_frame = data_frame.loc[:, ~data_frame.columns.duplicated()]
    data_frame = data_frame.rename(columns={'WSS_10M': 'wind_speed',
                                            'WSS': 'wind_speed_80m'})
    pickle.dump(data_frame, open(filename, 'wb'))
    return data_frame
