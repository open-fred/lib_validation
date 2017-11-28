import pandas as pd
import os
import pickle
from windpowerlib import (power_output, wind_speed)
import tools


def get_weather_data(pickle_load=None, filename='pickle_dump.p',
                     weather_data=None, year=None, coordinates=None,
                     data_frame=None):
    r"""
    Helper function to load pickled weather data or retrieve data and dump it.

    Parameters
    ----------
    pickle_load : Boolean
        True if data has already been dumped before.
    filename : String
        Name (including path) of file to load data from or if MERRA data is
        retrieved function 'create_merra_df' is used. Default: 'pickle_dump.p'.
    weather_data : String
        String specifying if open_FRED or MERRA data is retrieved in case
        `pickle_load` is False. Default: None.
    year : int
        Specifies which year the weather data is retrieved for. Default: None.
    coordinates : List
        List of coordinates [lat, lon] of location for loading data.
        Default: None
    data_frame : pandas.DataFrame
        Contains MERRA or open_FRED data. Makes function faster if it is used
        in a loop. Default: None.

    Returns
    -------
    data : pandas.DataFrame
        Weather data with time series as index and data like temperature and
        wind speed as columns.

    """
    if pickle_load:
        weather_df = pickle.load(open(filename, 'rb'))
    else:
        if weather_data == 'open_FRED':
            # TODO: add open_FRED weather data
            filename = 'weather_df_open_FRED_{0}.p'.format(year)
        elif weather_data == 'MERRA':
            if data_frame is None:
                # Load data from csv
                data_frame = pd.read_csv(os.path.join(
                    os.path.dirname(__file__), 'data/Merra', # TODO: make folder individua
                    'weather_data_GER_{0}.csv'.format(year)),
                    sep=',', decimal='.', index_col=0)
            weather_df = create_merra_df(data_frame, coordinates)
            # Set indices to standardized form
            weather_df.index = tools.get_indices_for_series(60, year=year)
#            visualization_tools.print_whole_dataframe(weather_df.lat)
            filename = 'weather_df_merra_{0}.p'.format(year)
        pickle.dump(weather_df, open(os.path.join(os.path.dirname(__file__),
                                     'dumps/weather', filename), 'wb'))
    return weather_df


def create_merra_df(dataframe, coordinates):
    r"""
    Parameters
    ----------
    filename : String
        Name (including path) of file to load data from or if MERRA data is
        retrieved function 'create_merra_df' is used. Default: 'pickle_dump.p'.
    coordinates : List
        List of coordinates [lat, lon] of location. For loading data.
        Default: None

    Returns
    -------
    merra_df : pandas.DataFrame
        Weather data with time series as index and data like temperature and
        wind speed as columns.

    """
    merra_df = dataframe.loc[(dataframe['lat'] == coordinates[0]) &
                             (dataframe['lon'] == coordinates[1])]
    merra_df = merra_df.drop(['v1', 'v2', 'h2', 'cumulated hours',
                              'SWTDN', 'SWGDN'], axis=1)
    merra_df = merra_df.rename(
        columns={'v_50m': 'wind_speed', 'h1': 'temperature_height',
                 'z0': 'roughness_length', 'T': 'temperature',
                 'rho': 'density', 'p': 'pressure'}) # TODO: check units of Merra data
    return merra_df


def power_output_sum(wind_turbine_fleet, weather_df, data_height):
    r"""
    Calculate power output of several wind turbines by summation.

    Simplest way to calculate the power output of a wind farm or other
    gathering of wind turbines. For the power_output of the single turbines
    a power_curve without density correction is used. The wind speed at hub
    height is calculated by the logarithmic wind profile.

    Parameters
    ----------
    wind_turbine_fleet : List of Dictionaries
        Wind turbines of wind farm. Dictionaries must have 'wind_turbine'
        (contains wind turbine object) and 'number_of_turbines' (number of
        turbine type in wind farm) as keys.
    weather_df : pandas.DataFrame
        DataFrame with time series for wind speed `wind_speed` in m/s and
        roughness length `roughness_length` in m.
    data_height : Dictionary
        Contains the heights of the weather measurements or weather
        model in meters with the keys of the data parameter.

    """
    farm_power_output = 0
    for turbine_type in wind_turbine_fleet:
        wind_speed_hub = wind_speed.logarithmic_profile(
            weather_df.wind_speed, data_height['wind_speed'],
            turbine_type['wind_turbine'].hub_height,
            weather_df.roughness_length, obstacle_height=0.0)
        farm_power_output += (power_output.power_curve(
            wind_speed_hub,
            turbine_type['wind_turbine'].power_curve['wind_speed'],
            turbine_type['wind_turbine'].power_curve['values']) *
            turbine_type['number_of_turbines'])
    return farm_power_output


