import os
import pandas as pd
import matplotlib.pyplot as mpl

from windpowerlib.modelchain import ModelChain
from windpowerlib.wind_turbine import WindTurbine

import get_weather_data
import read_greenwind_data
import analysis_tools


def rmse(df, resample_rule):
    r"""
    Calculates the RMSE between two columns of a dataframe.

    Parameters
    ----------
    df : pandas.DataFrame
       RMSE for the first two columns is calculated.
    resample_rule : String
       The offset string representing target conversion of
       pandas.DataFrame.resample, e.g. '1D' to downsample data to one day.

    Returns
    -------
    pandas.Series
       Series with RMSE values for each time interval.

    """
    return df.resample(resample_rule).agg(
        {'variability': lambda x: ((x[df.columns[0]] - x[
            df.columns[1]]) ** 2).mean() ** .5}).iloc[:, 0]


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


if __name__ == '__main__':

    windfarm = 'WF3'  # {'WF1', 'WF2', 'WF3'}
    year = 2015

    # read windfarm and weather data
    weather_data_directory = 'data/Fred/BB_2015'
    weather_data_file = 'fred_data_2015_{}.csv'.format(windfarm)
    weather_data = 'open_FRED'
    windfarm_df, weather_data = get_data(
        year, windfarm, weather_data_directory, weather_data_file,
        weather_data)

    # calculate and plot monthly correlation for wind speed and direction
    resample_rule = '1M'
    plot_directory = 'telko/wind'
    parameter = 'wind_speed'
    wind_speed_df = compare_weather_parameters(
        windfarm_df, weather_data, parameter, resample_rule, plot_directory)
    parameter = 'wind_dir'
    wind_dir_df = compare_weather_parameters(
        windfarm_df, weather_data, parameter, resample_rule, plot_directory)