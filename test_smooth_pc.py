from windpowerlib.wind_turbine import WindTurbine
from windpowerlib import power_output, tools
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import os
import pickle

enerconE126 = {
        'turbine_name': 'ENERCON E 126 7500',  # turbine name as in register
        'hub_height': 135,  # in m
        'rotor_diameter': 127  # in m
    }
# initialise WindTurbine object
e126 = WindTurbine(**enerconE126)

# Weather data for TI
# filename_weather = os.path.join(os.path.dirname(__file__), '../../MA_lib_validation/lib_validation/dumps/weather',
#                                     'weather_df_{0}_{1}.p'.format(
#                                         'open_FRED', 2015))
# of_weather = pickle.load(open(filename_weather, 'rb'))
z0 = pd.Series([0.04,0.04,0.04])
turbulence_intensity = 1 / np.log(135/z0.mean())
# turbulence_intensity = (2.4 * 0.41) / np.log(135/z0.mean()) * np.exp(-135/500)
smoothed_power_curve = power_output.smooth_power_curve(
    e126.power_curve.wind_speed, e126.power_curve['values'],
    block_width=0.05, normalized_standard_deviation=turbulence_intensity)

print(turbulence_intensity)

# print(e126.power_curve)
# print(smoothed_power_curve)

plt.plot(e126.power_curve['wind_speed'], e126.power_curve['values'])
plt.plot(smoothed_power_curve['wind_speed'], smoothed_power_curve['values'])
plt.show()


# variables = pd.Series(data=np.arange(-15.0, 15.0, 0.5), index=np.arange(-15.0, 15.0, 0.5))
# wind_speed = 12
# # variables = np.arange(-15.0, 15.0, 0.5)
# gauss =  tools.gaussian_distribution(variables, standard_deviation=0.15*wind_speed, mean=0)
# gauss.index = gauss.index + wind_speed
# gauss.plot()
# plt.show()
# print(gauss)