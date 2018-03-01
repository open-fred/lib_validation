# Imports from Windpowerlib
from windpowerlib.modelchain import ModelChain
from windpowerlib.wind_farm_modelchain import WindFarmModelChain

# Imports from lib_validation
import tools


def power_output_simple(wind_turbine_fleet, weather_df,
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
        roughness length `roughness_length` in m. TODO: add from wpl

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
    for turbine_type in wind_turbine_fleet:
        # Initialise ModelChain and run model
        mc = ModelChain(turbine_type['wind_turbine'],
                        **modelchain_data).run_model(weather_df)
        # Write power output timeseries to WindTurbine object
        turbine_type['wind_turbine'].power_output = mc.power_output
    return tools.power_output_simple_aggregation(wind_turbine_fleet)


def power_output_wind_farm(wind_farm, weather_df, cluster=False,
                           density_correction=False,
                           wake_losses_method=None,
                           smoothing=True, block_width=0.5,
                           standard_deviation_method='turbulence_intensity',
                           wind_farm_efficiency=None, **kwargs):
    r"""
    Calculate power output of... TODO: add to docstring

    Parameters
    ----------
    wind_farm : object
        A :class:`~.wind_farm.WindFarm` object representing the wind farm.
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
    cluster : Boolean
        TODO: add
    density_correction : Boolean
        If True a density correction will be applied to the power curves
        before the summation. Default: False.
    wake_losses_method : String
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
    wind_farm_efficiency : float or pd.DataFrame or Dictionary
        Efficiency of the wind farm. Either constant (float) or wind efficiency
        curve (pd.DataFrame or Dictionary) contianing 'wind_speed' and
        'efficiency' columns/keys with wind speeds in m/s and the
        corresponding dimensionless wind farm efficiency. Default: None.

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
    roughness_length : float, optional.
        Roughness length.
    turbulence_intensity : float, optional.
        Turbulence intensity.

    Returns
    -------
    pd.Series
        Simulated power output of wind farm.
    """
    wf_modelchain_data = {
        'cluster': cluster,
        'density_correction': density_correction,
        'wake_losses_method': wake_losses_method,
        'smoothing': smoothing,
        'block_width': block_width,
        'standard_deviation_method': standard_deviation_method,
        'wind_farm_efficiency': wind_farm_efficiency}
    # Add to modelchain data
    if 'wind_speed_model' in kwargs:
        wf_modelchain_data['wind_speed_model'] = kwargs['wind_speed_model']
    if 'temperature_model' in kwargs:
        wf_modelchain_data['temperature_model'] = kwargs['temperature_model']
    if 'density_model' in kwargs:
        wf_modelchain_data['density_model'] = kwargs['density_model']
    if 'power_output_model' in kwargs:
        wf_modelchain_data['power_output_model'] = kwargs['power_output_model']
    if 'density_correction' in kwargs:
        wf_modelchain_data['density_correction'] = kwargs['density_correction']
    if 'obstacle_height' in kwargs:
        wf_modelchain_data['obstacle_height'] = kwargs['obstacle_height']
    if 'hellman_exp' in kwargs:
        wf_modelchain_data['hellman_exp'] = kwargs['hellman_exp']
    wf_mc = WindFarmModelChain(wind_farm,
                               **wf_modelchain_data).run_model(weather_df,
                                                               **kwargs)
    return wf_mc.power_output
