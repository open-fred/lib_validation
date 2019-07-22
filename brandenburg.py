
# internal imports
import tools

from feedin_germany import geometries

from windpowerlib import wind_turbine as wt
from windpowerlib import wind_farm as wf
from windpowerlib import turbine_cluster_modelchain as tc_mc

import pandas as pd
import numpy as np
import os

def get_turbine_register(year, **kwargs):
    """

    Other parameters
    ----------------
    datapath : string
        Path to open_fred folder. For example '~/rl-institut/04_Projekte/163_Open_FRED/'.

    Returns
    -------
    df : pd.DataFrame
        - capacity in kw (as in windpowerlib)

    """
    if 'datapath' not in kwargs:
        kwargs['datapath'] = '~/rl-institut/04_Projekte/163_Open_FRED/'
    filename = os.path.join(
        kwargs['datapath'],
        '03-Projektinhalte/AP5 Einspeisezeitreihen/5.2 Wind/Brandenburg/bb_turbines.csv')
    df = pd.read_csv(filename, sep=',', decimal='.', index_col=0,
                     parse_dates=True).rename(columns={'turbine_type': 'name'})
    # get power plants installed before `year`
    # todo
    return df


def get_measured_time_series(year, **kwargs):
    """

    Other parameters
    ----------------
    datapath : string
        Path to open_fred folder. For example '~/rl-institut/04_Projekte/163_Open_FRED/'

    """
    if 'datapath' not in kwargs:
        kwargs['datapath'] = '~/rl-institut/04_Projekte/163_Open_FRED/'
    filename = os.path.join(
        kwargs['datapath'],
        '03-Projektinhalte/AP5 Einspeisezeitreihen/5.2 Wind/Brandenburg/bb_power_timeseries.csv')
    df = pd.read_csv(filename, sep=',', decimal='.',
                     parse_dates=True).rename(columns={'Von': 'time'})
    bb_df = pd.DataFrame(df.set_index('time')['Leistung kW'])
    # filter year # todo

    return bb_df


def load_uckermark_polygon():
    path = os.path.abspath(
        '/home/sabine/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP5 Einspeisezeitreihen/5.2 Wind/Brandenburg/regions_polygon/')
    filename = 'uckermark.geojson'
    regions = geometries.load(path=path, filename=filename)
    return regions[['geometry', 'NUTS']]


def get_weather(year, weather_data_name='open_FRED'):
    if weather_data_name == 'open_FRED':
        filename = os.path.join(
            '~/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/',
            'fred_data_{}_sh.csv'.format(year))
        weather_df = tools.example_weather_wind(filename)  # todo exchange with data loaded by Pierre
    else:
        pass
    return weather_df


def calculate_feedin(year, weather_data_name, **kwargs):
    register = get_turbine_register(year)
    weather_df = get_weather(year, weather_data_name)
    # todo @Birgit: parameters in **kwargs? f.e. 'fetch_turbine'
    register = tools.add_weather_locations_to_register(
        register=register, weather_coordinates=weather_df)
    weather_locations = register[['weather_lat', 'weather_lon']].groupby(
        ['weather_lat', 'weather_lon']).size().reset_index().drop([0], axis=1)
    # get turbine types (and data) from register
    turbine_data = register.groupby(
        ['name', 'hub_height',
         'rotor_diameter']).size().reset_index().drop(0, axis=1)
    # initialize wind turbine objects for each turbine type in register
    turbine_data['turbine'] = turbine_data.apply(
        lambda x: wt.WindTurbine(fetch_curve='power_curve', **x), axis=1)
    turbine_data.index = turbine_data['name']
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
            'name').size().reset_index().drop(0, axis=1)
        wind_farm_data = {'name': 'todo', 'wind_turbine_fleet': []}
        for turbine_type in turbine_types_location['name']:
            capacity = power_plants.loc[
                power_plants['name'] == turbine_type]['capacity'].sum()
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
    # register = get_turbine_register()
    # get_measured_time_series()
    calculate_feedin(2016, weather_data_name='open_FRED')