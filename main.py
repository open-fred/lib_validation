from windpowerlib import wind_turbine as wt
from windpowerlib import wind_farm as wf
import visualization_tools
import analysis_tools
import tools
import os
import pandas as pd
import numpy as np
import feedin_time_series

# Get all turbine types of windpowerlib
#turbines = wt.get_turbine_types(print_out=False)
#visualization_tools.print_whole_dataframe(turbines)

# ----------------------------- Set parameters ------------------------------ #
pickle_load_weather = True
pickle_load_arge = True
weather_data = 'MERRA'
validation_data = 'ArgeNetz'
year = 2015
filename_weather = os.path.join(os.path.dirname(__file__),
                                'dumps/weather',
                                'weather_df_merra_{0}.p'.format(year))


evaluate_power_output = False # delete
output_methods = [
    'hourly_energy_output',
    'monthly_energy_output'
    ]
visualization_methods = [
    'box_plots',
    'test'
    ]

plot_arge_feedin = False  # If True all ArgeNetz data is plotted
plot_wind_farms = False  # If True usage of plot_or_print_farm()
plot_wind_turbines = False  # If True usage of plot_or_print_turbine()

latex_output = False  # If True Latex tables will be created

if weather_data == 'MERRA':
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
# Create data frame from csv if pickle_load_weather == False
if pickle_load_weather:
        data_frame = None
else:
    print('Read MERRA data from csv...')
    data_frame = pd.read_csv(os.path.join(
        os.path.dirname(__file__), 'data/Merra',
        'weather_data_GER_{0}.csv'.format(year)),
        sep=',', decimal='.', index_col=0)
    # Visualize latitudes and longitudes of DataFrame
#    lat, lon = visualization_tools.return_lats_lons(data_frame)
#    print(lat, lon)

merra_farms = []
for description in wind_farm_data:
    # Initialise wind farm
    wind_farm = wf.WindFarm(**description)
    # Get weather
    weather = tools.get_weather_data(pickle_load_weather, filename_weather,
                                     weather_data, year,
                                     wind_farm.coordinates, data_frame)
    if year == 2015:
#        visualization_tools.print_whole_dataframe(weather.lat)
        weather = weather.loc[weather.index >= '2015-05-01']
#        visualization_tools.print_whole_dataframe(weather.lat) # TODO: check time zone (sometimes +1h sometimes +2h)
    data_height = {'wind_speed': 50,  # Source: https://data.open-power-system-data.org/weather_data/2017-07-05/
                   'roughness_length': 0,  # TODO: is this specified?
                   'temperature': weather.temperature_height,
                   'density': 0,
                   'pressure': 0}
    # Power output in MW
    wind_farm.power_output = tools.power_output_sum(
        wind_farm.wind_turbine_fleet, weather, data_height) / (1*10**6)
    # Annual energy output in MWh
    wind_farm.annual_energy_output = tools.annual_energy_output(
        wind_farm.power_output, temporal_resolution_weather)
    merra_farms.append(wind_farm)


# TODO: weather object? with temporal_resultion attribute

if plot_wind_farms:
    y_limit = [0, 60]
    visualization_tools.plot_or_print_farm(
        merra_farms, save_folder='Merra_power_output/{0}'.format(year),
        y_limit=y_limit)

# --------------------------- ArgeNetz Feedin Data -------------------------- #
# Set temporal resolution and create indices for DataFrame in standardized form
if year == 2015:
    temporal_resolution_arge = 5  # minutes
    indices = tools.get_indices_for_series(temporal_resolution_arge,
                                           start='5/1/2015' , end='1/1/2016')
if (year == 2016 or year == 2017):
    temporal_resolution_arge = 1  # minutes
    indices = tools.get_indices_for_series(temporal_resolution_arge, year=year)

# Get ArgeNetz Data
arge_netz_data = feedin_time_series.get_and_plot_feedin(
    year, pickle_load=pickle_load_arge, plot=plot_arge_feedin)

# Initialise Arge wind farms with power output and annual energy output
arge_farms = []
for description in wind_farm_data:
    # Initialise wind farm
    wind_farm = wf.WindFarm(**description)
    # Power output in MW with standard indices
    wind_farm.power_output = pd.Series(
        data=(arge_netz_data[description['wind_farm_name'] + 
                             '_P_W'].values / 1000),
        index=indices)
    # Annual energy output in MWh
    wind_farm.annual_energy_output = tools.annual_energy_output(
        wind_farm.power_output, temporal_resolution_arge)
    arge_farms.append(wind_farm)

