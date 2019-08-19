"""
The ``brandenburg_data`` module contains functions for validating ...
The following data is available:
- ...

DateTimeIndex in 'UTC' time zone.

"""

import pandas as pd
import numpy as np
import os

from feedinlib import tools as feedinlib_tools

# windpowerlib imports
from windpowerlib import wind_turbine as wt
from windpowerlib import wind_farm as wf
from windpowerlib import turbine_cluster_modelchain as tc_mc

# internal imports
import tools
import validation_tools as val_tools
import settings


def get_turbine_register():
    """
    Load turbine register from file.

    Returns
    -------
    df : pd.DataFrame
        - capacity in W (as in windpowerlib)

    """
    filename = os.path.join(
        settings.path_brandenburg, 'bb_turbines.csv')
    df = pd.read_csv(filename, sep=',', decimal='.', index_col=0,
                     parse_dates=True)
    # capacity in W
    df['capacity'] *= 1000
    return df


def get_measured_time_series(start=None, stop=None, completeness_limit=95.0):
    """
    completeness_limit : float
        Data contains column 'Vollständigkeit' which indicates the percentage
        of wind turbines of which data could be collected for the respective
        time step. Time steps with a percentage < `completeness_limit` are
        neglected.

    """
    filename = os.path.join(
        settings.path_brandenburg, 'bb_powerseries.csv')
    df = pd.read_csv(filename, sep=',', decimal='.',
                     parse_dates=True).rename(columns={'Von': 'time'}).rename(
        columns={'VollständigkeitDaten': 'Vollstaendigkeit'}).drop(
        'Regelvorgabe %', axis=1)
    # remove columns with 'Vollstaendigkeit' <= `completeness_limit`
    df['Vollstaendigkeit'] = df['Vollstaendigkeit'].apply(
        lambda x: x.split('%')[0]).apply(float)
    df = df.loc[df['Vollstaendigkeit'] >= completeness_limit]
    # get time series
    bb_ts = df.set_index('time')['Leistung kW'].rename(
        columns={'Leistung kW': 'feedin_val'}) * 1000
    bb_ts.index = pd.to_datetime(bb_ts.index, utc=True)
    bb_ts.name = 'feedin_val'
    if start:
        bb_ts = bb_ts[(bb_ts.index >= start)]
    if stop:
        bb_ts = bb_ts[(bb_ts.index <= stop)]
    return bb_ts


def get_weather(start=None, stop=None, weather_data_name='open_FRED'):
    r"""
    Get open_FRED or ERA5 weather data for Uckermark region in specific period.

    """
    if weather_data_name == 'open_FRED':
        pass # todo use feedinlib db.py mit region file
    elif weather_data_name == 'ERA5':
        weather_df = pd.DataFrame()
        for year in np.arange(start.year, stop.year + 1):
            filename = os.path.join(settings.weather_data_path,
                                    'era5_wind_um_{}.csv'.format(year))
            df = tools.example_weather_wind(filename).rename(
                columns={'wind speed': 'wind_speed'})
            weather_df = pd.concat([weather_df, df], axis=0)
        if start:
            weather_df = weather_df[
                weather_df.index.get_level_values(0).tz_localize('UTC') >=
                start]
        if stop:
            weather_df = weather_df[
                weather_df.index.get_level_values(0).tz_localize('UTC') <=
                    stop]
    return weather_df


def fill_missing_dates(register, com_date=None,
                       decom_date='2050-01-01 00:00:00'):
    r"""
    Fills missing commission and decommssion dates.

    If value None is given, no filling takes place.

 todo if used for other registers: If nan values exist in the
    columns a warning is given.

    Parameters:
    -----------
    register : pd.DataFrame
        Contains commissioning dates in column 'com_col' and decommissioning
        dates in 'decom_col'.
    """
    if com_date:
        indices = register.loc[
            register['commissioning_date'].isna() == True].index
        register.loc[indices]['commissioning_date'] = com_date
    if decom_date:
        indices = register.loc[
            register['decommissioning_date'].isna() == True].index
        register['decommissioning_date'].loc[indices] = decom_date
    return register


