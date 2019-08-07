"""
The ``brandenburg_data`` module contains functions for validating ...
The following data is available:
- ...

DateTimeIndex in 'UTC' time zone.

"""

# internal imports
import tools
import validation_tools as val_tools

# windpowerlib imports
from windpowerlib import wind_turbine as wt
from windpowerlib import wind_farm as wf
from windpowerlib import turbine_cluster_modelchain as tc_mc

import pandas as pd
import numpy as np
import os


def get_turbine_register(**kwargs):
    """
    Load turbine register from file.

    datapath : string (optional)
        Path to open_fred folder. For example '~/rl-institut/04_Projekte/163_Open_FRED/'.

    Returns
    -------
    df : pd.DataFrame
        - capacity in W (as in windpowerlib)

    """
    if 'datapath' not in kwargs:
        kwargs['datapath'] = '~/rl-institut/04_Projekte/163_Open_FRED/'
    filename = os.path.join(
        kwargs['datapath'],
        '03-Projektinhalte/AP5 Einspeisezeitreihen/5.2 Wind/Brandenburg/bb_turbines.csv')
    df = pd.read_csv(filename, sep=',', decimal='.', index_col=0,
                     parse_dates=True)
    # capacity in W
    df['capacity'] *= 1000
    return df


def get_measured_time_series(start=None, stop=None, **kwargs):
    """

´
    datapath : string (optional)
        Path to open_fred folder. For example '~/rl-institut/04_Projekte/163_Open_FRED/'

    """
    if 'datapath' not in kwargs:
        kwargs['datapath'] = '~/rl-institut/04_Projekte/163_Open_FRED/'
    filename = os.path.join(
        kwargs['datapath'],
        '03-Projektinhalte/AP5 Einspeisezeitreihen/5.2 Wind/Brandenburg/bb_powerseries.csv')
    df = pd.read_csv(filename, sep=',', decimal='.',
                     parse_dates=True).rename(columns={'Von': 'time'})
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
    if weather_data_name == 'open_FRED':
        pass # todo use feedinlib db.py mit region file
    elif weather_data_name == 'ERA5':
        weather_df = pd.DataFrame()
        for year in np.arange(start.year, stop.year + 1):  # todo check
            filename = '~/virtualenvs/lib_validation/lib_validation/dumps/weather/era5_wind_um_{}.csv'.format(
                year)
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


def get_time_periods_with_equal_capacity(register, start=None, stop=None,
                                         scale=None):
    r"""

    Parameters:
    -----------
    register : pd.DataFrame
        Contains commissioning dates in column 'com_col' and decommissioning
        dates in 'decom_col'.
    start : int or str (or pd.DatetimeIndex?)
        Specifies the year (int) or date (str) from which the periods of equal
        capacities are fetched.
    stop : int or str (or pd.DatetimeIndex?)
        Specifies the year (int) or date (str) up to which the periods of equal
        capacities are fetched. If stop is an integer the whole year is
        fetched.
    scale :
        Default: None.

    """
    if isinstance(start, int):
        start = '{}-01-01 00:00:00'.format(start)
    if isinstance(stop, int):
        stop = '{}-12-31 23:59:59'.format(stop)
    # find dates with capacity change within start and stop
    dates = register['com_col']
    dates = dates.append(register['decom_col']).dropna()
    dates_filtered = dates[(dates >= start) & (dates <= stop)]
    start_dates = dates_filtered.append(pd.Series(start)).sort_values()
    start_dates.index = np.arange(0,len(start_dates))
    stop_dates = dates_filtered.append(pd.Series(stop)).sort_values()
    stop_dates.index = np.arange(0, len(stop_dates))
    periods = pd.DataFrame([start_dates, stop_dates]).transpose().rename(
        columns={0: 'start', 1: 'stop'})
    periods['start'] = pd.to_datetime(periods['start'], utc=True)
    periods['stop'] = pd.to_datetime(periods['stop'], utc=True)
    return periods


def filter_register_by_period(register, start, stop):
    r"""

    Parameters:
    -----------
    register : pd.DataFrame
        Contains commissioning dates in column 'com_col' and decommissioning
        dates in 'decom_col'. Make sure there are no missing values!
    start : int or str (or pd.DatetimeIndex?)
        Start of period. Power plants decommissioned before this date are
        neglected.
    stop : int or str (or pd.DatetimeIndex?)
        End of period. Power plants installed from this date are neglected.

    """
    if not isinstance(register['com_col'][0], pd.Timestamp):
        register['com_col'] = pd.to_datetime(register['com_col'], utc=True)
    if not isinstance(register['decom_col'][0], pd.Timestamp):
        register['decom_col'] = pd.to_datetime(register['decom_col'], utc=True)
    df_1 = register[register['decom_col'] > start]
    filtered_register = df_1[df_1['com_col'] < stop]
    return filtered_register


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
        indices = register.loc[register['com_col'].isna() == True].index
        register.loc[indices]['com_col'] = com_date
    if decom_date:
        indices = register.loc[register['decom_col'].isna() == True].index
        register['decom_col'].loc[indices] = decom_date
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
    # set parameters
    weather_data_names = [
        # 'open_FRED',
        'ERA5'
    ]

    time_series_filename = os.path.join(os.path.dirname(__file__),
                                        'dumps/time_series_dfs/brandenburg')

    # get register
    register = get_turbine_register().rename(columns={
        'commissioning_date': 'com_col', 'decommissioning_date': 'decom_col'})
    register = fill_missing_dates(register, com_date=None,
                                  decom_date='2050-01-01 00:00:00')
    # get periods with no change in installed capacity
    periods = get_time_periods_with_equal_capacity(register, start=2013,
                                                   stop=2017, scale=None)
    # calculate feed-in for each period and save in data frame
    for weather_data_name in weather_data_names:
        feedin = pd.Series()
        for start, stop in zip(periods['start'], periods['stop']):
            # get weather and register for period and calculated feedin
            weather_df = get_weather(start=start, stop=stop,
                                     weather_data_name=weather_data_name)
            filtered_register = filter_register_by_period(
                register=register, start=start, stop=stop)
            feedin_period = calculate_feedin(weather_df=weather_df,
                                             register=register)
            feedin = feedin.append(feedin_period)
        feedin.name, feedin.index.name = 'feedin', 'time'
        feedin.index = feedin.index.tz_localize('UTC')

        # get validation data
        feedin_val = get_measured_time_series()

        # join data frame in the form needed by calculate_validation_metrics()
        validation_df = pd.merge(left=feedin, right=feedin_val, how='left',
                                     on=['time'])

        # save time series data frame (`validation_df`) to csv
        validation_df.to_csv(os.path.join(
            time_series_filename, 'time_series_df_brandenburg_{}.csv'.format(
                weather_data_name)))

        # calculate metrics and save to file
        validation_path = os.path.join(os.path.dirname(__file__),
                                       'validation/brandenburg')
        if not os.path.exists(validation_path):
            os.makedirs(validation_path, exist_ok=True)
        filename = os.path.join(validation_path,
            'validation_brandenburg_{}'.format(weather_data_name))
        val_tools.calculate_validation_metrics(
            df=validation_df, val_cols=['feedin', 'feedin_val'],
            metrics='standard', filename=filename)