import pandas as pd
import matplotlib.pyplot as mpl

import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib import irradiance

##############################################################################
# read HTW converter data
##############################################################################

file_directory = 'data/htw_2015/einleuchtend_data_2015/'
htw_wr3_data = pd.read_csv(
    file_directory + 'einleuchtend_wrdata_2015_wr3.csv',
    sep=';', header=[0], index_col=[0], parse_dates=True)
# resample to same resolution as FRED weather data
htw_wr3_data = htw_wr3_data.resample('30Min').mean()

##############################################################################
# get weather data HTW
##############################################################################

htw_weather_data = pd.read_csv(
    file_directory + 'htw_wetter_weatherdata_2015.csv',
    sep=';', header=[0], index_col=[0], parse_dates=True)

# select and rename columns
columns = {'G_hor_CMP6': 'ghi',
           'G_gen_CMP11': 'gni',
           'v_Wind': 'wind_speed',
           'T_Luft': 'temp_air'}
htw_weather_data = htw_weather_data[list(columns.keys())]
htw_weather_data.rename(columns=columns, inplace=True)
# resample to same resolution as FRED weather data
htw_weather_data = htw_weather_data.resample('30Min').mean()

##############################################################################
# get weather data FRED
##############################################################################

file_directory = 'data/htw_2015/'
fred_weather_data = pd.read_csv(
    file_directory + 'fred_data_2015_htw.csv',
    header=[0], index_col=[0], parse_dates=True)
fred_weather_data['ghi'] = fred_weather_data['dhi'] + \
                           fred_weather_data['dirhi']

fred_weather_data['temp_air'] = fred_weather_data['temp_air'] - 273.15

##############################################################################
# compare FRED and HTW weather data
##############################################################################

# # ghi
# # setup dataframe with ghi of HTW and FRED
# ghi = fred_weather_data['ghi'].to_frame().join(
#     htw_weather_data['ghi'].to_frame(), lsuffix='_fred', rsuffix='_htw')
# # calculate monthly correlation
# corr_ghi = ghi.resample('1M').agg({'corr' : lambda x: x[ghi.columns[0]].corr(
#     x[ghi.columns[1]])})
# corr_ghi = corr_ghi[corr_ghi.columns[0]]
# # plot correlation
# corr_ghi.plot()
# mpl.savefig('telko/pv/ghi_correlation_monthly.pdf')
# # plot january week
# index = pd.date_range(start='1/25/2015', end='2/1/2015', freq='30Min')
# ghi.loc[index, :].plot()
# mpl.show()
# mpl.savefig('telko/pv/ghi_january_week.pdf')
# # plot june week
# index = pd.date_range(start='6/2/2015', end='6/8/2015', freq='30Min')
# ghi.loc[index, :].plot()
# mpl.show()
# mpl.savefig('telko/pv/ghi_june_week.pdf')

# # gni
# # setup dataframe with gni of HTW and FRED
# fred_weather_data['gni'] = fred_weather_data['dni_2'] + \
#                            fred_weather_data['dhi']
# gni = fred_weather_data['gni'].to_frame().join(
#     htw_weather_data['gni'].to_frame(), lsuffix='_fred', rsuffix='_htw')
# # calculate monthly correlation
# corr_gni = gni.resample('1M').agg({'corr' : lambda x: x[gni.columns[0]].corr(
#     x[gni.columns[1]])})
# corr_gni = corr_gni[corr_gni.columns[0]]
# # plot correlation
# corr_gni.plot()
# mpl.savefig('telko/pv/gni_correlation_monthly.pdf')
# # plot january week
# index = pd.date_range(start='1/25/2015', end='2/1/2015', freq='30Min')
# gni.loc[index, :].plot()
# #mpl.show()
# mpl.savefig('telko/pv/gni_january_week.pdf')
# # plot june week
# index = pd.date_range(start='6/2/2015', end='6/8/2015', freq='30Min')
# gni.loc[index, :].plot()
# #mpl.show()
# mpl.savefig('telko/pv/gni_june_week.pdf')

# dni
# setup dataframe with dni of FRED and calculated dni
fred_weather_data_tz = fred_weather_data.copy()
# save initial index in column 'time'
fred_weather_data_tz.reset_index(inplace=True)
fred_weather_data_tz.set_index('time', drop=False, inplace=True)
# localize index
fred_weather_data_tz = fred_weather_data_tz.tz_localize('Etc/GMT+0')
# ToDo: is timedelta needed?
fred_weather_data_tz['new_index'] = fred_weather_data_tz.index +\
                                    pd.Timedelta(minutes=15)
fred_weather_data_tz.set_index('new_index', drop=True, inplace=True)
# calculate dni using the pvlib
times = fred_weather_data_tz.index
location = Location(latitude=52.456032, longitude=13.525282,
                    tz='Etc/GMT+1', altitude=60, name='HTW Berlin')
solarposition = location.get_solarposition(
    times, pressure=None, temperature=fred_weather_data_tz['temp_air'])
clearsky = location.get_clearsky(times, solar_position=solarposition)
calculated_dni = irradiance.dni(fred_weather_data_tz['ghi'],
                                fred_weather_data_tz['dhi'],
                                zenith=solarposition['zenith'],
                                clearsky_dni=clearsky['dni'],
                                clearsky_tolerance=1.1,
                                zenith_threshold_for_zero_dni=88.0,
                                zenith_threshold_for_clearsky_limit=80.0)