def calculate_feedin(register, weather_df, **kwargs):
    register = tools.add_weather_locations_to_register(
        register=register, weather_coordinates=weather_df)
    weather_locations = register[['weather_lat', 'weather_lon']].groupby(
        ['weather_lat', 'weather_lon']).size().reset_index().drop([0], axis=1)
    # get turbine types (and data) from register
    turbine_data = register.groupby(
        ['turbine_type', 'hub_height',
         'rotor_diameter']).size().reset_index().drop(0, axis=1)
    # initialize wind turbine objects for each turbine type in register
    turbine_data['turbine'] = turbine_data.apply(
        lambda x: wt.WindTurbine(**x), axis=1)
    turbine_data.index = turbine_data['turbine_type']
    turbines_region = dict(turbine_data['turbine'])

    region_feedin_df = pd.DataFrame()
    for weather_location, weather_index in zip(
            [list(weather_locations.iloc[index])
             for index in weather_locations.index],
            weather_locations.index):
        # select power plants belonging to weather location
        power_plants = register.loc[
            (register['weather_lat'] == weather_location[0]) & (
                    register['weather_lon'] == weather_location[
                1])]
        # prepare power plants for windpowerlib TurbineClusterModelChain
        turbine_types_location = power_plants.groupby(
            'turbine_type').size().reset_index().drop(0, axis=1)
        wind_farm_data = {'name': 'todo', 'wind_turbine_fleet': []}
        for turbine_type in turbine_types_location['turbine_type']:
            capacity = power_plants.loc[
                power_plants['turbine_type'] == turbine_type]['capacity'].sum()
            wind_farm_data['wind_turbine_fleet'].append(
                {'wind_turbine': turbines_region[turbine_type],
                 'number_of_turbines': capacity *1000 / turbines_region[
                     turbine_type].nominal_power})

        # initialize wind farm and run TurbineClusterModelChain
        wind_farm = wf.WindFarm(**wind_farm_data)
        # select weather of weather location and drop location index
        weather = weather_df.loc[
            (weather_df.index.get_level_values('lat') ==
             weather_location[0]) & (
                    weather_df.index.get_level_values('lon') ==
                    weather_location[1])].droplevel(level=[1, 2])
        feedin_ts = tc_mc.TurbineClusterModelChain(wind_farm,
                                             **kwargs).run_model(
            weather).power_output
        feedin_df = pd.DataFrame(data=feedin_ts).rename(
            columns={feedin_ts.name: 'feedin_{}'.format(weather_index)})
        region_feedin_df = pd.concat([region_feedin_df, feedin_df], axis=1)
    feedin = region_feedin_df.sum(axis=1).rename('feedin')
    return feedin


if __name__ == "__main__":
    settings.init()

    # set parameters
    weather_data_names = [
        # 'open_FRED',  # todo check resolution
        'ERA5'
    ]

    cases = ['aggregation', 'smoothing', 'wake_losses']

    windpowerlib_parameters = {
        'aggregation': {'smoothing': False,
                        'wake_losses_model': None},
        'smoothing': {'smoothing': True,
                      'wake_losses_model': None},
        'wake_losses': {'smoothing': False,
                        'wake_losses_model': 'dena_mean'}
    }  # note: default values for remaining parameters

    time_series_filename = settings.path_time_series_bb

    validation_path = settings.path_validation_metrics_bb

    # get register
    register = get_turbine_register()
    register = fill_missing_dates(register, com_date=None,
                                  decom_date='2050-01-01 00:00:00')
    # get periods with no change in installed capacity
    periods = feedinlib_tools.get_time_periods_with_equal_capacity(
        register, start=2013, stop=2017)
    # calculate feed-in for each period and save in data frame
    for weather_data_name in weather_data_names:
        validation_df = pd.DataFrame()
        for case in cases:
            feedin = pd.Series()
            for start, stop in zip(periods['start'], periods['stop']):
                # get weather and register for period and calculated feedin
                weather_df = get_weather(start=start, stop=stop,
                                         weather_data_name=weather_data_name)
                filtered_register = feedinlib_tools.filter_register_by_period(
                    register=register, start=start, stop=stop)
                feedin_period = calculate_feedin(
                    weather_df=weather_df, register=register,
                    **windpowerlib_parameters[case])
                feedin = feedin.append(feedin_period)
            feedin.name, feedin.index.name = 'feedin', 'time'
            feedin.index = feedin.index.tz_localize('UTC')

            # get validation data
            feedin_val = get_measured_time_series()

            # resample time series (returns dataframe)
            feedin_val = tools.resample_with_nan_theshold(
                pd.DataFrame(feedin_val), frequency='H', threshold=2)
            if weather_data_name == 'open_FRED':
                feedin = tools.resample_with_nan_theshold(  # todo check functionality
                    feedin, frequency='H', threshold=1)

            # join data frame in the form needed by calculate_validation_metrics()
            validation_df_case = pd.merge(left=feedin, right=feedin_val,
                                          how='left', on=['time'])
            validation_df_case['case'] = case
            validation_df = pd.concat([validation_df, validation_df_case])

        # save time series data frame (`validation_df`) to csv
        validation_df.to_csv(os.path.join(
            time_series_filename, 'time_series_df_brandenburg_{}.csv'.format(
                weather_data_name)))

        # calculate metrics and save to file
        filename = os.path.join(validation_path,
            'validation_brandenburg_{}.csv'.format(weather_data_name))
        val_tools.calculate_validation_metrics(
            df=validation_df, val_cols=['feedin', 'feedin_val'],
            filter_cols=['case'],
            metrics='standard', filename=filename)