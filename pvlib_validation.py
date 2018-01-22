import pandas as pd
import matplotlib.pyplot as mpl
import numpy as np

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
htw_wr3_data = htw_wr3_data.tz_localize('Etc/GMT-1')
htw_wr3_data = htw_wr3_data.tz_convert('UTC')

htw_wr4_data = pd.read_csv(
    file_directory + 'einleuchtend_wrdata_2015_wr4.csv',
    sep=';', header=[0], index_col=[0], parse_dates=True)
# resample to same resolution as FRED weather data
htw_wr4_data = htw_wr4_data.resample('30Min').mean()
htw_wr4_data = htw_wr4_data.tz_localize('Etc/GMT-1')
htw_wr4_data = htw_wr4_data.tz_convert('UTC')

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
htw_weather_data = htw_weather_data.tz_localize('Etc/GMT-1')
htw_weather_data = htw_weather_data.tz_convert('UTC')

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
fred_weather_data = fred_weather_data.tz_localize('UTC')

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
# index = pd.date_range(start='1/25/2015', end='2/1/2015',
#                       freq='30Min', tz='UTC')
# ghi.loc[index, :].plot()
# mpl.savefig('telko/pv/ghi_january_week.pdf')
# # plot june week
# index = pd.date_range(start='6/2/2015', end='6/8/2015',
#                       freq='30Min', tz='UTC')
# ghi.loc[index, :].plot()
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
# index = pd.date_range(start='1/25/2015', end='2/1/2015',
#                       freq='30Min', tz='UTC')
# gni.loc[index, :].plot()
# mpl.savefig('telko/pv/gni_january_week.pdf')
# # plot june week
# index = pd.date_range(start='6/2/2015', end='6/8/2015',
#                       freq='30Min', tz='UTC')
# gni.loc[index, :].plot()
# mpl.savefig('telko/pv/gni_june_week.pdf')

# # dni
# # setup dataframe with dni of FRED and calculated dni
# # save initial index in column 'time'
# fred_weather_data_tz = fred_weather_data.copy()
# fred_weather_data_tz.reset_index(inplace=True)
# fred_weather_data_tz.set_index('time', drop=False, inplace=True)
# # ToDo: is timedelta needed?
# fred_weather_data_tz['new_index'] = fred_weather_data_tz.index + \
#                                     pd.Timedelta(minutes=15)
# fred_weather_data_tz.set_index('new_index', drop=True, inplace=True)
# # calculate dni using the pvlib
# times = fred_weather_data_tz.index
# location = Location(latitude=52.456032, longitude=13.525282,
#                     tz='Etc/GMT+1', altitude=60, name='HTW Berlin')
# solarposition = location.get_solarposition(
#     times, pressure=None, temperature=fred_weather_data_tz['temp_air'])
# clearsky = location.get_clearsky(times, solar_position=solarposition)
# calculated_dni = irradiance.dni(fred_weather_data_tz['ghi'],
#                                 fred_weather_data_tz['dhi'],
#                                 zenith=solarposition['zenith'],
#                                 clearsky_dni=clearsky['dni'],
#                                 clearsky_tolerance=1.1,
#                                 zenith_threshold_for_zero_dni=88.0,
#                                 zenith_threshold_for_clearsky_limit=80.0)
# calculated_dni_uncorrected = (fred_weather_data_tz['ghi'] -
#                               fred_weather_data_tz['dhi']) / np.cos(
#     np.radians(solarposition['zenith']))
# # setup df with calculated and Fred dni
# dni = fred_weather_data_tz['dni_2'].to_frame().join(
#     calculated_dni.to_frame())
# dni.rename(columns={'dni_2': 'dni_FRED', 0: 'dni_pvlib'}, inplace=True)
# dni = dni.join(calculated_dni_uncorrected.to_frame())
# dni.rename(columns={0: 'dni_uncorrected'}, inplace=True)
# dni = dni.join(fred_weather_data_tz['time'])
# dni.set_index('time', inplace=True)
# # calculate monthly correlation
# corr_pvlib = dni[['dni_FRED', 'dni_pvlib']]
# corr_dni_pvlib = corr_pvlib.resample('1M').agg(
#     {'corr' : lambda x: x[corr_pvlib.columns[0]].corr(
#         x[corr_pvlib.columns[1]])})
# corr_dni_pvlib = corr_dni_pvlib[corr_dni_pvlib.columns[0]]
# corr_uncorr = dni[['dni_FRED', 'dni_uncorrected']]
# corr_dni_uncorr = corr_uncorr.resample('1M').agg(
#     {'corr' : lambda x: x[corr_uncorr.columns[0]].corr(
#         x[corr_uncorr.columns[1]])})
# corr_dni_uncorr = corr_dni_uncorr[corr_dni_uncorr.columns[0]]
# corr_dni = corr_dni_pvlib.to_frame().join(corr_dni_uncorr.to_frame(),
#                                           lsuffix='pvlib',
#                                           rsuffix='uncorrected')
# # plot correlation
# corr_dni.plot()
# mpl.savefig('telko/pv/dni_correlation_monthly.pdf')
# # plot january week
# index = pd.date_range(start='1/18/2015', end='1/24/2015',
#                       freq='30Min', tz='UTC')
# dni.loc[index, :].plot()
# mpl.savefig('telko/pv/dni_january_week_incl_uncorrected_dni.pdf')
# dni[['dni_FRED', 'dni_pvlib']].loc[index, :].plot()
# mpl.savefig('telko/pv/dni_january_week.pdf')
# # plot june week
# index = pd.date_range(start='6/2/2015', end='6/8/2015',
#                       freq='30Min', tz='UTC')
# dni.loc[index, :].plot()
# mpl.savefig('telko/pv/dni_june_week_incl_uncorrected_dni.pdf')
# dni[['dni_FRED', 'dni_pvlib']].loc[index, :].plot()
# mpl.savefig('telko/pv/dni_june_week.pdf')

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
module_4 = PVSystem(surface_tilt=14.57, surface_azimuth=215., albedo=0.2,
                    module='Aleo_Solar_S19U245_ulr', inverter=inv_sma,
                    module_parameters=CEC_modules['Aleo_Solar_S19U245_ulr'],
                    modules_per_string=13, strings_per_inverter=1,
                    inverter_parameters=CEC_inverters[inv_sma],
                    name='HTW_module_4')
