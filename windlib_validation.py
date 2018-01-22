import pandas as pd
import matplotlib.pyplot as mpl

from windpowerlib.modelchain import ModelChain
from windpowerlib.wind_turbine import WindTurbine

##############################################################################
# read windpark data
##############################################################################

windfarm = 'WF3' # {'WF1', 'WF2', 'WF3'}
year = 2015
file_directory = 'data/Daten_Twele/processed_data/'
windfarm_df = pd.read_csv(file_directory + '{}_{}.csv'.format(windfarm, year),
                          header=[0], index_col=[0], parse_dates=True)
# resample to same resolution as FRED weather data
windfarm_df = windfarm_df.resample('30Min').mean()
windfarm_df = windfarm_df.tz_localize('UTC')
#htw_wr3_data = htw_wr3_data.tz_convert('UTC')

##############################################################################
# get weather data FRED
##############################################################################

file_directory = 'data/Fred/BB_2015/'
fred_weather_data = pd.read_csv(
    file_directory + 'fred_data_2015_{}.csv'.format(windfarm),
    header=[0, 1], index_col=[0], parse_dates=True)
fred_weather_data = fred_weather_data.tz_localize('UTC')

# change type of height from str to int by resetting columns
fred_weather_data.columns = [fred_weather_data.axes[1].levels[0][
                                 fred_weather_data.axes[1].labels[0]],
                             fred_weather_data.axes[1].levels[1][
                                 fred_weather_data.axes[1].labels[1]].astype(
                                 int)]

##############################################################################
# compare FRED and windpark weather data - wind speed
##############################################################################

single_turbine = {'WF1': '6_8', 'WF2': '7_1', 'WF3': '8_2'}
hub_height = {'WF1': 105, 'WF2': 105, 'WF3': 60}
wt = WindTurbine(**{'turbine_name': 'VESTAS V 90 2000',
                    'hub_height': hub_height[windfarm],
                    'rotor_diameter': 127})
mc = ModelChain(wt)
wind_speed_hub = mc.wind_speed_hub(fred_weather_data)
wind_speed_hub.name = 'wind_speed_hub'

# columns with wind speed
columns_wind_speed = [i for i in windfarm_df if 'wind_speed' in i]
wind_speed_df = windfarm_df[columns_wind_speed]
wind_speed_df = wind_speed_df.join(wind_speed_hub.to_frame())

# calculate monthly correlation for each wind turbine in the windpark
counter = 0
for col_name in columns_wind_speed:
    corr_df_tmp = wind_speed_df[[col_name, 'wind_speed_hub']]
    corr = corr_df_tmp.resample('1M').agg(
        {'corr' : lambda x: x[corr_df_tmp.columns[0]].corr(
            x[corr_df_tmp.columns[1]])})
    corr = corr[corr.columns[0]]
    corr.name = corr.name[1]
    if counter == 0:
        corr_df = corr.to_frame()
    else:
        corr_df = corr_df.join(corr.to_frame())
    counter += 1

# plot correlation
corr_df.plot(figsize=(15, 10))
mpl.savefig('telko/wind/wind_speed_correlation_monthly_{}.pdf'.format(
    windfarm))
# plot january week
index = pd.date_range(start='1/25/2015', end='2/1/2015',
                      freq='30Min', tz='UTC')
wind_speed_df.loc[index, :].plot(figsize=(15, 10))
mpl.savefig('telko/wind/wind_speed_january_week_{}.pdf'.format(windfarm))
wind_speed_df[['wf_{}_wind_speed'.format(single_turbine[windfarm]),
               'wind_speed_hub']].loc[index, :].plot(figsize=(15, 10))
mpl.savefig('telko/wind/wind_speed_january_week_{}_single.pdf'.format(
    windfarm))
# plot june week
index = pd.date_range(start='6/2/2015', end='6/8/2015',
                      freq='30Min', tz='UTC')
wind_speed_df.loc[index, :].plot(figsize=(15, 10))
mpl.savefig('telko/wind/wind_speed_june_week_{}.pdf'.format(windfarm))
wind_speed_df[['wf_{}_wind_speed'.format(single_turbine[windfarm]),
               'wind_speed_hub']].loc[index, :].plot(figsize=(15, 10))
mpl.savefig('telko/wind/wind_speed_june_week_{}_single.pdf'.format(
    windfarm))

##############################################################################
# compare FRED and windpark weather data - wind direction
##############################################################################

# columns with wind direction
wind_direction_height = {'WF1': [100, 120], 'WF2': [100, 120], 'WF3': [80, 10]}
columns_wind_direction = [i for i in windfarm_df if 'wind_dir' in i]
wind_direction_df = windfarm_df[columns_wind_direction]
wind_direction_df = wind_direction_df.join(
    fred_weather_data['wind_direction'][
        wind_direction_height[windfarm][0]].to_frame())
wind_direction_df = wind_direction_df.join(
    fred_weather_data['wind_direction'][
        wind_direction_height[windfarm][1]].to_frame())

# calculate monthly correlation for each wind turbine in the windpark
counter = 0
for col_name in columns_wind_direction:
    corr_df_tmp = wind_direction_df[[col_name,
                                     wind_direction_height[windfarm][0]]]
    corr = corr_df_tmp.resample('1M').agg(
        {'corr' : lambda x: x[corr_df_tmp.columns[0]].corr(
            x[corr_df_tmp.columns[1]])})
    corr = corr[corr.columns[0]]
    corr.name = corr.name[1]
    if counter == 0:
        corr_df = corr.to_frame()
    else:
        corr_df = corr_df.join(corr.to_frame())
    counter += 1

# plot correlation
corr_df.plot(figsize=(15, 10))
mpl.savefig('telko/wind/wind_direction_correlation_monthly_{}.pdf'.format(
    windfarm))
# plot january week
index = pd.date_range(start='1/25/2015', end='2/1/2015',
                      freq='30Min', tz='UTC')
wind_direction_df.loc[index, :].plot(figsize=(15, 10))
mpl.savefig('telko/wind/wind_direction_january_week_{}.pdf'.format(windfarm))
wind_direction_df[['wf_{}_wind_dir'.format(single_turbine[windfarm]),
                   wind_direction_height[windfarm][0]]].loc[index, :].plot(
    figsize=(15, 10))
mpl.savefig('telko/wind/wind_direction_january_week_{}_single.pdf'.format(
    windfarm))
# plot june week
index = pd.date_range(start='6/2/2015', end='6/8/2015',
                      freq='30Min', tz='UTC')
wind_direction_df.loc[index, :].plot(figsize=(15, 10))
mpl.savefig('telko/wind/wind_direction_june_week_{}.pdf'.format(windfarm))
wind_direction_df[['wf_{}_wind_dir'.format(single_turbine[windfarm]),
                   wind_direction_height[windfarm][0]]].loc[index, :].plot(
    figsize=(15, 10))
mpl.savefig('telko/wind/wind_direction_june_week_{}_single.pdf'.format(
    windfarm))
