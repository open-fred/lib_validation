import os
import pandas as pd
import matplotlib.pyplot as mpl
import numpy as np

from windpowerlib.modelchain import ModelChain
from windpowerlib.wind_turbine import WindTurbine

import get_weather_data
import read_greenwind_data
import analysis_tools
import wind_farm_specifications
from argenetz_data import get_argenetz_data


def get_data(year, windfarm, weather_data_directory, weather_data_file,
             weather_data='open_FRED'):

    # read windpark data
    windfarm_df = read_greenwind_data.read_windfarm_dataframe(year, windfarm)
    windfarm_df = windfarm_df.tz_localize('UTC')

    # get weather data
    if weather_data == 'open_FRED':
        weather_data = \
            get_weather_data.read_of_weather_df_windpowerlib_from_csv(
                weather_data_directory, weather_data_file)
        # resample to same resolution as FRED weather data
        windfarm_df = windfarm_df.resample('30Min').mean()
    return windfarm_df, weather_data


def compare_weather_parameters(windfarm_df, weather_data, parameter,
                               resample_rule, plot_directory):
    # evaluation only for fred data so far
    # define hub height and heights closest to hub height for wind direction
    hub_height = {'WF1': 105, 'WF2': 105, 'WF3': 60}
    wind_direction_height = {'WF1': [100, 120], 'WF2': [100, 120],
                             'WF3': [80, 10]}

    # columns containing the parameter
    parameter_cols = [i for i in windfarm_df if parameter in i]
    df = windfarm_df[parameter_cols]

    if parameter == 'wind_speed':
        # get wind speed at hub height using the ModelChain of the windpowerlib
        wt = WindTurbine(**{'turbine_name': 'VESTAS V 90 2000',
                            'hub_height': hub_height[windfarm],
                            'rotor_diameter': 127})
        mc = ModelChain(wt)
        wind_speed_hub = mc.wind_speed_hub(weather_data)
        wind_speed_hub.name = 'wind_speed_hub'

        df = df.join(wind_speed_hub.to_frame())

    elif parameter == 'wind_dir':
        df = df.join(weather_data['wind_direction'][
                         wind_direction_height[windfarm][0]].to_frame())
        df = df.join(weather_data['wind_direction'][
                         wind_direction_height[windfarm][1]].to_frame())

    # calculate correlation for each wind turbine in the windpark
    counter = 0
    for col_name in parameter_cols:
        corr_df_tmp = df[[col_name, 'wind_speed_hub']]
        corr = analysis_tools.correlation(corr_df_tmp, resample_rule)
        if counter == 0:
            corr_df = corr.to_frame()
        else:
            corr_df = corr_df.join(corr.to_frame())
        counter += 1

    # plot correlation
    corr_df.plot(figsize=(15, 10))
    mpl.savefig(os.path.join(
        plot_directory, '{}_correlation_{}_{}.pdf'.format(
            parameter, resample_rule, windfarm)))
    return df


def plot(df, windfarm, plot_directory, parameter):
    # plot january week
    single_turbine = {'WF1': '6_8', 'WF2': '7_1', 'WF3': '8_2'}
    index = pd.date_range(start='1/25/2015', end='2/1/2015',
                          freq='30Min', tz='UTC')
    df.loc[index, :].plot(figsize=(15, 10))
    mpl.savefig('telko/wind/wind_speed_january_week_{}.pdf'.format(windfarm))
    df[['wf_{}_wind_speed'.format(single_turbine[windfarm]),
                   'wind_speed_hub']].loc[index, :].plot(figsize=(15, 10))
    mpl.savefig('telko/wind/wind_speed_january_week_{}_single.pdf'.format(
        windfarm))

    # plot june week
    index = pd.date_range(start='6/2/2015', end='6/8/2015',
                          freq='30Min', tz='UTC')
    df.loc[index, :].plot(figsize=(15, 10))
    mpl.savefig(os.path.join(plot_directory, '{}_june_week_{}.pdf'.format(
        parameter, windfarm)))
    df[['wf_{}_wind_speed'.format(single_turbine[windfarm]),
                   'wind_speed_hub']].loc[index, :].plot(figsize=(15, 10))
    mpl.savefig('telko/wind/wind_speed_june_week_{}_single.pdf'.format(
        windfarm))

    # plot january week
    index = pd.date_range(start='1/25/2015', end='2/1/2015',
                          freq='30Min', tz='UTC')
    wind_direction_df.loc[index, :].plot(figsize=(15, 10))
    mpl.savefig('telko/wind/wind_direction_january_week_{}.pdf'.format(windfarm))
    wind_direction_df[['wf_{}_wind_dir'.format(single_turbine[windfarm]),
                       wind_direction_height[windfarm][0]]].loc[index, :].plot(
        figsize=(15, 10))
    mpl.savefig('telko/wind/wind_direction_january_week_{}_single.pdf'.format(
        windfarm))
    # plot june week
    index = pd.date_range(start='6/2/2015', end='6/8/2015',
                          freq='30Min', tz='UTC')
    wind_direction_df.loc[index, :].plot(figsize=(15, 10))
    mpl.savefig('telko/wind/wind_direction_june_week_{}.pdf'.format(windfarm))
    wind_direction_df[['wf_{}_wind_dir'.format(single_turbine[windfarm]),
                       wind_direction_height[windfarm][0]]].loc[index, :].plot(
        figsize=(15, 10))
    mpl.savefig('telko/wind/wind_direction_june_week_{}_single.pdf'.format(
        windfarm))