# setup df with calculated and Fred dni
dni = fred_weather_data_tz['dni_2'].to_frame().join(
    calculated_dni.to_frame())
dni.rename(columns={'dni_2': 'dni_FRED', 0: 'dni_pvlib'}, inplace=True)
dni = dni.join(fred_weather_data_tz['time'])
dni.set_index('time', inplace=True)
# calculate monthly correlation
corr_dni = dni.resample('1M').agg({'corr' : lambda x: x[dni.columns[0]].corr(
    x[dni.columns[1]])})
corr_dni = corr_dni[corr_dni.columns[0]]
# plot correlation
corr_dni.plot()
mpl.savefig('telko/pv/dni_correlation_monthly.pdf')
# plot january week
index = pd.date_range(start='1/18/2015', end='1/24/2015', freq='30Min')
dni.loc[index, :].plot()
#mpl.show()
mpl.savefig('telko/pv/dni_january_week.pdf')
# plot june week
index = pd.date_range(start='6/2/2015', end='6/8/2015', freq='30Min')
dni.loc[index, :].plot()
#mpl.show()
mpl.savefig('telko/pv/dni_june_week.pdf')

##############################################################################
# setup modules
##############################################################################

# get module and inverter parameters
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
sandia_inverters = pvlib.pvsystem.retrieve_sam('sandiainverter')
CEC_modules = pvlib.pvsystem.retrieve_sam('CECMod')
CEC_inverters = pvlib.pvsystem.retrieve_sam('sandiainverter')

inv_sma = 'SMA_Solar_Technology_AG__SB3000HFUS_30___240V_240V__CEC_2011_'
inv_danfoss = 'Danfoss_Solar__DLX_2_9_UL__240V__240V__CEC_2013_'

# module 1 - Schott aSi 105W / Danfoss DLX 2.9
# module 2 - Aleo S19 285W / Danfoss DLX 2.9 'Aleo_Solar_S19H270' CEC

# module 3 - Aleo S18 240W / Danfoss DLX 2.9
module_3 = PVSystem(surface_tilt=14.57, surface_azimuth=215., albedo=0.2,
                    module='aleo_solar_S18_240', inverter=inv_danfoss,
                    module_parameters=CEC_modules['aleo_solar_S18_240'],
                    modules_per_string=14, strings_per_inverter=1,
                    inverter_parameters=CEC_inverters[inv_danfoss],
                    name='HTW_module_3')
module_3.module_parameters['EgRef'] = 1.121
module_3.module_parameters['dEgdT'] = -0.0002677
module_3.module_parameters['alpha_sc'] = 0.04

# module 4 - Aleo S19 245W / SMA SB 3000HF-30 'Aleo_Solar_S19U245_ulr' CEC
# module 5 - Schott aSi 105W / SMA SB 3000HF-30
#
# ############################################################################
# # setup location
# ############################################################################

location = Location(latitude=52.456032, longitude=13.525282,
                    tz='Etc/GMT+2', altitude=60, name='HTW Berlin')

##############################################################################
# call modelchain
##############################################################################

# pvlib's ModelChain
mc = ModelChain(system=module_3, location=location,
                aoi_model='no_loss', spectral_model='no_loss')
pvlib_data = fred_weather_data.tz_localize('Etc/GMT+2')
pvlib_data['dni'] = pvlib_data['dni_2']
mc.run_model(pvlib_data.index, weather=pvlib_data)
# mc.dc.p_mp.fillna(0).plot()
# htw_wr3_data['P_DC'].plot()
# mpl.show()
# print('x')

# calculate monthly correlation
corr_feedin_3 = mc.dc.p_mp.to_frame().join(htw_wr3_data['P_DC'].to_frame())
corr_feedin_3 = corr_feedin_3.resample('1M').agg(
    {'corr' : lambda x: x[corr_feedin_3.columns[0]].corr(
        x[corr_feedin_3.columns[1]])})
corr_feedin_3 = corr_feedin_3[corr_feedin_3.columns[0]]
# plot correlation
corr_feedin_3.plot()
mpl.savefig('telko/pv/feedin_wr3_correlation_monthly.pdf')
# plot january week
index = pd.date_range(start='1/18/2015', end='1/24/2015', freq='30Min')
corr_feedin_3.loc[index, :].plot()
#mpl.show()
mpl.savefig('telko/pv/feedin_wr3_january_week.pdf')
# plot june week
index = pd.date_range(start='6/2/2015', end='6/8/2015', freq='30Min')
corr_feedin_3.loc[index, :].plot()
#mpl.show()
mpl.savefig('telko/pv/feedin_wr3_june_week.pdf')

#
# # plot the results
# dc = mc.dc.p_mp.sum()
# ac = mc.ac.sum()
# diff = dc - ac
# print("dc = ", dc)
# print("ac = ", ac)
# print("diff = ", diff)
#
# logging.info('Done!')

# if plt:
#     mc.dc.p_mp.fillna(0).plot()
#     plt.show()
# else:
#     logging.warning("No plots shown. Install matplotlib to see the plots.")