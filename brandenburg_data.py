"""
The ``brandenburg_data`` module contains functions for validating ...
The following data is available:
- ...

DateTimeIndex in 'UTC' time zone.

"""

import pandas as pd
import os
import pickle

from feedin_germany import power_plant_register_tools as ppr_tools

# internal imports
import settings

settings.init()


def get_turbine_register(year):
    """
    Load turbine register from file.

    Returns
    -------
    df : pd.DataFrame
        - capacity in W (as in windpowerlib)

    """
    filename = os.path.join(
        settings.path_brandenburg, 'bb_turbines.csv')
    if os.path.exists('turbines_bb_dump.p'):
        df = pickle.load(open('turbines_bb_dump.p', 'rb'))
    else:
        df = pd.read_csv(filename, sep=',', decimal='.', index_col=0,
                         parse_dates=True)
        pickle.dump(df, open('turbines_bb_dump.p', 'wb'))

    # capacity in W
    df['capacity'] *= 1000

    # prepare dates
    date_cols = ('commissioning_date', 'decommissioning_date')
    prepared_df = ppr_tools.prepare_dates(df=df, date_cols=date_cols)
    prepared_df['commissioning_date'] = pd.to_datetime(
        prepared_df['commissioning_date'], utc=True)
    prepared_df['decommissioning_date'] = pd.to_datetime(
        prepared_df['decommissioning_date'], utc=True)

    # filter by year
    filtered_df = ppr_tools.get_pp_by_year(
        year=year, register=prepared_df,
        month_wise_capacities=False)
    return filtered_df


def get_measured_time_series(start=None, stop=None, year=None,
                             completeness_limit=95.0):
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
    if year:
        bb_df = bb_ts.reset_index('time')
        bb_df = bb_df[bb_df['time'].dt.year == year]
        bb_df.set_index('time', inplace=True)
        bb_ts = bb_df['feedin_val']
    return bb_ts
