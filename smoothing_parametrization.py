# Imports from Windpowerlib
from windpowerlib.wind_turbine import WindTurbine
from windpowerlib.wind_farm import WindFarm
from windpowerlib import power_output, tools

# Imports from lib_validation
import wind_farm_specifications
from tools import get_weather_data

# Other imports
from matplotlib import pyplot as plt
import os
import pandas as pd
import numpy as np
import pickle


def plot_smoothed_pcs(standard_deviation_method, block_width,
                      wind_speeds_block_range, mean_roughness_length=None):
    # Initialise WindTurbine objects
    turbines = wind_farm_specifications.initialize_turbines(
        ['enerconE70', 'enerconE66']) # TODO: add turbines
    for turbine in turbines:
        if standard_deviation_method == 'turbulence_intensity':
            turbulence_intensity = tools.estimate_turbulence_intensity(
                turbine.hub_height, mean_roughness_length)
        else:
            turbulence_intensity = None
        # Get smoothed power curve
        smoothed_power_curve = power_output.smooth_power_curve(
            turbine.power_curve.wind_speed, turbine.power_curve['power'],
            block_width=block_width,
            standard_deviation_method=standard_deviation_method,
            turbulence_intensity=turbulence_intensity)
        fig = plt.figure()
        a, = plt.plot(turbine.power_curve['wind_speed'],
                     turbine.power_curve['power']/1000, label='original')
        b, = plt.plot(smoothed_power_curve['wind_speed'],
                     smoothed_power_curve['power']/1000, label='smoothed')
        plt.ylabel('Power in kW')
        plt.xlabel('Wind speed in m/s')
        plt.title(turbine.object_name)
        plt.legend(handles=[a, b])
        fig.savefig(os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../Plots/power_curves',
            '{0}_{1}_blockwidth{2}_range{3}.pdf'.format(
                turbine.object_name, standard_deviation_method,
                block_width, wind_speeds_block_range))))
        plt.close()


# variables = pd.Series(data=np.arange(-15.0, 15.0, 0.5), index=np.arange(-15.0, 15.0, 0.5))
# wind_speed = 12
# # variables = np.arange(-15.0, 15.0, 0.5)
# gauss =  tools.gaussian_distribution(variables, standard_deviation=0.15*wind_speed, mean=0)
# gauss.index = gauss.index + wind_speed
# gauss.plot()
# plt.show()
# print(gauss)




if __name__ == "__main__":
    # standard_deviaton_methods = ['turbulence_intensity', 'Staffell']
    # for std_dev_method in standard_deviaton_methods:
    #     plot_smoothed_pcs(
    #         standard_deviation_method=std_dev_method, block_width,
    #                       wind_speeds_block_range, mean_roughness_length=None)
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'helper_files',
                                  'Norgaard_standard_deviation.csv'),
                     index_col=0)
    print('l')