# Imports from lib_validation
from wind_farm_specifications import initialize_turbines

# Other imports
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import os

turbines = initialize_turbines([
    'enerconE70', 'vestasV90', 'vestasV80', 'ge_1500',
    # 'enerconE66_1800_65', # Note: war nur für wf_3
    'enerconE82_2000'])
    # These implies also most often installe turbines from dena study

for turbine in turbines:
    # Load power and power coefficient curve
    power_curve = pd.DataFrame(turbine.power_curve)
    power_curve.set_index('wind_speed', inplace=True)
    power_curve.columns = ['original power curve']
    power_coefficient_curve = pd.DataFrame(turbine.power_coefficient_curve)
    # Convert power coefficient curve to power curve with standard air density
    power_coefficient_curve['calculated power curve'] = (
        power_coefficient_curve['power coefficient'] * (1 / 8) * 1.225 *
        turbine.rotor_diameter ** 2 * np.pi *
        power_coefficient_curve['wind_speed'] ** 3)
    power_coefficient_curve.drop('power coefficient', axis=1, inplace=True)
    power_coefficient_curve.set_index('wind_speed', inplace=True)
    # Plot
    fig, ax = plt.subplots()
    power_curve.plot(ax=ax, legend=True)
    power_coefficient_curve.plot(ax=ax, legend=True)
    plt.title(turbine.object_name)
    fig.savefig(
        os.path.join(
        os.path.dirname(__file__),
        '../../../User-Shares/Masterarbeit/Latex/inc/images/cp_to_p_curves',
        'cp_to_p_{0}'.format(turbine.object_name).replace(' ', '_')))
    plt.close()