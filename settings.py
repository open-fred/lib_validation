import os

def init():
    ## path to server
    path_to_server = '/home/sabine/rl-institut'
    path_to_data_server = '/home/sabine/Daten_flexibel_01'

    ## validation data
    global path_greenwind, path_brandenburg
    path_greenwind = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP5 Einspeisezeitreihen/5.2 Wind/Daten_Twele/'
    path_brandenburg = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP5 Einspeisezeitreihen/5.2 Wind/Brandenburg/'

    ## weather
    global weather_data_path
    # path to csv weather files
    weather_data_path = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/weather_data'

    ## time series
    global path_time_series_bb, path_time_series_wind_speed, path_time_series_power_output, path_time_series_single_turbine
    # path to time series
    path_time_series_bb = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/time_series/wind/Folie_8_brandenburg/'
    path_time_series_wind_speed = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/time_series/wind/Folie_6_wind_speed/'
    path_time_series_power_output = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/time_series/wind/Folie_5_power_output/'
    path_time_series_single_turbine = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/time_series/wind/Folie_7_single_turbine/'


    ## validation
    # path to validation metrics paper
    global path_validation_metrics_bb, path_validation_metrics_wind_speed, path_validation_metrics_power_output, path_validation_metrics_single_turbine
    path_validation_metrics_bb = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/validation_metrics/wind/Folie_8_brandenburg/'
    path_validation_metrics_wind_speed = path_to_server + '//04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/validation_metrics/wind/Folie_6_wind_speed/'
    path_validation_metrics_power_output = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/validation_metrics/wind/Folie_5_power_output/'
    path_validation_metrics_single_turbine = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/validation_metrics/wind/Folie_7_single_turbine/'


    ## Abschlussbericht
    global brandenburg_ts_bericht, brandenburg_val_metrics_bericht, brandenburg_validation_df_bericht, brandenburg_plots_bericht
    brandenburg_ts_bericht = path_to_data_server + '/Einspeisezeitreihen_open_FRED_bericht_und_WAM/Brandenburg/time_series'
    brandenburg_validation_df_bericht = path_to_data_server + '/Einspeisezeitreihen_open_FRED_bericht_und_WAM/Brandenburg/validation_dfs'
    brandenburg_val_metrics_bericht = path_to_data_server + '/Einspeisezeitreihen_open_FRED_bericht_und_WAM/Brandenburg/validation_metrics'
    brandenburg_plots_bericht = path_to_data_server + '/Einspeisezeitreihen_open_FRED_bericht_und_WAM/Brandenburg/plots'


    ## geometries
    global path_geometries
    path_geometries = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/geometries/'