if plot_arge_feedin:
#    y_limit = [0, 60]
    y_limit = None
    visualization_tools.plot_or_print_farm(
        arge_farms, save_folder='ArgeNetz_power_output/Plots_{0}'.format(year),
        y_limit=y_limit)

# ------------------------------ Data Evaluation ---------------------------- #
# TODO: statt arge_farms, merra_farms more generic: validation_farms, simulation_farms
validation_sets= []
if 'hourly_energy_output' in output_methods:
    # ValidationObjects!!!!!
    val_set_hourly_energy = analysis_tools.evaluate_feedin_time_series(
        arge_farms, merra_farms, temporal_resolution_arge,
        temporal_resolution_weather, 'H', 'hourly_energy_output',
        validation_data, weather_data) # time_period
    validation_sets.append(val_set_hourly_energy)

if 'monthly_energy_output' in output_methods:
    val_set_monthly_energy = analysis_tools.evaluate_feedin_time_series(
        arge_farms, merra_farms, temporal_resolution_arge,
        temporal_resolution_weather, 'M', 'monthly_energy_output',
        validation_data, weather_data) # time_period
    validation_sets.append(val_set_monthly_energy)

# Specify folder for saving the plots
save_folder='../Plots/{0}/{1}/'.format(
                year, weather_data + '_' + validation_data) # TODO: maybe move up

for validation_set in validation_sets:
    if 'box_plots' in visualization_methods:
        # All bias time series of a validation set in one DataFrame for Boxplot
        bias_df = pd.DataFrame()
        for validation_object in validation_set:
            df_part = pd.DataFrame(data=validation_object.bias,
                                   columns=[validation_object.wind_farm_name])
            bias_df = pd.concat([bias_df, df_part], axis=1)
        # Specify filename
        filename = save_folder + '{0}_Boxplot_{1}_{2}_{3}.pdf'.format(
                validation_set[0].output_method, year,
                validation_data, weather_data)
        visualization_tools.box_plots_bias(
            bias_df, filename=filename,
            title='Deviation of {0} {1} from {2} in {3}.'.format(
                weather_data, validation_set[0].output_method.replace('_',' '),
                validation_data, year))
    if '...' in visualization_methods:
        pass

if evaluate_power_output:
    # Compare power output
    series = merra_farms[0].power_output
    index = pd.date_range('1/1/{0}'.format(year+1), tz='Europe/Berlin', closed='left', periods=1)
    series2 = pd.Series(10, index=index)
    merra_farm = pd.concat([series, series2])
    out = merra_farm.resample(
        '{0}min'.format(temporal_resolution_arge)).pad()
    pd.options.display.max_rows = 500
    print(out)
#    print(out[436400:436400])
#    print(out.tail(1).index)
    out = out.drop(out.index[-1])
    

# ---------------------------------- LaTeX Output --------------------------- #
if latex_output:
    all_farm_lists = [arge_farms, merra_farms]
    column_names = ['ArgeNetz', 'MERRA']  # evtl als if abfrage in funktion
    df = pd.DataFrame()
    i = 0
    for farm_list in all_farm_lists:
        index = [farm.wind_farm_name for farm in farm_list]
        # Annual energy output in GWh
        data = [round(farm.annual_energy_output, 3)
                for farm in farm_list]
        df_temp = pd.DataFrame(data=data, index=index,
                               columns=[[column_names[i]],
                                        ['Energy Output [MWh]']])
        df = pd.concat([df, df_temp], axis=1)
        if i != 0:
            data = [round((farm_list[j].annual_energy_output -
                          all_farm_lists[0][j].annual_energy_output) /
                          all_farm_lists[0][j].annual_energy_output * 100, 3)
                    for j in range(len(arge_farms))]
            df_temp = pd.DataFrame(
                data=data, index=index,
                columns=[[column_names[i]], ['Deviation [%]']])
            df = pd.concat([df, df_temp], axis=1)
        i += 1
    
    path_latex_tables = os.path.join(os.path.dirname(__file__),
                                     '../../../tubCloud/Latex/Tables/')
    name = os.path.join(path_latex_tables, 'name_of_table.tex')
    # TODO: make fully customized table
    df.to_latex(buf=name)

print('# ----------- Done ----------- #')
