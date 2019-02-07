from windpowerlib.wind_turbine import WindTurbine
# Other imports
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import os


def get_curves_for_plot(turbine):
    # Load power and power coefficient curve
    power_curve = pd.DataFrame(turbine.power_curve)
    power_curve.rename(columns={col: col.replace('wind_speed',
                                                 'wind speed [m/s]') for
                                col in list(power_curve)}, inplace=True)
    power_curve.set_index('wind speed [m/s]', inplace=True)
    power_curve.columns = ['original power curve']
    power_curve = power_curve / (1 * 10 ** 6)
    power_coefficient_curve = pd.DataFrame(turbine.power_coefficient_curve)
    # Convert power coefficient curve to power curve with standard air density
    power_coefficient_curve['calculated power curve'] = (
        power_coefficient_curve['value'] * (1 / 8) * 1.225 *
        turbine.rotor_diameter ** 2 * np.pi *
        power_coefficient_curve['wind_speed'] ** 3)
    power_coefficient_curve.drop('value', axis=1, inplace=True)
    power_coefficient_curve.rename(columns={
        col: col.replace('wind_speed', 'wind speed [m/s]') for
        col in list(power_coefficient_curve)}, inplace=True)
    power_coefficient_curve.set_index('wind speed [m/s]', inplace=True)
    power_coefficient_curve = power_coefficient_curve / (1 * 10 ** 6)
    return power_curve, power_coefficient_curve


def cp_to_p_curve_single_plots():
    turbine_params = {'hub_height': 98,
                      'nominal_power': 2300000,
                      'name': 'E-82/2300',
                      'fetch_curve': 'power_coefficient_curve',
                      'rotor_diameter': 82}
    turbine = WindTurbine(**turbine_params)
    turbine_params['fetch_curve'] = 'power_curve'
    temp_turbine =  WindTurbine(**turbine_params)
    turbine.power_curve = temp_turbine.power_curve
    # These implies also most often installe turbines from dena study
    power_curve, power_coefficient_curve = get_curves_for_plot(turbine)
    # Plot
    fig, ax = plt.subplots()
    power_curve.plot(ax=ax, legend=True)
    power_coefficient_curve.plot(ax=ax, legend=True)
    plt.title(turbine.name)
    plt.ylabel('Power in MW')
    fig.savefig(os.path.join(os.path.dirname(__file__), 'power_curve.png'))
    plt.close()


if __name__ == "__main__":
    cp_to_p_curve_single_plots()
