# Imports from Windpowerlib
from windpowerlib.modelchain import ModelChain
from windpowerlib.turbine_cluster_modelchain import TurbineClusterModelChain
from windpowerlib.wind_speed import logarithmic_profile, hellman
from windpowerlib import tools as wpl_tools

# Other imports
import logging
import pandas as pd
import numpy as np


def power_output_simple(wind_turbine_fleet, weather_df, wind_speed=None,
                        wind_speed_model='logarithmic',
                        density_model='barometric',
                        temperature_model='linear_gradient',
                        power_output_model='power_curve',
                        density_correction=False,
                        obstacle_height=0, hellman_exp=None):
    r"""
    Calculate power output of several wind turbines by a simple method.

    Simplest way to calculate the power output of a wind farm or other
    gathering of wind turbines. For the power_output of the single turbines
    a power_curve without density correction is used. The wind speed at hub
    height is calculated by the logarithmic wind profile. The power output of
    the wind farm is calculated by aggregation of the power output of the
    single turbines.

    Parameters
    ----------
    wind_turbine_fleet : List of Dictionaries
        Wind turbines of wind farm. Dictionaries must have 'wind_turbine'
        (contains wind turbine object) and 'number_of_turbines' (number of
        turbine type in wind farm) as keys.
    weather_df : pandas.DataFrame
        DataFrame with time series for wind speed `wind_speed` in m/s and
        roughness length `roughness_length` in m.
    wind_speed : pd.Series or np.array
        If this parameter is given, this wind_speed instead of the one in
        `weather_df` is used for calculations. Default: None.

    Returns
    -------
    pd.Series
        Simulated power output of wind farm.

    """
    modelchain_data = {
        'wind_speed_model': wind_speed_model,
        'density_model': density_model,
        'temperature_model': temperature_model,
        'power_output_model': power_output_model,
        'density_correction': density_correction,
        'obstacle_height': obstacle_height,
        'hellman_exp': hellman_exp}
    # Get power output of each turbine
    for turbine_type in wind_turbine_fleet:
        if wind_speed is not None:
            df = pd.DataFrame(
                data=wind_speed.values,
                index=wind_speed.index,
                columns=[np.array(['wind_speed']),
                         np.array([turbine_type['wind_turbine'].hub_height])])
            # resample weather_df to resolution of wind_speed
            if not weather_df.index.freq == wind_speed.index.freq:
                weather_df = weather_df.resample(wind_speed.index.freq).mean()
            weather_df = pd.concat([weather_df, df], axis=1)
        # Initialise ModelChain and run model
        mc = ModelChain(turbine_type['wind_turbine'],
                        **modelchain_data).run_model(weather_df)
        # Write power output timeseries to WindTurbine object
        turbine_type['wind_turbine'].power_output = mc.power_output
    # Sum up the power output
    farm_power_output = 0
    for turbine_type in wind_turbine_fleet:
        farm_power_output += (turbine_type['wind_turbine'].power_output *
                              turbine_type['number_of_turbines'])
    return farm_power_output


