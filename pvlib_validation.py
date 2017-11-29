import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
import xarray

data = xarray.open_dataset('ASWDIFU_S/oF_00625_MERRA2.ASWDIFU_S.2002_02.DEplus.nc')
#a = data.where(data.lat<46.0) #sel(rlat=[0], rlon=[0], time=[12])
b = data.sel(rlat=[-4.5, -4.4], method='nearest')
# = data.to_dataframe()

# # preparing the weather data to suit pvlib's needs
# # different name for the wind speed
# my_weather.data.rename(columns={'v_wind': 'wind_speed'}, inplace=True)
# # temperature in degree Celsius instead of Kelvin
# my_weather.data['temp_air'] = my_weather.data.temp_air - 273.15
# # calculate ghi
# my_weather.data['ghi'] = my_weather.data.dirhi + my_weather.data.dhi
# w = my_weather.data
#
# # time index from weather data set
# times = my_weather.data.index

####################################################################################################
# setup modules
####################################################################################################

# # get module and inverter parameters
# sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
# CEC_modules = pvlib.pvsystem.retrieve_sam('CECMod')
# CEC_inverters = pvlib.pvsystem.retrieve_sam('sandiainverter')
#
# inv_sma = 'SMA_Solar_Technology_AG__SB3000HFUS_30___240V_240V__CEC_2011_'
# inv_danfoss = 'Danfoss_Solar__DLX_2_9_UL__240V__240V__CEC_2013_'
#
# # module 1 - Schott aSi 105W / Danfoss DLX 2.9
# # module 2 - Aleo S19 285W / Danfoss DLX 2.9 'Aleo_Solar_S19H270' CEC
#
# # module 3 - Aleo S18 240W / Danfoss DLX 2.9
# module_3 = PVSystem(surface_tilt=14.57, surface_azimuth=215., albedo=0.2,
#                  module=CEC_modules['aleo_Solar_S18_240'],
#                  modules_per_string=14, strings_per_inverter=1,
#                  inverter=CEC_inverters[inv_danfoss],
#                  name='HTW_module_3')
#
# # module 4 - Aleo S19 245W / SMA SB 3000HF-30 'Aleo_Solar_S19U245_ulr' CEC
# # module 5 - Schott aSi 105W / SMA SB 3000HF-30
#
# ####################################################################################################
# # setup location
# ####################################################################################################
#
# location = Location(latitude=52.456032, longitude=13.525282,
#                     tz='Europe/Berlin', altitude=60, name='HTW Berlin')

####################################################################################################
# call modelchain
####################################################################################################

# mc = ModelChain(PVSystem(**yingli210),
#                 Location(**wittenberg),
#                 orientation_strategy='south_at_latitude_tilt')
#
# mc.run_model(times, weather=w)
#
# if plt:
#     mc.dc.p_mp.fillna(0).plot()
#     plt.show()
# else:
#     logging.warning("No plots shown. Install matplotlib to see the plots.")
#
# logging.info('Done!')