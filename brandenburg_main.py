import pandas as pd
import numpy as np
import os
import pickle

from feedin_germany import feedin as f
from feedin_germany import geometries
from feedin_germany import validation_tools as val_tools
from feedin_germany import plots


# internal imports
import settings
from brandenburg_data import get_turbine_register, get_measured_time_series

settings.init()

# set parameters
weather_data_names = [
    'open_FRED',
    'ERA5'
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
# plots_folder = settings.brandenburg_plots_bericht
# todo exchange
feedin_folder = 'temp'
val_folder = 'temp'
val_metrics_folder = 'temp'
plots_folder = 'temp'


# get region shape
if os.path.exists('region_bb_dump.p'):
    region = pickle.load(open('region_bb_dump.p', 'rb'))
else:
    region = geometries.load_polygon('uckermark')
    pickle.dump(region, open('region_bb_dump.p', 'wb'))


for weather_data_name in weather_data_names:
    for year in years:
        # get register
        register = get_turbine_register(year)
        for case in cases:
            print('Calculating feed-in for weather dataset {}, year {} and'
                  ' case {}.'.format(weather_data_name, year, case))
            feedin = f.calculate_feedin_germany(
                year=year, categories=['Wind'], regions=region,
                register_name=register,
                weather_data_name=weather_data_name,
                wake_losses_model=windpowerlib_parameters[case]['wake_losses_model'],
                return_feedin=True,
                smoothing=windpowerlib_parameters[case]['smoothing'])
            feedin.set_index('time').to_csv(os.path.join(
                feedin_folder, 'feedin_brandenburg_{}_{}_{}.csv'.format(
                    weather_data_name, year, case)))

# get validation time series for all years
if os.path.exists('val_dump.p'):
    val_feedin = pickle.load(open('val_dump.p', 'rb'))
else:
    val_feedin = pd.DataFrame()
    for year in years:
        val_feedin_year = get_measured_time_series(year=year)
        val_feedin = pd.concat([val_feedin, pd.DataFrame(val_feedin_year)])
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
                                 how='left', on=['time'])
        validation_df.set_index('time').to_csv(os.path.join(
            val_folder, 'validation_df_{}_{}.csv'.format(
                weather_data_name, case)))


def get_combined_df():
    complete_df = pd.DataFrame()
    for weather_data_name in weather_data_names:
        for case in cases:
            val_filename = os.path.join(
                val_folder, 'validation_df_{}_{}.csv'.format(
                    weather_data_name, case))
            validation_df = pd.read_csv(val_filename, parse_dates=True,
                                        index_col=0)
            validation_df['weather'] = weather_data_name
            validation_df['case'] = case
            complete_df = pd.concat([complete_df, validation_df])
    return complete_df


###############################################################################
# calculate metrics and save to file
###############################################################################
metrics = ['rmse_norm', 'rmse_norm_bias_corrected', 'mean_bias', 'rmse',
           'pearson', 'energy_yield_deviation', 'time_step_amount']

complete_df = get_combined_df()

filename = os.path.join(val_metrics_folder, 'validation_metrics_MW.csv')
val_tools.calculate_validation_metrics(
    df=complete_df, val_cols=['feedin', 'feedin_val'], metrics=metrics,
    unit_factor=1e6, filter_cols=['weather', 'case'],
    filename=filename)


###############################################################################
# plots
###############################################################################

###### qq plots
years = [2016, 2017]
# years = None

for weather_data_name in weather_data_names:
    for case in cases:
        # load validation data frame
        val_filename = os.path.join(
            val_folder, 'validation_df_{}_{}.csv'.format(
                weather_data_name, case))
        validation_df = pd.read_csv(val_filename, parse_dates=True,
                                    index_col=0)
        # feed-in in MW
        validation_df['feedin'] = validation_df['feedin'] / 1e6
        validation_df['feedin_val'] = validation_df['feedin_val'] / 1e6

        if years:
            for year in years:
                filename_plot = os.path.join(
                    plots_folder, 'qq_plot_{}_{}_{}.png'.format(
                        weather_data_name, case, year))
                maximum = None
                plot_title = None
                df_year = validation_df.loc[validation_df.index.year == year]
                plots.plot_correlation(
                    df=df_year, val_cols=['feedin', 'feedin_val'],
                    filename=filename_plot, title=plot_title,
                    ylabel='Calculated feed-in in MW',
                    xlabel='Validation feed-in in MW', color='darkblue',
                    marker_size=3, maximum=maximum)
        else:
            filename_plot = os.path.join(
                plots_folder, 'qq_plot_{}_{}.png'.format(weather_data_name, case))
            maximum = None
            plot_title = None
            plots.plot_correlation(
                df=validation_df, val_cols=['feedin', 'feedin_val'],
                filename=filename_plot, title=plot_title,
                ylabel='Calculated feed-in in MW',
                xlabel='Validation feed-in in MW', color='darkblue',
                marker_size=3, maximum=maximum)

###### Leistungshistogramm / ramps
freq = 5.0  # for ramps 1.0
settings = [
    None,
    'smoothing_1',
    'smoothing_2',
    'ramps'
    ]


complete_df = get_combined_df()
# filter and rename for histogram function
hist_df = pd.DataFrame()
filter_cols = ['case', 'weather']
val_cols = ['feedin', 'feedin_val']
filter_df = complete_df.groupby(filter_cols).size().reset_index().drop(
            columns=[0], axis=1)
for filters, index in zip(filter_df.values, filter_df.index):
    # select time series by filters
    complete_df['temp'] = complete_df[filter_cols].isin(filters).all(axis=1)
    df = complete_df.loc[complete_df['temp'] == True][val_cols]
    complete_df.drop(columns=['temp'], inplace=True)
    if filters[0] == 'smoothing':
        add_on = '_smoothed'
    else:
        add_on = ''
    df.rename(columns={'feedin': 'feedin_{}{}'.format(filters[1], add_on)},
              inplace=True)
    if index != 0:
        df.drop(columns=['feedin_val'], inplace=True)
    hist_df = pd.concat([hist_df, df], axis=1)

# calculate ramp
ind_2 = hist_df.index - pd.Timedelta(hours=1)
cols = ['feedin_{}'.format(_) for _ in weather_data_names]
cols.append('feedin_val')
for col in cols:
    hist_df['ramp_{}'.format(col)] = \
        hist_df.loc[:, col].values - \
        hist_df.loc[ind_2, col].values

for setting_name in settings:
    if setting_name == 'ramps':
        freq = 1.0
    else:
        freq = freq
    if setting_name is None:
        setting_for_filename = 'weather'
    else:
        setting_for_filename = setting_name
    filename = os.path.join(plots_folder,
                            'histogram_brandenburg_{}_compare'.format(
        setting_for_filename.replace('1', 'open_FRED').replace('2', 'ERA5')))
    plots.histogram(hist_df, filename=filename,
                  freq=freq, setting=setting_name, unit='MW', unit_factor=1e6)