def power_output_cluster(wind_object, weather_df, wake_losses_model=None,
                         smoothing=True, block_width=0.5,
                         standard_deviation_method='turbulence_intensity',
                         smoothing_order='wind_farm_power_curves',
                         wind_speed=None, **kwargs):
    r"""
    Calculate power output of a wind farm or cluster.

    Parameters
    ----------
    wind_object : WindFarm or WindTurbineCluster
        A :class:`~.wind_farm.WindFarm` object representing the wind farm or
        a :class:`~.wind_turbine_cluster.WindTurbineCluster` object
        representing the wind turbine cluster.
    weather_df : pandas.DataFrame
        DataFrame with time series for wind speed `wind_speed` in m/s, and
        roughness length `roughness_length` in m, as well as optionally
        temperature `temperature` in K, pressure `pressure` in Pa and
        density `density` in kg/m³ depending on `power_output_model` and
        `density_model chosen`.
        The columns of the DataFrame are a MultiIndex where the first level
        contains the variable name (e.g. wind_speed) and the second level
        contains the height at which it applies (e.g. 10, if it was
        measured at a height of 10 m). See documentation of
        :func:`modelchain.ModelChain.run_model` for an example on how to
        create the weather_df DataFrame.
    wake_losses_model : String
        Defines the method for talking wake losses within the farm into
        consideration. Default: 'constant_efficiency'.
    smoothing : Boolean
        If True the power curves will be smoothed before the summation.
        Default: True.
    block_width : float, optional
        Width of the moving block.
        Default in :py:func:`~.power_output.smooth_power_curve`: 0.5.
    standard_deviation_method : String, optional
        Method for calculating the standard deviation for the gaussian
        distribution. Options: 'turbulence_intensity', 'Norgaard', 'Staffell'.
        Default in :py:func:`~.power_output.smooth_power_curve`:
        'turbulence_intensity'.
    smoothing_order : String
        Defines when the smoothing takes place if `smoothing` is True. Options:
        'turbine_power_curves' (to the single turbine power curves),
        'wind_farm_power_curves' or 'cluster_power_curve'.
        Default: 'wind_farm_power_curves'.

    Other Parameters
    ----------------
    wind_speed_model : string, optional.
        Parameter to define which model to use to calculate the wind speed at
        hub height. Valid options are 'logarithmic', 'hellman' and
        'interpolation_extrapolation'.
    temperature_model : string, optional.
        Parameter to define which model to use to calculate the temperature of
        air at hub height. Valid options are 'linear_gradient' and
        'interpolation_extrapolation'.
    density_model : string, optional.
        Parameter to define which model to use to calculate the density of air
        at hub height. Valid options are 'barometric', 'ideal_gas' and
        'interpolation_extrapolation'.
    power_output_model : string, optional.
        Parameter to define which model to use to calculate the turbine power
        output. Valid options are 'power_curve' and 'power_coefficient_curve'.
    density_correction : boolean, optional.
        If the parameter is True the density corrected power curve is used for
        the calculation of the turbine power output.
    obstacle_height : float, optional.
        Height of obstacles in the surrounding area of the wind turbine in m.
        Set `obstacle_height` to zero for wide spread obstacles.
    hellman_exp : float, optional.
        The Hellman exponent, which combines the increase in wind speed due to
        stability of atmospheric conditions and surface roughness into one
        constant.
    turbulence_intensity : float, optional.
        Turbulence intensity.

    Returns
    -------
    pd.Series
        Simulated power output of wind farm.
    """
    wf_modelchain_data = {
        'wake_losses_model': wake_losses_model,
        'smoothing': smoothing,
        'block_width': block_width,
        'standard_deviation_method': standard_deviation_method,
        'smoothing_order': smoothing_order}
    if 'density_correction' in kwargs:
        wf_modelchain_data['density_correction'] = kwargs['density_correction']
    if wind_speed is not None:
        # Attention: in this thesis used for a validation data set, where hub
        # height of turbines within one wind farm is the same!
        wind_object.mean_hub_height()
        df = pd.DataFrame(
            data=wind_speed.values,
            index=wind_speed.index,
            columns=[np.array(['wind_speed']),
                     np.array([wind_object.hub_height])])
        weather_df = pd.concat([weather_df, df], axis=1)
    wf_mc = TurbineClusterModelChain(
        wind_object, **wf_modelchain_data).run_model(weather_df)
    return wf_mc.power_output


def wind_speed_to_hub_height(wind_turbine_fleet, weather_df,
                             wind_speed_model='logarithmic',
                             obstacle_height=0, hellman_exp=None):
    r"""
    Calculates the wind speed at hub height. (function from modelchain)

    The method specified by the parameter `wind_speed_model` is used.

    Parameters
    ----------
    wind_turbine_fleet : List of Dictionaries
        Wind turbines of wind farm. Dictionaries must have 'wind_turbine'
        (contains wind turbine object) and 'number_of_turbines' (number of
        turbine type in wind farm) as keys.
    weather_df : pandas.DataFrame
        DataFrame with time series for wind speed `wind_speed` in m/s and
        roughness length `roughness_length` in m.

    Returns
    -------
        wind_speed_hub : pd.Series
            Simulated wind speed at hub height.
    """
    hub_height = wind_turbine_fleet[0]['wind_turbine'].hub_height
    if hub_height in weather_df['wind_speed']:
        wind_speed_hub = weather_df['wind_speed'][hub_height]
    elif wind_speed_model == 'logarithmic':
        logging.debug('Calculating wind speed using logarithmic wind '
                      'profile.')
        closest_height = weather_df['wind_speed'].columns[
            min(range(len(weather_df['wind_speed'].columns)),
                key=lambda i: abs(weather_df['wind_speed'].columns[i] -
                                  hub_height))]
        wind_speed_hub = logarithmic_profile(
            weather_df['wind_speed'][closest_height], closest_height,
            hub_height, weather_df['roughness_length'].ix[:, 0],
            obstacle_height)
    elif wind_speed_model == 'hellman':
        logging.debug('Calculating wind speed using hellman equation.')
        closest_height = weather_df['wind_speed'].columns[
            min(range(len(weather_df['wind_speed'].columns)),
                key=lambda i: abs(weather_df['wind_speed'].columns[i] -
                                  hub_height))]
        wind_speed_hub = hellman(
            weather_df['wind_speed'][closest_height], closest_height,
            hub_height, weather_df['roughness_length'].ix[:, 0], hellman_exp)
    elif wind_speed_model == 'interpolation_extrapolation':
        logging.debug('Calculating wind speed using linear inter- or '
                      'extrapolation.')
        wind_speed_hub = wpl_tools.linear_interpolation_extrapolation(
            weather_df['wind_speed'], hub_height)
    elif wind_speed_model == 'log_interpolation_extrapolation':
        logging.debug('Calculating wind speed using logarithmic inter- or '
                      'extrapolation.')
        wind_speed_hub = wpl_tools.logarithmic_interpolation_extrapolation(
            weather_df['wind_speed'], hub_height)
    else:
        raise ValueError("'{0}' is an invalid value. ".format(
            wind_speed_model) + "`wind_speed_model` must be "
            "'logarithmic', 'hellman', 'interpolation_extrapolation' " +
            "or 'log_interpolation_extrapolation'.")
    return wind_speed_hub
