from windpowerlib import wind_turbine as wt
from windpowerlib import wind_farm as wf
import visualization_tools
import tools
import os
import pandas as pd
import feedin_time_series

# Get all turbine types of windpowerlib
#turbines = wt.get_turbine_types(print_out=False)
#visualization_tools.print_whole_dataframe(turbines)

# ----------------------------- Set parameters ------------------------------ #
pickle_load = True
weather_data = 'merra'
year = 2016
filename = os.path.join(os.path.dirname(__file__),
                        'dumps/weather', 'weather_df_merra_{0}.p'.format(year))

plot_arge_feedin = False  # If True all ArgeNetz data is plotted
plot_wind_farms = False  # If True usage of plot_or_print_farm()
plot_wind_turbines = False  # If True usage of plot_or_print_turbine()

if weather_data == 'merra':
    temporal_resolution_weather = 60
# --------------------- Turbine data and initialization --------------------- #
# TODO: scale power curves??
# Turbine data
enerconE70 = {
    'turbine_name': 'ENERCON E 70 2300',  # NOTE: Peak power should be 2.37 MW - is 2,31 for turbine in windpowerlib
    'hub_height': 64,  # in m
    'rotor_diameter': 71  # in m    source: www.wind-turbine-models.com
}
enerconE66 = {
    'turbine_name': 'ENERCON E 66 1800',  # NOTE: Peak power should be 1.86 MW - ist 1,8 for turbine in windpowerlib
    'hub_height': 65,  # in m
    'rotor_diameter': 70  # in m    source: www.wind-turbine-models.com
}

# Initialize WindTurbine objects
e70 = wt.WindTurbine(**enerconE70)
e66 = wt.WindTurbine(**enerconE66)
if plot_wind_turbines:
    visualization_tools.plot_or_print_turbine(e70)
    visualization_tools.plot_or_print_turbine(e66)

# ----------------------------- Wind farm data ------------------------------ #
# Bredstedt (54.578219, 8.978092)
bredstedt = {
    'wind_farm_name': 'Bredstedt',
    'wind_turbine_fleet': [{'wind_turbine': e70,
                            'number_of_turbines': 16}],
    'coordinates': [54.5, 8.75]
}
# Nordstrand (54.509708, 8.9007)
nordstrand = {
    'wind_farm_name': 'Nordstrand',
    'wind_turbine_fleet': [{'wind_turbine': e70,
                            'number_of_turbines': 6}],
    'coordinates': [54.5, 8.75]
}
# PPC_4919 (54.629167, 9.0625)
PPC_4919 = {
    'wind_farm_name': 'PPC_4919',
    'wind_turbine_fleet': [{'wind_turbine': e70,
                            'number_of_turbines': 13},
                           {'wind_turbine': e66,
                            'number_of_turbines': 4}],
    'coordinates': [55, 8.75]  # NOTE: lon exactly in between two coordinates
}
# PPC_4950 (54.629608, 9.029239)
PPC_4950 = {
    'wind_farm_name': 'PPC_4950',
    'wind_turbine_fleet': [{'wind_turbine': e70,
                            'number_of_turbines': 22}],
    'coordinates': [54.5, 8.75]
}
# PPC_5598 (54.596603, 8.968139)
PPC_5598 = {
    'wind_farm_name': 'PPC_5598',
    'wind_turbine_fleet': [{'wind_turbine': e70,
                            'number_of_turbines': 14}],
    'coordinates': [54.5, 8.75]
}

if year == 2015:
    wind_farm_data = [bredstedt, nordstrand, PPC_4919, PPC_4950, PPC_5598]
if (year == 2016 or year == 2017):
    wind_farm_data = [bredstedt, PPC_4919, PPC_4950, PPC_5598]

# ------------------------- Power output simulation ------------------------- #
# TODO: new section: weather (for different weather sources)
# TODO: actually only for more complex caluclations like this.. for simple calculations
#       modelchain can be used (if temperature is not beeing used)
# TODO: weather for all the ArgeNetz wind farms identical - if change: save
#first for eventual other time series
# Create data frame from csv if pickle_load == False
if pickle_load:
        data_frame = None
else:
    print('Read MERRA data from csv...')
    data_frame = pd.read_csv(os.path.join(
        os.path.dirname(__file__), 'data/Merra',
        'weather_data_GER_{0}.csv'.format(year)),
        sep=',', decimal='.', index_col=0)
#    lat, lon = visualization_tools.return_lats_lons(data_frame)
#    print(lat, lon)
merra_farms = []
for description in wind_farm_data:
    # Initialise wind farm
    wind_farm = wf.WindFarm(**description)
    # Get weather
    weather = tools.get_weather_data(pickle_load, filename, weather_data,
                                     year, wind_farm.coordinates, data_frame)
    data_height = {'wind_speed': 50,  # Source: https://data.open-power-system-data.org/weather_data/2017-07-05/
                   'roughness_length': 0,  # TODO: is this specified?
                   'temperature': weather.temperature_height,
                   'density': 0,
                   'pressure': 0}
    # Power output in W
    wind_farm.power_output = tools.power_output_sum(
        wind_farm.wind_turbine_fleet, weather, data_height)
    # Annual energy output in Wh
    wind_farm.annual_energy_output = tools.annual_energy_output(
        wind_farm.power_output, temporal_resolution_weather)
    merra_farms.append(wind_farm)


# TODO: weather object? with temporal_resultion attribute

if plot_wind_farms:
    visualization_tools.plot_or_print_farm(
        merra_farms, save_folder='Merra_power_output/{0}'.format(year),
        y_limit=[0, 6 * 10 ** 7])

# --------------------------- ArgeNetz Feedin Data -------------------------- #
if year == 2015:
    temporal_resolution_arge = 5
if (year == 2016 or year == 2017):
    temporal_resolution_arge = 1
arge_netz_data = feedin_time_series.get_and_plot_feedin(
    year, plot=plot_arge_feedin)
power_output_series = []

arge_farms = []
for description in wind_farm_data:
    # Initialise wind farm
    wind_farm = wf.WindFarm(**description)
    # Power output in W
    wind_farm.power_output = arge_netz_data[description['wind_farm_name']
                                            + '_P_W'] * 1000
    # Annual energy output in Wh
    wind_farm.annual_energy_output = tools.annual_energy_output(
        wind_farm.power_output, temporal_resolution_arge)
    arge_farms.append(wind_farm)
