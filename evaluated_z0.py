from wind_farm_specifications import (get_joined_wind_farm_data,
                                      get_wind_farm_data)
from open_fred_weather_data import get_open_fred_data
import tools
import os

def evaluate_z0_data(weather_data_name, wind_farm_data, year,
                     temperature_heights=None):
    filename_weather = os.path.join(
        os.path.dirname(__file__), 'dumps/weather',
        'weather_df_{0}_{1}.p'.format(weather_data_name, year))
    for wf_data in wind_farm_data:
        wf_name = wf_data['object_name']
        # Get weather data
        weather = tools.get_weather_data(
            weather_data_name, wf_data['coordinates'], pickle_load=True,
            filename=filename_weather, year=year,
            temperature_heights=temperature_heights)
        z0 = weather['roughness_length']

if __name__ == "__main__":
    years = [
        2015,
        2016
    ]
    weather_data_names = ['MERRA', 'open_FRED']
    temperature_heights = [60, 64, 65, 105, 114]
    # Get wind farm data
    filenames = ['farm_specification_argenetz_2015.p',
                 'farm_specification_argenetz_2016.p',
                 'farm_specification_enertrag_2016.p',
                 'farm_specification_greenwind_2015.p',
                 'farm_specification_greenwind_2016.p']
    wind_farm_pickle_folder = os.path.join(os.path.dirname(__file__),
                                           'dumps/wind_farm_data')
    wind_farm_data = get_joined_wind_farm_data(
        filenames, wind_farm_pickle_folder, pickle_load=True)
    for weather_data_name in weather_data_names:
        for year in years:
            evaluate_z0_data(weather_data_name, wind_farm_data, year,
                             temperature_heights)