def annual_energy_output(power_output, temporal_resolution):
    r"""
    Calculate annual energy output from power output time series.

    Parameters
    ----------
    power_output : pd.Series
        Power output time series of wind turbine or wind farm.
    temporal_resolution : Integer
        Temporal resolution of power output time series in minutes.

    Return
    ------
    Float
        Annual energy output in Wh, kWh or MWh depending on the
        unit of `power_output`.

    """
    energy = power_output * temporal_resolution / 60
    return energy.sum()


def energy_output_series(power_output, temporal_resolution, output_resolution):
    r"""
    Converts power output time series to hourly energy output time series.

    Power output time series of different temporal resolutions are converted to
    energy output time series with a temporal resolution of one hour.

    Parameters
    ----------
    power_output : pd.Series
        Power output of wind turbine or wind farm.
    temporal_resolution : Integer
        Temporal resolution of power output time series in minutes.
    output_resolution : String
        Intended resolution of output series: 'H' for hourly, 'M' for monthly,
        etc. see http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

    Returns
    -------
    energy_output : pd.Series
        Energy output time series with a temporal resolution of one hour.

    """
    energy_output_series = power_output * temporal_resolution / 60
    energy_output = energy_output_series.resample(output_resolution).sum()
    energy_output = energy_output.dropna()
    return energy_output


def power_output_fill(power_output, output_resolution, year):
    r"""
    Change temporal resolution of power output by filling with pad().

    Parameters
    ----------
    power_output : pd.Series
        Power output of wind turbine or wind farm.
    output_resolution : Integer
        Temporal resolution of output time series in minutes.
    year : Integer
        Year of the power output series.

    Returns
    -------
    output_series : pd.Series
        Power output of wind turbine or wind farm in the temporal resolution of
        `output_resolution`.

    """
    index = pd.to_datetime(pd.datetime(
            year + 1, 1, 1, 0)).tz_localize('Europe/Berlin').tz_convert('UTC')
    output_series = pd.concat([power_output, pd.Series(10, index=[index])])
    output_series = output_series.resample(
        '{0}min'.format(output_resolution)).pad()
    output_series = output_series.drop(output_series.index[-1])
    return output_series


def get_indices_for_series(temporal_resolution, year=None,
                           start=None, end=None):
    r"""
    Create indices for annual time series in a certain frequency and form.

    Parameters
    ----------
    temporal_resolution : integer
        Intended temporal resolution of time series index in min.
    year : integer
        Year of the time series. Either `year` or `start` and `end` have to be
        defined. If all three are given, `start` and `end` will be used.
        Default: None.
    start : String
        Start date of index time series. Either `year` or `start` and `end`
        have to be defined. Format: 'd/m/yyyy'. Default: None.
    end : String
        Defines end date - set `end` to one day after the end date.
        Example: '1/1/2017' for ending in 2016.
        Either `year` or `start` and `end` have to be defined. Default: None.

    Returns
    -------
        Date range index in intended temporal resolution.

    """
    frequency = '{0}min'.format(temporal_resolution)
    if (start is not None and end is not None):
        pass
    else:
        try:
            start = '1/1/{0}'.format(year)
            end = '1/1/{0}'.format(year + 1)
        except TypeError:
            raise TypeError("Either `year` or `start` and `end`" +
                            "have to be defined.")
    return (pd.date_range(start, end, freq=frequency,
                          tz='Europe/Berlin', closed='left'))

#dev = standard_deviation([6,7,7.5,6.5,7.5,8,6.5])  # Test
#dev = standard_deviation(pd.Series(data=[6,7,7.5,6.5,7.5,8,6.5]))  # Test
# TODO: possible: split tools module to power_output, weather, comparison...


def select_certain_time_steps(series, time_period):
    r"""
    Selects certain time steps from series by a specified time period.

    Parameters
    ----------
    series : pd.Series
        Time series of which will be selected certain time steps.
    time_period : Tuple (Int, Int)
        Indicates time period for selection. Format (h, h) example (9, 12) will
        select all time steps whose time lies between 9 and 12 o'clock.

    """
    return series[(time_period[0] <= series.index.hour) &
                  (series.index.hour <= time_period[1])]
