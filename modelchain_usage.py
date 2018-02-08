# Imports from Windpowerlib
from windpowerlib import (power_output, wind_speed, density, temperature)
from windpowerlib.modelchain import ModelChain

# Imports from lib_validation
import tools

# Other imports


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
        # Initialise ModelChain
        mc = ModelChain(turbine_type['wind_turbine'],
                        **modelchain_data).run_model(weather_df)
        # Write power output timeseries to WindTurbine object
        turbine_type['wind_turbine'].power_output = mc.power_output
    return tools.power_output_simple_aggregation(wind_turbine_fleet)
