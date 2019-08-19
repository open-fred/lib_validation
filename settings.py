import os

def init():
    ## path to server
    path_to_server = '/home/sabine/rl-institut'
    ## weather
    global weather_data_path, path_era5_netcdf, path_time_series_50_Hz
    # path to csv weather files
    weather_data_path = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/weather_data'

    ## time series
    global path_time_series_bb
    # path to time series
    path_time_series_bb = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/time_series/wind/Folie_8_brandenburg/'

    ## validation
    # path to validation metrics paper
    global path_validation_metrics_bb
    path_validation_metrics_bb = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/validation_metrics/wind/Folie_8_brandenburg/'

