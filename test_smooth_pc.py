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

#enerconE126 = {
#        'turbine_name': 'ENERCON E 126 7500',  # turbine name as in register
#        'hub_height': 135,  # in m
#        'rotor_diameter': 127  # in m
#    }
## initialise WindTurbine object
#e126 = WindTurbine(**enerconE126)
#
## Weather data for TI
## filename_weather = os.path.join(os.path.dirname(__file__), '../../MA_lib_validation/lib_validation/dumps/weather',
##                                     'weather_df_{0}_{1}.p'.format(
##                                         'open_FRED', 2015))
## of_weather = pickle.load(open(filename_weather, 'rb'))
#z0 = pd.Series([0.04,0.04,0.04])
#turbulence_intensity = 1 / np.log(135/z0.mean())
## turbulence_intensity = (2.4 * 0.41) / np.log(135/z0.mean()) * np.exp(-135/500)
#smoothed_power_curve = power_output.smooth_power_curve(
#    e126.power_curve.wind_speed, e126.power_curve['values'],
#    block_width=0.05, normalized_standard_deviation=turbulence_intensity)
#
#print(turbulence_intensity)
#
## print(e126.power_curve)
## print(smoothed_power_curve)
#
#plt.plot(e126.power_curve['wind_speed'], e126.power_curve['values'])
#plt.plot(smoothed_power_curve['wind_speed'], smoothed_power_curve['values'])
#plt.show()
#plt.close()
#
## variables = pd.Series(data=np.arange(-15.0, 15.0, 0.5), index=np.arange(-15.0, 15.0, 0.5))
## wind_speed = 12
## # variables = np.arange(-15.0, 15.0, 0.5)
## gauss =  tools.gaussian_distribution(variables, standard_deviation=0.15*wind_speed, mean=0)
## gauss.index = gauss.index + wind_speed
## gauss.plot()
## plt.show()
## print(gauss)
#
#
#enerconE70 = {
#            'turbine_name': 'ENERCON E 70 2300',
#            'hub_height': 64,
#            'rotor_diameter': 71
#        }
#enerconE66 = {
#            'turbine_name': 'ENERCON E 66 1800',
#            'hub_height': 65,
#            'rotor_diameter': 70
#        }
#vestasV126 = {
#            'turbine_name': 'VESTAS V 126 3300',
#            'hub_height': 117,
#            'rotor_diameter': 126
#        }
#
#
#e70 = WindTurbine(**enerconE70)
#e66 = WindTurbine(**enerconE66)
#v126 = WindTurbine(**vestasV126)
#parameters = {'wind_turbine_fleet': [{'wind_turbine': e70,
#                                      'number_of_turbines': 13},
#                                     {'wind_turbine': e66,
#                                      'number_of_turbines': 4},
#                                      {'wind_turbine': v126,
#                                      'number_of_turbines': 2}],
#              'smoothing': True,
#              'density_correction': False,
#              'roughness_length': 0.4
#              }
#power_curve_exp = 2
#summarized_power_curve_df = summarized_power_curve(**parameters)
#print(summarized_power_curve_df)
#
## plt.plot(summarized_power_curve_df['wind_speed'], summarized_power_curve_df['values'])
## plt.show()
## plt.close()

e70, e66 = wind_farm_specifications.initialize_turbines(['enerconE70',
                                                         'enerconE66'])
wf_3 = {
    'wind_farm_name': 'wf_3',
    'wind_turbine_fleet': [{'wind_turbine': e70,
                            'number_of_turbines': 13},
                           {'wind_turbine': e66,
                            'number_of_turbines': 4}],
    'coordinates': [54.629167, 9.0625]}
wf = WindFarm(**wf_3)