def run_arge_validation(year):
    # Get wind farm data
    wind_farm_data = wind_farm_specifications.get_wind_farm_data(
        'farm_specification_argenetz_{0}.p'.format(year),
        os.path.join(os.path.dirname(__file__),
                     'dumps/wind_farm_data'),
        pickle_load=True)
    # Get ArgeNetz Data
    arge_pickle_filename = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'dumps/validation_data',
        'arge_netz_data_{0}.p'.format(year)))
    validation_data = get_argenetz_data(
        year, pickle_load=True, filename=arge_pickle_filename,
        csv_dump=False, plot=False)

    # Nordstrand
    '{}_power_output'
    return


if __name__ == '__main__':

    year = 2015
    windfarms = ['wf_1', 'wf_2', 'wf_3','wf_4', 'wf_5']

    # compare daily variability
    var_merra = pd.read_csv(
        'Auswertungen_20180212/daily_variability_SH_MERRA_{}.csv'.format(year),
        header=[0], index_col=[0], parse_dates=True)
    var_fred = pd.read_csv(
        'Auswertungen_20180212/daily_variability_SH_open_FRED_{}.csv'.format(
            year),
        header=[0], index_col=[0], parse_dates=True)

    windfarm = 'wf_2'
    col_1 = var_merra['daily_variability_{}'.format(windfarm)]
    col_2 = var_fred['daily_variability_{}'.format(windfarm)]
    df = col_1.to_frame().join(
        col_2.to_frame(), how='outer',
        lsuffix='_merra', rsuffix='_fred').dropna(how='all')
    df.plot()
    mpl.savefig('daily_variability_{}_MERRA_FRED_{}.png'.format(
        windfarm, year))
    mpl.clf()


    # compare correlation
    corr_merra = pd.read_csv(
        'Auswertungen_20180212/weekly_correlation_SH_MERRA_{}.csv'.format(
            year),
        header=[0], index_col=[0], parse_dates=True)
    corr_fred = pd.read_csv(
        'Auswertungen_20180212/weekly_correlation_SH_open_FRED_{}.csv'.format(
            year),
        header=[0], index_col=[0], parse_dates=True)

    windfarm = 'wf_2'
    col_1 = corr_merra['{}'.format(windfarm)]
    col_2 = corr_fred['{}'.format(windfarm)]
    df = col_1.to_frame().join(
        col_2.to_frame(), how='outer',
        lsuffix='_merra', rsuffix='_fred').dropna(how='all')
    df.plot()
    mpl.savefig('weekly_correlation_{}_MERRA_FRED_{}.png'.format(
        windfarm, year))
    mpl.clf()

    # scatter plot feedin
    feedin_merra = pd.read_csv(
        'Auswertungen_20180212/feedin_SH_MERRA_{}.csv'.format(
            year),
        header=[0], index_col=[0], parse_dates=True)
    feedin_fred = pd.read_csv(
        'Auswertungen_20180212/feedin_SH_open_FRED_{}.csv'.format(
            year),
        header=[0], index_col=[0], parse_dates=True)

    for windfarm in windfarms:
        feedin_merra.plot.scatter(x='feedin_calculated_{}'.format(windfarm),
                                  y='feedin_measured_{}'.format(windfarm))
        max_value = feedin_merra['feedin_calculated_{}'.format(windfarm)].max()
        mpl.plot([0, max_value], [0, max_value], 'r')
        mpl.savefig('feedin_measured_vs_calculated_{}_MERRA_{}.png'.format(
            windfarm, year))
        mpl.clf()

        feedin_fred.plot.scatter(x='feedin_calculated_{}'.format(windfarm),
                                 y='feedin_measured_{}'.format(windfarm))
        max_value = feedin_merra['feedin_calculated_{}'.format(windfarm)].max()
        mpl.plot([0, max_value], [0, max_value], 'r')
        mpl.savefig('feedin_measured_vs_calculated_{}_Fred_{}.png'.format(
            windfarm, year))
        mpl.clf()

    #run_arge_validation(year)

    #
    # # read windfarm and weather data
    # weather_data_directory = 'data/Fred/BB_2015'
    # weather_data_file = 'fred_data_2015_{}.csv'.format(windfarm)
    # weather_data = 'open_FRED'
    # windfarm_df, weather_data = get_data(
    #     year, windfarm, weather_data_directory, weather_data_file,
    #     weather_data)
    #
    # # calculate and plot monthly correlation for wind speed and direction
    # resample_rule = '1M'
    # plot_directory = 'telko/wind'
    # parameter = 'wind_speed'
    # wind_speed_df = compare_weather_parameters(
    #     windfarm_df, weather_data, parameter, resample_rule, plot_directory)
    # parameter = 'wind_dir'
    # wind_dir_df = compare_weather_parameters(
    #     windfarm_df, weather_data, parameter, resample_rule, plot_directory)

    # measured = validation_farms[1].power_output
    # from datetime import timedelta
    # d = timedelta(days=0.5)
    ## verschiebt den Zeitstempel der Ausgabe um einen halben Tag
    # measured.resample('1D', loffset=d).sum()
    ## starte bei Stunde 7 bzw. 19
    # measured.resample('12H', base=7).sum()
