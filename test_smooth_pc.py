from windpowerlib.wind_turbine import WindTurbine
from windpowerlib.wind_farm import WindFarm
from windpowerlib.power_output import summarized_power_curve

from windpowerlib import power_output, tools
import pandas as pd
import numpy as np
import wind_farm_specifications
# from matplotlib import pyplot as plt
import os
import pickle


# initialise WindTurbine object
turbines = wind_farm_specifications.initialize_turbines(
    ['enerconE70', 'enerconE66'])
# Weather data for TI
# filename_weather = os.path.join(os.path.dirname(__file__), '../../MA_lib_validation/lib_validation/dumps/weather',
#                                     'weather_df_{0}_{1}.p'.format(
#                                         'open_FRED', 2015))
# of_weather = pickle.load(open(filename_weather, 'rb'))
z0 = pd.Series([0.04, 0.04, 0.04])
block_width = 0.5
standard_deviation_method = 'turbulence_intensity'
# standard_deviation_method='Staffell'
#turbulence_intensity = 1 / np.log(135/z0.mean())
turbulence_intensity = tools.estimate_turbulence_intensity(
    135, z0.mean())
# turbulence_intensity = (2.4 * 0.41) / np.log(135/z0.mean()) * np.exp(-135/500) # constant boundary layer

for turbine in turbines:
    smoothed_power_curve = power_output.smooth_power_curve(
        turbine.power_curve.wind_speed, turbine.power_curve['values'],
        block_width=block_width,
        standard_deviation_method=standard_deviation_method,
        turbulence_intensity=turbulence_intensity)

    # print(e126.power_curve)
    # print(smoothed_power_curve)
    fig = plt.figure()
    plt.plot(turbine.power_curve['wind_speed'], turbine.power_curve['values'])
    plt.plot(smoothed_power_curve['wind_speed'],
             smoothed_power_curve['values'])
    fig.savefig(os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../Plots/power_curves',
        '{0}_{1}_{2}.png'.format(turbine.turbine_name,
                                 standard_deviation_method, block_width))))
    plt.close()

# variables = pd.Series(data=np.arange(-15.0, 15.0, 0.5), index=np.arange(-15.0, 15.0, 0.5))
# wind_speed = 12
# # variables = np.arange(-15.0, 15.0, 0.5)
# gauss =  tools.gaussian_distribution(variables, standard_deviation=0.15*wind_speed, mean=0)
# gauss.index = gauss.index + wind_speed
# gauss.plot()
# plt.show()
# print(gauss)
