import pandas as pd
import matplotlib.pyplot as mpl

##############################################################################
# read correlation data - energy
##############################################################################

# file_directory = 'telko/wind/SH/'
# correlations_hourly = pd.read_csv(file_directory + 'correlations_hourly.csv',
#                                   header=[0], index_col=[0], parse_dates=True)
#
# # wind_farms = ['wf_1', 'wf_2', 'wf_3', 'wf_4', 'wf_5', 'Sum']
# # for i in wind_farms:
# #     # get columns
# #     cols = [j for j in correlations_hourly.columns if i in j]
# #     # plot correlation
# #     correlations_hourly[cols].plot(figsize=(15, 10))
# #     mpl.savefig('telko/wind/SH/correlations_hourly_{}.pdf'.format(i))
#
# weather_data_source = ['open_FRED', 'MERRA']
# for i in weather_data_source:
#     # get columns
#     cols = [j for j in correlations_hourly.columns if i in j]
#     # plot correlation
#     correlations_hourly[cols].plot(figsize=(15, 10))
#     mpl.savefig('telko/wind/SH/correlations_energy_{}.pdf'.format(i))

##############################################################################
# read correlation data - power
##############################################################################

file_directory = 'telko/wind/SH/'
correlations_hourly = pd.read_csv(file_directory + 'correlations_power.csv',
                                  header=[0], index_col=[0], parse_dates=True)

correlations_hourly = correlations_hourly.loc[
    correlations_hourly[correlations_hourly.columns[0]].isnull() == False]

weather_data_source = ['open_FRED', 'MERRA']
for i in weather_data_source:
    # get columns
    cols = [j for j in correlations_hourly.columns if i in j]
    # plot correlation
    correlations_hourly[cols].plot(figsize=(15, 10))
    mpl.savefig('telko/wind/SH/correlations_power_{}.pdf'.format(i))