module_4.module_parameters['EgRef'] = 1.121
module_4.module_parameters['dEgdT'] = -0.0002677
module_4.module_parameters['alpha_sc'] = 0.03
# module 5 - Schott aSi 105W / SMA SB 3000HF-30
#
# ############################################################################
# # setup location
# ############################################################################

location = Location(latitude=52.456032, longitude=13.525282,
                    tz='Etc/GMT-1', altitude=60, name='HTW Berlin')

##############################################################################
# call modelchain with FRED data
##############################################################################

# MODULE 3
mc = ModelChain(system=module_3, location=location,
                aoi_model='no_loss', spectral_model='no_loss')
pvlib_data = fred_weather_data.copy()
pvlib_data['dni'] = pvlib_data['dni_2']
mc.run_model(pvlib_data.index, weather=pvlib_data)

# calculate monthly correlation
feedin_3 = mc.dc.p_mp.to_frame().join(htw_wr3_data['P_DC'].to_frame())
feedin_3.rename(columns={'p_mp': 'energy_calculated',
                         'P_DC': 'energy_measured'},
                inplace=True)
# corr_feedin_3 = feedin_3.resample('1M').agg(
#     {'corr' : lambda x: x[feedin_3.columns[0]].corr(
#         x[feedin_3.columns[1]])})
# corr_feedin_3 = corr_feedin_3[corr_feedin_3.columns[0]]
# # plot correlation
# corr_feedin_3.plot()
# mpl.savefig('telko/pv/feedin_wr3_correlation_monthly.pdf')
# # plot january week
# index = pd.date_range(start='1/18/2015', end='1/24/2015',
#                       freq='30Min', tz='UTC')
# feedin_3.loc[index, :].plot()
# mpl.savefig('telko/pv/feedin_wr3_january_week.pdf')
# # plot june week
# index = pd.date_range(start='6/2/2015', end='6/8/2015',
#                       freq='30Min', tz='UTC')
# feedin_3.loc[index, :].plot()
# mpl.savefig('telko/pv/feedin_wr3_june_week.pdf')
#
# # compare monthly energy
# monthly_energy_feedin_3 = feedin_3.resample('1M').sum()
# monthly_energy_feedin_3.plot()
# mpl.savefig('telko/pv/feedin_wr3_energy.pdf')

