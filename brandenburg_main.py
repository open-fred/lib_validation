import pandas as pd
import numpy as np
import os
import pickle

# feedinlib imports
from feedinlib import tools as feedinlib_tools

# windpowerlib imports
from windpowerlib import wind_turbine as wt
from windpowerlib import wind_farm as wf
from windpowerlib import turbine_cluster_modelchain as tc_mc

from feedin_germany import feedin as f
from feedin_germany import geometries
from feedin_germany import power_plant_register_tools as ppr_tools


# internal imports
import tools
import validation_tools as val_tools
import settings
from brandenburg_data import get_turbine_register, get_measured_time_series

settings.init()

# set parameters
weather_data_names = [
    'open_FRED',  # todo check resolution
    # 'ERA5'
]

years = [
    2016,
    2017
]

cases = [
    # 'aggregation',
    'smoothing',
    'wake_losses'
]

windpowerlib_parameters = {
    # 'aggregation': {'smoothing': False,
    #                 'wake_losses_model': None},
    'smoothing': {'smoothing': True,
                  'wake_losses_model': 'dena_mean'},
    'wake_losses': {'smoothing': False,
                    'wake_losses_model': 'dena_mean'}
}  # note: default values for remaining parameters

time_series_filename = settings.path_time_series_bb

# feedin_folder = settings.brandenburg_ts_bericht
# val_folder = settings.brandenburg_validation_df_bericht
# val_metrics_folder = settings.brandenburg_val_metrics_bericht
# todo exchange
feedin_folder = 'temp'
val_folder = 'temp'
val_metrics_folder = 'temp'


# get region shape
if os.path.exists('region_bb_dump.p'):
    region = pickle.load(open('region_bb_dump.p', 'rb'))
else:
    region = geometries.load_polygon('uckermark')
    pickle.dump(region, open('region_bb_dump.p', 'wb'))


# for weather_data_name in weather_data_names:
#     for year in years:
#         # get register
#         register = get_turbine_register(year)
#         for case in cases:
#             print('Calculating feed-in for weather dataset {}, year {} and'
#                   ' case {}.'.format(weather_data_name, year, case))
#             feedin = f.calculate_feedin_germany(
#                 year=year, categories=['Wind'], regions=region,
#                 register_name=register,
#                 weather_data_name=weather_data_name,
#                 wake_losses_model=windpowerlib_parameters[case]['wake_losses_model'],
#                 return_feedin=True,
#                 smoothing=windpowerlib_parameters[case]['smoothing'])
#             feedin.set_index('time').to_csv(os.path.join(
#                 feedin_folder, 'feedin_brandenburg_{}_{}_{}.csv'.format(
#                     weather_data_name, year, case)))

# get validation time series for all years
if os.path.exists('val_dump.p'):
    val_feedin = pickle.load(open('val_dump.p', 'rb'))
else:
    val_feedin = pd.DataFrame()
    for year in years:
        val_feedin_year = get_measured_time_series(year=year)
        val_feedin = pd.concat([val_feedin, val_feedin_year])
    val_feedin.rename(columns={0: 'feedin_val'}, inplace=True)
    val_feedin.index.name = 'time'
    val_feedin.reset_index('time', inplace=True)
    pickle.dump(val_feedin, open('val_dump.p', 'wb'))


# load feed-in and validation time series into one data frame
for weather_data_name in weather_data_names:
    for case in cases:
        feedin_df = pd.DataFrame()
        for year in years:
            filename = os.path.join(
                feedin_folder, 'feedin_brandenburg_{}_{}_{}.csv'.format(
                    weather_data_name, year, case))
            feedin_year = pd.read_csv(filename,index_col=0,
                                      parse_dates=True).reset_index()
            feedin_df = pd.concat([feedin_df, feedin_year])

        validation_df = pd.merge(left=feedin_df, right=val_feedin,
                                 how='left', on=['time', 'nuts'])
        validation_df.set_index('time').to_csv(os.path.join(
            val_folder, 'validation_df_{}_{}.csv'.format(
                weather_data_name, case)))

###############################################################################
# calculate metrics and save to file (for each case and each weather data)
###############################################################################
for weather_data_name in weather_data_names:
    for case in cases:
        # load validation data frame
        val_filename = os.path.join(
            val_folder, 'validation_df_{}_{}.csv'.format(
                weather_data_name, case))
        validation_df = pd.read_csv(val_filename, parse_dates=True, index_col=0)
        filename = os.path.join(
            val_metrics_folder, 'validation_metrics_{weather}_{case}.csv'.format(
                case=case, weather=weather_data_name))
        val_tools.calculate_validation_metrics(
            df=validation_df,
            val_cols=['feedin', 'feedin_val'], metrics='standard',
            filter_cols=['nuts', 'technology'],
            filename=filename)