# MODULE 4
mc = ModelChain(system=module_4, location=location,
                aoi_model='no_loss', spectral_model='no_loss')
pvlib_data = fred_weather_data.copy()
pvlib_data['dni'] = pvlib_data['dni_2']
mc.run_model(pvlib_data.index, weather=pvlib_data)

# calculate monthly correlation
feedin_4 = mc.dc.p_mp.to_frame().join(htw_wr4_data['P_DC'].to_frame())
feedin_4.rename(columns={'p_mp': 'energy_calculated',
                         'P_DC': 'energy_measured'},
                inplace=True)
# corr_feedin_4 = feedin_4.resample('1M').agg(
#     {'corr' : lambda x: x[feedin_4.columns[0]].corr(
#         x[feedin_4.columns[1]])})
# corr_feedin_4 = corr_feedin_4[corr_feedin_4.columns[0]]
# # plot correlation
# corr_feedin_4.plot()
# mpl.savefig('telko/pv/feedin_wr4_correlation_monthly.pdf')
# # plot january week
# index = pd.date_range(start='1/18/2015', end='1/24/2015',
#                       freq='30Min', tz='UTC')
# feedin_4.loc[index, :].plot()
# mpl.savefig('telko/pv/feedin_wr4_january_week.pdf')
# # plot june week
# index = pd.date_range(start='6/2/2015', end='6/8/2015',
#                       freq='30Min', tz='UTC')
# feedin_4.loc[index, :].plot()
# mpl.savefig('telko/pv/feedin_wr4_june_week.pdf')
#
# # compare monthly energy
# monthly_energy_feedin_3 = feedin_4.resample('1M').sum()
# monthly_energy_feedin_3.plot()
# mpl.savefig('telko/pv/feedin_wr4_energy.pdf')

##############################################################################
# call modelchain with HTW data
##############################################################################

# # pvlib's ModelChain
# mc = ModelChain(system=module_3, location=location,
#                 aoi_model='no_loss', spectral_model='no_loss')
# pvlib_data = fred_weather_data.copy()
# pvlib_data['dni'] = pvlib_data['dni_2']
# pvlib_data['ghi'] = htw_weather_data['ghi']
# pvlib_data['dhi'] = pvlib_data['ghi'] - pvlib_data['dirhi']
# mc.run_model(pvlib_data.index, weather=pvlib_data)
#
# # calculate monthly correlation
# feedin_3 = mc.dc.p_mp.to_frame().join(htw_wr3_data['P_DC'].to_frame())
# feedin_3.rename(columns={'p_mp': 'energy_calculated',
#                          'P_DC': 'energy_measured'},
#                 inplace=True)
# corr_feedin_3 = feedin_3.resample('1M').agg(
#     {'corr' : lambda x: x[feedin_3.columns[0]].corr(
#         x[feedin_3.columns[1]])})
# corr_feedin_3 = corr_feedin_3[corr_feedin_3.columns[0]]
# # plot correlation
# corr_feedin_3.plot()
# mpl.savefig('telko/pv/feedin_wr3_correlation_monthly_htw.pdf')
# # plot january week
# index = pd.date_range(start='1/18/2015', end='1/24/2015',
#                       freq='30Min', tz='UTC')
# feedin_3.loc[index, :].plot()
# mpl.savefig('telko/pv/feedin_wr3_january_week_htw.pdf')
# # plot june week
# index = pd.date_range(start='6/2/2015', end='6/8/2015',
#                       freq='30Min', tz='UTC')
# feedin_3.loc[index, :].plot()
# mpl.savefig('telko/pv/feedin_wr3_june_week_htw.pdf')
#
# # compare monthly energy
# monthly_energy_feedin_3 = feedin_3.resample('1M').sum()