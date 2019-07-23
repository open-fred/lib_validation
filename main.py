# Imports from Windpowerlib
from windpowerlib import wind_farm as wf

# Imports from lib_validation
# import visualization_tools
import tools
# import latex_tables
import modelchain_usage
from wind_farm_specifications import (get_joined_wind_farm_data,
                                      get_wind_farm_data)
# from merra_weather_data import get_merra_data
from open_fred_weather_data import get_open_fred_data
# from argenetz_data import get_argenetz_data
# from enertrag_data import get_enertrag_data, get_enertrag_curtailment_data
# from analysis_tools import ValidationObject
from greenwind_data import (get_greenwind_data, get_highest_wind_speeds,
                            get_first_row_turbine_time_series)
from config_simulation_cases import get_configuration
# import plots_single_functionalities
# from create_wind_efficiency_curves import get_power_efficiency_curves
import validation_tools as val_tools


# Other imports
import os
import pandas as pd
import numpy as np
import pickle
import logging

logging.getLogger().setLevel(logging.INFO)

# ----------------------------- Set parameters ------------------------------ #
cases = [
    # ---- Single functions - wind speed ---- # (only open_FRED)
    'wind_speed_1',
    # 'wind_speed_2',
    # 'wind_speed_3',
    # 'wind_speed_4',
    # 'wind_speed_5',  # first row like weather_wind_speed_3
    # 'wind_speed_6',  # first row like weather_wind_speed_3
    # 'wind_speed_7',  # first row like weather_wind_speed_3
    # 'wind_speed_8',  # first row like weather_wind_speed_3
    # ---- Single functions - wind speed ---- # (only open_FRED)
    'power_output_1',
    # ---- Single functions - smoothing, density... ---- #
    # 'smoothing_1',
    # 'smoothing_2',
    # ---- Single functions - Wake losses ---- #
    # 'wake_losses_3',
    # ---- Single Turbine Model ---- '
    'single_turbine_1',
    # ---- Wind Farm Model ---- '
    # 'wind_farm_final',
    # ---- weather data ---- #
    # 'weather_wind_speed_1',
    # 'weather_wind_farm'
]

temporal_resolution = 'H'  # not fully implemented yet - only use 'H'

min_periods_pearson = None  # Minimum amount of periods for correlation.

# Pickle load time series data frame - if one of the below pickle_load options
# is set to False, `pickle_load_time_series_df` is automatically set to False
pickle_load_time_series_df = False

# pickle_load_merra = False
pickle_load_open_fred = True
pickle_load_era5 = False
# pickle_load_arge = True
# pickle_load_enertrag = True
pickle_load_greenwind = True
pickle_load_wind_farm_data = True
pickle_load_wind_efficiency_curves = False

csv_load_time_series_df = False  # Load time series data frame from csv dump
if pickle_load_time_series_df:
    csv_dump_time_series_df = False
else:
    csv_dump_time_series_df = True  # Dump df as csv

plot_single_func = True

feedin_comparsion_all_in_one = True  # Plots all calculated series for one
                                     # wind farm in one plot (multiple)

# Select time of day you want to observe or None for all day
time_period = (
#       6, 22  # time of day to be selected (from h to h)
         None   # complete time series will be observed
        )

# Relative path to latex tables folder
latex_tables_folder = ('../../../User-Shares/Masterarbeit/Latex/Tables/' +
                       'automatic/')

# Other plots
# plot_arge_feedin = False  # If True plots each column of ArgeNetz data frame

# Folder specifications
validation_pickle_folder = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'dumps/validation_data'))
wind_farm_pickle_folder = os.path.join(os.path.dirname(__file__),
                                       'dumps/wind_farm_data')

time_series_dump_folder = os.path.join(
    os.path.dirname(__file__),
    'dumps/time_series_dfs')

validation_folder = os.path.join(
    os.path.dirname(__file__),
    'validation')

# csv_folder = '../../../User-Shares/Masterarbeit/Latex/csv_for_plots'

# Heights for which temperature of MERRA shall be calculated
# temperature_heights = [60, 64, 65, 105, 114]

# Threshold factor. F.e. if threshold_factor is 0.5 resampling is only done, if
# more than 50 percent of the values are not nan.
threshold_factor = 0.5

# If pickle_load options not all True:
if (
        # not pickle_load_merra or
        not pickle_load_open_fred or not
        # pickle_load_arge or not pickle_load_enertrag or not
        pickle_load_greenwind or not pickle_load_wind_farm_data):
    pickle_load_time_series_df = False


def run_main(case, parameters, year):
    logging.info("--- Simulation with case {0} in year {1} starts ---".format(
        case, year))

    # Start and end date for time period to be plotted when 'feedin_comparison'
    # is selected. (not for monthly output).
    # start_end_list = [
    #     (None, None),  # for whole year
    #     ('{0}-05-07'.format(year), '{0}-05-08'.format(year)),
    #     ('{0}-05-06'.format(year), '{0}-05-08'.format(year))
    #     ]

    # Set parameters
    restriction_list = parameters['restriction_list']
    validation_data_list = parameters['validation_data_list']
    weather_data_list = parameters['weather_data_list']
    approach_list = parameters['approach_list']
    output_methods = parameters['output_methods']
    visualization_methods = parameters['visualization_methods']
    latex_output = parameters['latex_output']
    key_figures_print = parameters['key_figures_print']
    replacement = parameters['replacement']

    # -------------------------------- Warning ------------------------------ #
    # if (year == 2015 and validation_data_list[0] == 'Enertrag' and
    #         validation_data_list[-1] == 'Enertrag'):
    #     raise ValueError("Enertrag data not available for 2015 - select " +
    #                      "other validation data or year 2016")

    # ------------------------ Validation Feedin Data ----------------------- #
    def get_threshold(out_frequency, original_resolution):
        if (out_frequency == 'H' or out_frequency == '60T'):
            resolution = 60
        elif out_frequency == 'M':
            resolution = 31 * 24 * 60
        else:
            resolution = out_frequency.n
        if original_resolution == 1:
            original_resolution = 60
        return resolution / original_resolution * threshold_factor

    def get_validation_data(frequency):
        r"""
        Writes all measured power output time series into one DataFrame.

        All time series are resampled to the given frequency.

        Parameters
        ----------
        frequency : string
            Frequency for resampling. Examples: 'H' for hourly, '30T' for half-
            hourly, 'M' for monthly.

        Returns
        -------
        validation_df : pd.DataFrame
            Measured power output in MW. Column names are as follows:
            'wf_SH_measured', 'wf_BS_measured', etc. OR 'single_BS_measured'

        """
        validation_df_list = []
        # if 'ArgeNetz' in validation_data_list:
        #     # Get ArgeNetz Data
        #     arge_data = get_argenetz_data(
        #         year, pickle_load=pickle_load_arge,
        #         filename=os.path.join(validation_pickle_folder,
        #                               'arge_netz_data_{0}.p'.format(year)),
        #         csv_dump=False, plot=plot_arge_feedin)
        #     # Select only column containing the power output of wf_2 and rename
        #     arge_data = arge_data[[
        #         'wf_2_power_output']].rename(
        #         columns={'wf_2_power_output': 'wf_SH_measured'})
        #     # Set negative values to nan (for Enertrag and GreenWind this
        #     # happens in the separate modules)
        #     arge_data = tools.negative_values_to_nan(arge_data)
        #     # Resample the DataFrame columns with `frequency` and `threshold`
        #     # and add to list
        #     threshold = get_threshold(frequency, arge_data.index.freq.n)
        #     validation_df_list.append(tools.resample_with_nan_theshold(
        #         df=arge_data, frequency=frequency, threshold=threshold))
        # if ('Enertrag' in validation_data_list and year == 2016):
        #     # Get Enertrag Data
        #     enertrag_data = get_enertrag_data(
        #         pickle_load=pickle_load_enertrag,
        #         filename=os.path.join(validation_pickle_folder,
        #                               'enertrag_data_2016.p'))
        #     # Select aggregated power output of wind farm (rename)
        #     enertrag_data = enertrag_data[['wf_BNE_power_output']].rename(
        #         columns={'wf_BNE_power_output': 'wf_BNE_measured'})
        #     # Resample the DataFrame columns with `frequency` and add to list
        #     threshold = get_threshold(frequency, enertrag_data.index.freq.n)
        #     validation_df_list.append(tools.resample_with_nan_theshold(
        #         df=enertrag_data, frequency=frequency, threshold=threshold))
        if 'GreenWind' in validation_data_list:
            # Get wind farm data
            wind_farm_data_gw = get_wind_farm_data(
                'farm_specification_greenwind_{0}.p'.format(year),
                wind_farm_pickle_folder, pickle_load_wind_farm_data)
            # Get Greenwind data
            greenwind_data = get_greenwind_data(
                year, pickle_load=pickle_load_greenwind, resample=False,
                filename=os.path.join(validation_pickle_folder,
                                      'greenwind_data_{0}.p'.format(year)),
                filter_errors=True)
            # Select aggregated power output of wind farm (rename)
            greenwind_data = greenwind_data[[
                '{0}_power_output'.format(data['name']) for
                data in wind_farm_data_gw]].rename(
                columns={col: col.replace('power_output', 'measured') for
                         col in greenwind_data.columns})
            # Resample the DataFrame columns with `frequency` and add to list
            threshold = get_threshold(frequency, greenwind_data.index.freq.n)
            validation_df_list.append(tools.resample_with_nan_theshold(
                df=greenwind_data, frequency=frequency, threshold=threshold))
        if 'single' in validation_data_list:
            # if case == 'highest_wind_speed':
            #     filename_green_wind = os.path.join(
            #         os.path.dirname(__file__), validation_pickle_folder,
            #         'greenwind_data_{0}.p'.format(year))
            #     # Get highest wind speed (measured at wind turbines) and rename
            #     single_data = get_highest_wind_speeds(
            #         year, filename_green_wind,
            #         pickle_load=pickle_load_greenwind,
            #         filename=os.path.join(
            #             os.path.dirname(__file__), validation_pickle_folder,
            #             'green_wind_highest_wind_speed_{}.p'.format(year)))
            #     single_data.rename(
            #             columns={column: column.replace(
            #                 'highest_wind_speed', 'measured').replace(
            #                     'wf', 'single') for
            #                 column in list(single_data)}, inplace=True)
            # else:
            if case in ['weather_wind_speed_3', 'wind_speed_5',
                        'wind_speed_6', 'wind_speed_7', 'wind_speed_8']:
                filename = os.path.join(
                    os.path.dirname(__file__), validation_pickle_folder,
                    'greenwind_data_first_row_{0}_weather_wind_speed_3.p'.format(year))
            else:
                filename = os.path.join(
                    os.path.dirname(__file__), validation_pickle_folder,
                    'greenwind_data_first_row_{0}.p'.format(year))
            single_data = get_first_row_turbine_time_series(
                year=year, filter_errors=True, print_error_amount=False,
                pickle_filename=filename, pickle_load_raw_data=True,
                pickle_load=pickle_load_greenwind,
                filename_raw_data=os.path.join(
                    validation_pickle_folder,
                    'greenwind_data_{0}.p'.format(year)),
                case=case)
            if 'wind_speed' in case:
                # Get first row single turbine wind speed and rename
                # columns
                single_data = single_data[[col for
                                           col in list(single_data) if
                                           'wind_speed' in col]].rename(
                    columns={column: column.replace(
                        'wind_speed', 'measured').replace(
                        'wf', 'single') for column in list(single_data)})
            else:
                single_data = single_data[[col for
                                           col in list(single_data) if
                                           'power_output' in col]].rename(
                    columns={column: column.replace(
                        'power_output', 'measured').replace(
                        'wf', 'single') for column in list(single_data)})
            # Resample the DataFrame columns with `frequency` and add to list
            threshold = get_threshold(frequency, single_data.index.freq.n)
            validation_df_list.append(tools.resample_with_nan_theshold(
                df=single_data, frequency=frequency, threshold=threshold))
        if 'gw_wind_speeds' in validation_data_list:
            # Get Greenwind data
            greenwind_data = get_greenwind_data(
                year, pickle_load=pickle_load_greenwind, resample=False,
                filename=os.path.join(
                    os.path.dirname(__file__),
                    'dumps/validation_data',
                    'greenwind_data_{0}_raw_resolution.p'.format(year)),
                filter_errors=True)
            # Select only power output columns and drop wind farm power output
            turbine_power_output = greenwind_data[[
                column_name for column_name in list(greenwind_data) if
                'power_output' in column_name]].drop(
                ['wf_{}_power_output'.format(wf) for
                 wf in ['BE', 'BS', 'BNW']], axis=1)
            turbine_power_output.rename(columns={
                old_col: old_col.replace('wf_', '').replace(
                    'power_output', 'measured') for
                old_col in list(turbine_power_output)}, inplace=True)
            # Resample the DataFrame colu'mns with `frequency` and add to list
            threshold = get_threshold(frequency,
                                      turbine_power_output.index.freq.n)
            validation_df_list.append(tools.resample_with_nan_theshold(
                df=turbine_power_output, frequency=frequency,
                threshold=threshold))
        # Join DataFrames - power output in MW - wind speed in m/s
        if 'wind_speed' in case:
            validation_df = pd.concat(validation_df_list, axis=1)
            col_name = 'wind_speed_val'
        else:
            validation_df = pd.concat(validation_df_list, axis=1) / 1000
            col_name = 'feedin_val'

        # Validation df in db format for new validation tools
        validation_df_db_format = pd.DataFrame()
        for col in validation_df.keys():
            df = pd.DataFrame(validation_df[col]).rename(columns={
                col: col_name})
            df['turbine_or_farm'] = col.replace('_measured', '')
            validation_df_db_format = pd.concat([validation_df_db_format, df])

        # validation_df_db_format = pd.concat(
        #     [pd.DataFrame([validation_df[name].values,
        #                    [name for i in range(len(validation_df))],
        #                    validation_df.index]).transpose().set_index(
        #         2).rename(columns={0: 'feedin_val', 1: 'turbine_or_farm'}) for
        #      name in validation_df.keys()])
        return validation_df, validation_df_db_format

    # ---------------------------- Wind farm data --------------------------- #
    def return_wind_farm_data(single=False, gw_wind_speeds=False,
                              sh_wind_speeds=False):
        r"""
        Get wind farm data of all validation data.

        single : Boolean
            If True the single turbine data is fetched.

        Returns
        -------
        List of Dictionaries
            Dictionaries contain information about the wind farm.

        """
        if single:
            filenames = ['farm_specification_greenwind_{0}.p'.format(year)]
            wind_farm_data = get_joined_wind_farm_data(
                filenames, wind_farm_pickle_folder,
                pickle_load_wind_farm_data)
            for item in wind_farm_data:
                item['wind_turbine_fleet'][0]['number_of_turbines'] = 1
                item['name'] = 'single_{}'.format(
                    item['name'].split('_')[1])
        elif gw_wind_speeds:
            filenames = ['turbine_specification_greenwind_{0}.p'.format(year)]
            wind_farm_data = get_joined_wind_farm_data(
                filenames, wind_farm_pickle_folder, pickle_load_wind_farm_data)
        elif sh_wind_speeds:
            filenames = ['turbine_specification_argenetz_{0}.p'.format(year)]
            wind_farm_data = get_joined_wind_farm_data(
                filenames, wind_farm_pickle_folder, pickle_load_wind_farm_data)
        else:
            filenames = ['farm_specification_{0}_{1}.p'.format(
                validation_data_name.replace('ArgeNetz',
                                             'argenetz').replace(
                    'GreenWind', 'greenwind'), year)
                for validation_data_name in validation_data_list if
                validation_data_name is not 'Enertrag']
            if (year == 2016 and 'Enertrag' in validation_data_list):
                filenames += ['farm_specification_enertrag_2016.p']
            wind_farm_data = get_joined_wind_farm_data(
                filenames, wind_farm_pickle_folder,
                pickle_load_wind_farm_data)
        return wind_farm_data

    # ----------------------- Power output simulation ----------------------- #
    def get_calculated_data(weather_data_name, wind_farm_data_list):
        r"""
        Calculates time series with different approaches.

        Data is saved in a DataFrame that can later be joined with the
        validation data frame.

        Parameters
        ----------
        weather_data_name : String
            Weather data for which the feed-in is calculated.
        wind_farm_data_list : List

        Returns
        -------
        calculation_df : pd.DataFrame
            Calculated power output in MW. Column names are as follows:
            'wf_1_calculated_{0}'.format(approach) etc.

        """
        # Get weather data
        # Generate weather filename (including path) for pickle dumps (loads)
        filename_weather = os.path.join(
            os.path.dirname(__file__), 'dumps/weather',
            'weather_df_{0}_{1}.p'.format(weather_data_name, year))
        # Read csv files that contains weather data (pd.DataFrame is dumped)
        # to save time below
        # if weather_data_name == 'MERRA':
        #     if not pickle_load_merra:
        #         get_merra_data(year, heights=temperature_heights,
        #                        filename=filename_weather)
        if weather_data_name == 'open_FRED':
            if not pickle_load_open_fred:
                fred_path = '~/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_{0}_sh.csv'.format(year) # todo adapt
                get_open_fred_data(
                    filename=fred_path, pickle_filename=filename_weather,
                    pickle_load=False)
        if weather_data_name == 'ERA5':
            if not pickle_load_era5:
                era5_path = '~/virtualenvs/lib_validation/lib_validation/dumps/weather/era5_wind_bb_{}.csv'.format(year)
                get_open_fred_data(
                    filename=era5_path, pickle_filename=filename_weather,
                    pickle_load=False)
        # Initialise calculation_df_list and calculate power output
        calculation_df_list = []
        # Initialise calculation_df_db_format for new validation tools format
        calculation_df_db_format = pd.DataFrame()
        # Initialise wind farms
        wind_farm_list = [wf.WindFarm(**wind_farm_data) for
                          wind_farm_data in wind_farm_data_list]
        for wind_farm in wind_farm_list:
            # Get weather data for specific coordinates
            weather = tools.get_weather_data(
                weather_data_name, wind_farm.coordinates, pickle_load=True,
                filename=filename_weather, year=year,
                # temperature_heights=temperature_heights
            )
            # Resample weather data
            weather = weather.resample(temporal_resolution).mean()
            # if ('wake_losses' in case or 'wind_farm' in case):
            #     # highest_power_output = False
            #     # file_add_on = ''
            #     # Get wind efficiency curves - they are assigned to wind farms
            #     # below in calculations
            #     wind_eff_curves = get_power_efficiency_curves(
            #         drop_higher_one=True,
            #         pickle_load=False,
            #         filename=os.path.join(os.path.dirname(__file__), 'dumps',
            #                               'wind_efficiency_curves.p'))

            # Calculate power output and store in list for approaches in
            # approach_list

            # --- wind speed calculations --- #
            # if 'logarithmic' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.wind_speed_to_hub_height(
            #             wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #             weather_df=weather, wind_speed_model='logarithmic',
            #             obstacle_height=0).to_frame(
            #             name='{0}_calculated_logarithmic'.format(
            #                 wind_farm.name)))
            if 'log_100' in approach_list:
                calculated_value = modelchain_usage.wind_speed_to_hub_height(
                    wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                    weather_df=weather, wind_speed_model='logarithmic',
                    obstacle_height=0)
                calculation_df_list.append(calculated_value.to_frame(
                        name='{0}_calculated_log_100'.format(wind_farm.name)))
                df = calculated_value.to_frame(name='wind_speed')
                df['turbine_or_farm'] = wind_farm.name
                df['approach'] = 'log_100'
                calculation_df_db_format = pd.concat(
                    [calculation_df_db_format, df], axis=0)
            if 'log_80' in approach_list:
                modified_weather = weather[['roughness_length', 'wind_speed']]
                modified_weather.drop([100, 120, 10], axis=1, level=1,
                                      inplace=True)
                calculated_value = modelchain_usage.wind_speed_to_hub_height(
                        wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                        weather_df=modified_weather,
                        wind_speed_model='logarithmic',
                        obstacle_height=0)
                calculation_df_list.append(calculated_value.to_frame(
                        name='{0}_calculated_log_80'.format(
                            wind_farm.name)))
                df = calculated_value.to_frame(name='wind_speed')
                df['turbine_or_farm'] = wind_farm.name
                df['approach'] = 'log_80'
                calculation_df_db_format = pd.concat(
                    [calculation_df_db_format, df], axis=0)
            if 'log_10' in approach_list:
                modified_weather = weather[['roughness_length', 'wind_speed']]
                modified_weather.drop([100, 120, 80], axis=1, level=1,
                                      inplace=True)
                calculated_value = modelchain_usage.wind_speed_to_hub_height(
                        wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                        weather_df=modified_weather,
                        wind_speed_model='logarithmic',
                        obstacle_height=0)
                calculation_df_list.append(calculated_value.to_frame(
                        name='{0}_calculated_log_10'.format(
                            wind_farm.name)))
                df = calculated_value.to_frame(name='wind_speed')
                df['turbine_or_farm'] = wind_farm.name
                df['approach'] = 'log_10'
                calculation_df_db_format = pd.concat(
                    [calculation_df_db_format, df], axis=0)
            # if 'hellman' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.wind_speed_to_hub_height(
            #             wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #             weather_df=weather, wind_speed_model='hellman',
            #             hellman_exp=None).to_frame(
            #             name='{0}_calculated_hellman'.format(
            #                 wind_farm.name)))
            # if 'hellman_100' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.wind_speed_to_hub_height(
            #             wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #             weather_df=weather, wind_speed_model='hellman',
            #             hellman_exp=None).to_frame(
            #             name='{0}_calculated_hellman_100'.format(
            #                 wind_farm.name)))
            # if 'hellman_80' in approach_list:
            #     modified_weather = weather[['roughness_length', 'wind_speed']]
            #     modified_weather.drop([100, 120, 10], axis=1, level=1,
            #                           inplace=True)
            #     calculation_df_list.append(
            #         modelchain_usage.wind_speed_to_hub_height(
            #             wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #             weather_df=modified_weather,
            #             wind_speed_model='hellman',
            #             hellman_exp=None).to_frame(
            #             name='{0}_calculated_hellman_80'.format(
            #                 wind_farm.name)))
            # if 'hellman_10' in approach_list:
            #     modified_weather = weather[['roughness_length', 'wind_speed']]
            #     modified_weather.drop([100, 120, 80], axis=1, level=1,
            #                           inplace=True)
            #     calculation_df_list.append(
            #         modelchain_usage.wind_speed_to_hub_height(
            #             wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #             weather_df=modified_weather,
            #             wind_speed_model='hellman',
            #             hellman_exp=None).to_frame(
            #             name='{0}_calculated_hellman_10'.format(
            #                 wind_farm.name)))
            # if 'hellman_2' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.wind_speed_to_hub_height(
            #             wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #             weather_df=weather, wind_speed_model='hellman',
            #             hellman_exp=1 / 7).to_frame(
            #             name='{0}_calculated_hellman_2'.format(
            #                 wind_farm.name)))
            # if 'hellman2_100' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.wind_speed_to_hub_height(
            #             wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #             weather_df=weather, wind_speed_model='hellman',
            #             hellman_exp=1 / 7).to_frame(
            #             name='{0}_calculated_hellman2_100'.format(
            #                 wind_farm.name)))
            # if 'hellman2_80' in approach_list:
            #     modified_weather = weather[['roughness_length', 'wind_speed']]
            #     modified_weather.drop([100, 120, 10], axis=1, level=1,
            #                           inplace=True)
            #     calculation_df_list.append(
            #         modelchain_usage.wind_speed_to_hub_height(
            #             wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #             weather_df=modified_weather,
            #             wind_speed_model='hellman',
            #             hellman_exp=1 / 7).to_frame(
            #             name='{0}_calculated_hellman2_80'.format(
            #                 wind_farm.name)))
            # if 'hellman2_10' in approach_list:
            #     modified_weather = weather[['roughness_length', 'wind_speed']]
            #     modified_weather.drop([100, 120, 80], axis=1, level=1,
            #                           inplace=True)
            #     calculation_df_list.append(
            #         modelchain_usage.wind_speed_to_hub_height(
            #             wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #             weather_df=modified_weather,
            #             wind_speed_model='hellman',
            #             hellman_exp=1 / 7).to_frame(
            #             name='{0}_calculated_hellman2_10'.format(
            #                 wind_farm.name)))
            # if 'lin._interp.' in approach_list:
            #     if len(list(weather['wind_speed'])) > 1:
            #         calculation_df_list.append(
            #             modelchain_usage.wind_speed_to_hub_height(
            #                 wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #                 wind_speed_model='interpolation_extrapolation',
            #                 weather_df=weather).to_frame(
            #                 name='{0}_calculated_lin._interp.'.format(
            #                     wind_farm.name)))
            # if 'log._interp.' in approach_list:
            #     if len(list(weather['wind_speed'])) > 1:
            #         calculation_df_list.append(
            #             modelchain_usage.wind_speed_to_hub_height(
            #                 wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #                 wind_speed_model='log_interpolation_extrapolation',
            #                 weather_df=weather).to_frame(
            #                 name='{0}_calculated_log._interp.'.format(
            #                     wind_farm.name)))

            # --- wind speed definition for next cases --- #
            if (case == 'wind_farm_3' or case == 'weather_single_turbine_2' or
                    case == 'wake_losses_1'):
                # Use wind speed from first row GreenWind data as weather data
                single_data_raw = get_first_row_turbine_time_series(
                    year=year, filter_errors=True, print_error_amount=False,
                    pickle_filename=os.path.join(
                        os.path.dirname(__file__), 'dumps/validation_data',
                        'greenwind_data_first_row_{0}.p'.format(year)),
                    pickle_load=pickle_load_greenwind, case=case)
                wind_speed = single_data_raw[['wf_{}_wind_speed'.format(
                    wind_farm.name.split('_')[1])]]
            elif case == 'power_output_1':
                # Get Greenwind data and get wind speed from each turbine
                greenwind_data = get_greenwind_data(
                    year, pickle_load=pickle_load_greenwind, resample=False,
                    filename=os.path.join(
                        os.path.dirname(__file__),
                        'dumps/validation_data',
                        'greenwind_data_{0}_raw_resolution.p'.format(year)),
                    filter_errors=True)
                # Select wind speed column of specific turbine
                wind_speed = greenwind_data[['wf_{}_wind_speed'.format(
                    wind_farm.name)]]
            else:
                wind_speed = None
            if wind_speed is not None:
                # Resample wind speed time series if it does not have the same
                # temporal resolution as the weather data time series
                wind_speed = (
                    wind_speed if
                    wind_speed.index.freq == weather.index.freq else
                    tools.resample_with_nan_theshold(
                        df=wind_speed, frequency=weather.index.freq,
                        threshold=get_threshold(
                            out_frequency=weather.index.freq,
                            original_resolution=wind_speed.index.freq.n)))
            if 'p-curve' in approach_list:
                calculated_value = modelchain_usage.power_output_simple(
                        wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                        weather_df=weather, wind_speed=wind_speed,
                        wind_speed_model='logarithmic',
                        density_model='ideal_gas',
                        temperature_model='linear_gradient',
                        power_output_model='power_curve',
                        density_correction=False, obstacle_height=0,
                        hellman_exp=None)
                calculation_df_list.append(
                    calculated_value.to_frame(
                        name='{0}_calculated_p-curve'.format(
                            wind_farm.name)))
                df = calculated_value.to_frame(name='feedin')
                df['turbine_or_farm'] = wind_farm.name
                df['approach'] = 'p-curve'
                calculation_df_db_format = pd.concat(
                    [calculation_df_db_format, df], axis=0)
            # if 'cp-curve' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_simple(
            #             wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #             weather_df=weather, wind_speed=wind_speed,
            #             wind_speed_model='logarithmic',
            #             density_model='ideal_gas',
            #             temperature_model='linear_gradient',
            #             power_output_model='power_coefficient_curve',
            #             density_correction=False,
            #             obstacle_height=0, hellman_exp=None).to_frame(
            #             name='{0}_calculated_cp-curve'.format(
            #                 wind_farm.name)))
            # if 'p-curve_(d._c.)' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_simple(
            #             wind_turbine_fleet=wind_farm.wind_turbine_fleet,
            #             weather_df=weather, wind_speed=wind_speed,
            #             wind_speed_model='logarithmic',
            #             density_model='ideal_gas',
            #             temperature_model='linear_gradient',
            #             power_output_model='power_curve',
            #             density_correction=True,
            #             obstacle_height=0, hellman_exp=None).to_frame(
            #             name='{0}_calculated_p-curve_(d._c.)'.format(
            #                 wind_farm.name)))
            #
            # # --- power output calculations wind farms --- #
            # if 'Turbine_TI' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model=None, smoothing=True,
            #             wind_speed=wind_speed,
            #             standard_deviation_method='turbulence_intensity',
            #             smoothing_order='turbine_power_curves',
            #             roughness_length=weather[
            #                 'roughness_length'][0].mean()).to_frame(
            #                 name='{0}_calculated_Turbine_TI'.format(
            #                     wind_farm.name)))
            # if 'Turbine_SP' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model=None, smoothing=True,
            #             wind_speed=wind_speed,
            #             standard_deviation_method='Staffell_Pfenninger',
            #             smoothing_order='turbine_power_curves').to_frame(
            #                 name='{0}_calculated_Turbine_SP'.format(
            #                     wind_farm.name)))
            # if 'Farm_TI' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model=None, smoothing=True,
            #             wind_speed=wind_speed,
            #             standard_deviation_method='turbulence_intensity',
            #             smoothing_order='wind_farm_power_curves',
            #             roughness_length=weather[
            #                 'roughness_length'][0].mean()).to_frame(
            #                 name='{0}_calculated_Farm_TI'.format(
            #                     wind_farm.name)))
            # if 'Farm_SP' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model=None, smoothing=True,
            #             wind_speed=wind_speed,
            #             standard_deviation_method='Staffell_Pfenninger',
            #             smoothing_order='wind_farm_power_curves').to_frame(
            #                 name='{0}_calculated_Farm_SP'.format(
            #                     wind_farm.name)))
            # if 'aggregation' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_simple(
            #             wind_farm.wind_turbine_fleet, weather,
            #             wind_speed=wind_speed).to_frame(
            #                 name='{0}_calculated_aggregation'.format(
            #                     wind_farm.name)))
            # if ('TI' in approach_list and case == 'smoothing_2'):
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model=None, smoothing=True,
            #             wind_speed=wind_speed,
            #             standard_deviation_method='turbulence_intensity',
            #             smoothing_order='wind_farm_power_curves',
            #             roughness_length=weather[
            #                 'roughness_length'][0].mean()).to_frame(
            #             name='{0}_calculated_TI'.format(
            #                 wind_farm.name)))
            # if ('SP' in approach_list and case == 'smoothing_2'):
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model=None, smoothing=True,
            #             wind_speed=wind_speed,
            #             standard_deviation_method='Staffell_Pfenninger',
            #             smoothing_order='wind_farm_power_curves').to_frame(
            #             name='{0}_calculated_SP'.format(
            #                 wind_farm.name)))
            # if 'Calculated' in approach_list:
            #     wind_farm.efficiency = wind_eff_curves[[wind_farm.name]]
            #     wind_farm.efficiency.reset_index(level=0, inplace=True)
            #     wind_farm.efficiency.rename(columns={
            #         'index': 'wind_speed',
            #         wind_farm.name: 'efficiency'}, inplace=True)
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, wind_speed=wind_speed,
            #             wake_losses_model='power_efficiency_curve',
            #             smoothing=False, density_correction=False).to_frame(
            #             name='{0}_calculated_Calculated'.format(
            #                 wind_farm.name)))
            # if 'Constant' in approach_list:
            #     wind_farm.efficiency = 0.8
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, wind_speed=wind_speed,
            #             wake_losses_model='constant_efficiency',
            #             smoothing=False, density_correction=False).to_frame(
            #             name='{0}_calculated_Constant'.format(
            #                 wind_farm.name)))
            # if 'Dena' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, wind_speed=wind_speed,
            #             wake_losses_model='dena_mean',
            #             smoothing=False, density_correction=False).to_frame(
            #             name='{0}_calculated_Dena'.format(
            #                 wind_farm.name)))
            # if 'Knorr_extreme2' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wind_speed=wind_speed,
            #             wake_losses_model='knorr_extreme2',
            #             smoothing=False).to_frame(
            #             name='{0}_calculated_Knorr_extreme2'.format(
            #                 wind_farm.name)))
            # if 'No_losses' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, wind_speed=wind_speed,
            #             wake_losses_model=None,
            #             smoothing=False, density_correction=False).to_frame(
            #             name='{0}_calculated_No_losses'.format(
            #                 wind_farm.name)))
            # if 'Dena-TI' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model='dena_mean',
            #             smoothing=True, wind_speed=wind_speed,
            #             standard_deviation_method='turbulence_intensity',
            #             smoothing_order='wind_farm_power_curves',
            #             roughness_length=weather[
            #                 'roughness_length'][0].mean()).to_frame(
            #             name='{0}_calculated_Dena-TI'.format(
            #                 wind_farm.name)))
            # if 'Dena-SP' in approach_list:
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model='dena_mean',
            #             smoothing=True, wind_speed=wind_speed,
            #             standard_deviation_method='Staffell_Pfenninger',
            #             smoothing_order='wind_farm_power_curves').to_frame(
            #             name='{0}_calculated_Dena-SP'.format(
            #                 wind_farm.name)))
            # if 'Const.-TI' in approach_list:
            #     wind_farm.efficiency = 0.8
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model='constant_efficiency',
            #             smoothing=True, wind_speed=wind_speed,
            #             standard_deviation_method='turbulence_intensity',
            #             smoothing_order='wind_farm_power_curves',
            #             roughness_length=weather[
            #                 'roughness_length'][0].mean()).to_frame(
            #             name='{0}_calculated_Const.-TI'.format(
            #                 wind_farm.name)))
            # if 'Const.-TI-70' in approach_list:
            #     wind_farm.efficiency = 0.7
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model='constant_efficiency',
            #             smoothing=True, wind_speed=wind_speed,
            #             standard_deviation_method='turbulence_intensity',
            #             smoothing_order='wind_farm_power_curves',
            #             roughness_length=weather[
            #                 'roughness_length'][0].mean()).to_frame(
            #             name='{0}_calculated_Const.-TI-70'.format(
            #                 wind_farm.name)))
            # if 'Const.-TI-60' in approach_list:
            #     wind_farm.efficiency = 0.6
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model='constant_efficiency',
            #             smoothing=True, wind_speed=wind_speed,
            #             standard_deviation_method='turbulence_intensity',
            #             smoothing_order='wind_farm_power_curves',
            #             roughness_length=weather[
            #                 'roughness_length'][0].mean()).to_frame(
            #             name='{0}_calculated_Const.-TI-60'.format(
            #                 wind_farm.name)))
            # if 'Const.-SP' in approach_list:
            #     wind_farm.efficiency = 0.8
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, density_correction=False,
            #             wake_losses_model='constant_efficiency',
            #             smoothing=True, wind_speed=wind_speed,
            #             standard_deviation_method='Staffell_Pfenninger',
            #             smoothing_order='wind_farm_power_curves').to_frame(
            #             name='{0}_calculated_Const.-SP'.format(
            #                 wind_farm.name)))
            # if 'Calc.-TI' in approach_list:
            #     wind_farm.efficiency = wind_eff_curves[[wind_farm.name]]
            #     wind_farm.efficiency.reset_index(level=0, inplace=True)
            #     wind_farm.efficiency.rename(columns={
            #         'index': 'wind_speed',
            #         wind_farm.name: 'efficiency'}, inplace=True)
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, wind_speed=wind_speed,
            #             wake_losses_model='power_efficiency_curve',
            #             smoothing=True,
            #             standard_deviation_method='turbulence_intensity',
            #             density_correction=False,
            #             smoothing_order='wind_farm_power_curves',
            #             roughness_length=weather[
            #                 'roughness_length'][0].mean()).to_frame(
            #             name='{0}_calculated_Calc.-TI'.format(
            #                 wind_farm.name)))
            # if 'Calc.-SP' in approach_list:
            #     wind_farm.efficiency = wind_eff_curves[[wind_farm.name]]
            #     wind_farm.efficiency.reset_index(level=0, inplace=True)
            #     wind_farm.efficiency.rename(columns={
            #         'index': 'wind_speed',
            #         wind_farm.name: 'efficiency'}, inplace=True)
            #     calculation_df_list.append(
            #         modelchain_usage.power_output_cluster(
            #             wind_farm, weather, wind_speed=wind_speed,
            #             wake_losses_model='power_efficiency_curve',
            #             smoothing=True,
            #             smoothing_order='wind_farm_power_curves',
            #             standard_deviation_method='Staffell_Pfenninger',
            #             density_correction=False).to_frame(
            #             name='{0}_calculated_Calc.-SP'.format(
            #                 wind_farm.name)))
        # Join DataFrames - power output in MW - wind speed in m/s
        if 'wind_speed' in case:
            calculation_df = pd.concat(calculation_df_list, axis=1)
        else:
            calculation_df = pd.concat(
                calculation_df_list, axis=1) / (1 * 10 ** 6)
            calculation_df_db_format['feedin'] = (
                    calculation_df_db_format['feedin'] / (1 * 10 ** 6))
        # Add curtailment for Enertrag wind farm
        # for column_name in list(calculation_df):
        #     if column_name.split('_')[1] == 'BNE':
        #         curtailment = get_enertrag_curtailment_data(weather.index.freq)
        #         # Replace values of 0 with nan as they should not be considered
        #         # in the validation
        #         curtailment.replace(0.0, np.nan, inplace=True)
        #         # Add curtailment to data frame
        #         df = pd.concat([calculation_df[[column_name]], curtailment],
        #                        axis=1)
        #         calculation_df[column_name] = df[column_name] * df[
        #             'curtail_rel']
        return calculation_df, calculation_df_db_format

    def get_time_series_df(weather_data_name, wind_farm_data_list):
        r"""
        If there are any values in restriction_list, the columns containing
        these strings are dropped. This takes place after dumping.

        """
        time_series_filename = os.path.join(
            time_series_dump_folder, 'time_series_df_{0}_{1}_{2}.p'.format(
                case, weather_data_name, year))
        csv_filename = os.path.join(time_series_dump_folder,
                                    'time_series_df_{0}_{1}_{2}.csv'.format(
                                        case, weather_data_name, year))
        if pickle_load_time_series_df:
            time_series_df = pickle.load(open(time_series_filename, 'rb'))
        elif csv_load_time_series_df:
            time_series_df = pd.read_csv(csv_filename, index_col=0,
                                         parse_dates=True)
            # Add frequency attribute
            freq = pd.infer_freq(time_series_df.index)
            time_series_df.index.freq = pd.tseries.frequencies.to_offset(freq)
            pickle.dump(time_series_df, open(time_series_filename, 'wb'))
        else:
            # Get validation and calculated data
            calculation_df, calculation_df_db_format = get_calculated_data(
                weather_data_name, wind_farm_data_list)
            validation_df, validation_df_db_format = get_validation_data(
                frequency=calculation_df.index.freq)
            # Join data frames
            time_series_df = pd.concat([validation_df, calculation_df], axis=1)
            time_series_df_db_format = pd.merge(
                calculation_df_db_format.reset_index(),
                validation_df_db_format.reset_index().rename(
                    columns={'timeindex': 'time'}),
                on=['time', 'turbine_or_farm']).set_index('time')
            # Set value of measured series to nan if respective calculated
            # value is nan and the other way round
            sim_name = 'wind_speed' if 'wind_speed' in case else 'feedin'
            val_name = 'wind_speed_val' if 'wind_speed' in case else 'feedin_val'
            time_series_df_db_format[sim_name].loc[
                time_series_df_db_format[
                    val_name].isnull() == True] = np.nan
            time_series_df_db_format[val_name].loc[
                time_series_df_db_format[
                    sim_name].isnull() == True] = np.nan
            # pickle.dump(time_series_df_db_format,
            #             open(time_series_filename.replace('.p', 'db_format.p'),
            #                  'wb'))
            # todo leave >>>>>>>> for time series df old format
            # column_name_lists = [
            #     [name for name in list(time_series_df) if wf_name in name] for
            #     wf_name in wind_farm_names]
            # for column_name in column_name_lists:
            #     # Nans of calculated data to measured data
            #     time_series_df.loc[:, column_name[0]].loc[
            #         time_series_df.loc[:, column_name[1]].loc[
            #             time_series_df.loc[
            #                 :, column_name[1]].isnull() == True].index] = (
            #                 np.nan)
            #     # Nans of measured data to calculated data
            #     for i in range(len(column_name) - 1):
            #         time_series_df.loc[:, column_name[i+1]].loc[
            #             time_series_df.loc[:, column_name[0]].loc[
            #                 time_series_df.loc[
            #                 :, column_name[0]].isnull() == True].index] = (
            #                     np.nan)
            # # Only keep rows within the right year
            # time_series_df['boolean'] = (time_series_df.index.year == year)
            # time_series_df = time_series_df.loc[
            #    time_series_df.loc[time_series_df['boolean']].index].drop(
            #         ['boolean'], axis=1)
            # pickle.dump(time_series_df, open(time_series_filename, 'wb'))
        if csv_dump_time_series_df:
            time_series_df.to_csv(csv_filename)
            time_series_df_db_format.to_csv(csv_filename.replace(
                '.csv', '_db_format.csv'))
        # todo leave <<<<<<<<< for time series df old format
        # # Drop columns that contain at least one item of `restriction_list` in
        # # their name
        # drop_list = []
        # for restriction in restriction_list:
        #     drop_list.extend(
        #         [column_name for column_name in list(time_series_df) if
        #          restriction in column_name])
        # time_series_df.drop([column_name for column_name in drop_list],
        #                     axis=1, inplace=True)
        return time_series_df, time_series_df_db_format

    # ---------------------------- Helper functions ------------------------- #
    def initialize_dictionary(dict_type, time_series_pairs=None):
        if dict_type == 'validation_objects':
            dictionary = {weather_data_name: {method: {approach:
                          [] for approach in approach_list if
                          approach not in restriction_list} for
                                              method in output_methods}
                          for weather_data_name in weather_data_list}
        if dict_type == 'annual_energy':
            if (time_series_pairs is None):
                raise ValueError("`time_series_pairs` has to be given.")
            wf_strings = ['_'.join(list(time_series_pair)[0].split('_')[:2])
                          for time_series_pair in time_series_pairs]
            dictionary = {
                wf_string: {approach: {'[MWh]': None,
                                       'deviation [%]': None}
                            for approach in approach_list}
                for wf_string in wf_strings}
        return dictionary

    # ---------------------------- Data Evaluation -------------------------- #
    # Get wind farm data
    if 'single' in validation_data_list:
        wind_farm_data_list = return_wind_farm_data(single=True)
        if case in ['weather_wind_speed_3', 'wind_speed_5',
                    'wind_speed_6', 'wind_speed_7', 'wind_speed_8']:
            wind_farm_data_list = [item for item in wind_farm_data_list if
                                   (item['name'] == 'single_BS' or
                                    item['name'] == 'single_BE')]
    elif 'gw_wind_speeds' in validation_data_list:
        wind_farm_data_list = return_wind_farm_data(single=False,
                                                    gw_wind_speeds=True)
    elif 'sh_wind_speeds' in validation_data_list:
        wind_farm_data_list = return_wind_farm_data(single=False,
                                                    sh_wind_speeds=True)
    # elif case == 'wake_losses_3':
    #     wind_farm_data_list = return_wind_farm_data()
    #     wind_farm_data_list = [item for item in wind_farm_data_list if
    #                            item['name'] == 'wf_BS']
    else:
        wind_farm_data_list = return_wind_farm_data()
    # Get wind farm names
    wind_farm_names = [data['name'] for data in wind_farm_data_list]
    # Initialize dictionary for validation objects
    # val_obj_dict = initialize_dictionary(dict_type='validation_objects')
    # Initialize dict for annual energy output of each weather data set
    # annual_energy_dicts = {weather_data_name: None
    #                        for weather_data_name in weather_data_list}
    for weather_data_name in weather_data_list:
        time_series_df, time_series_df_db_format = get_time_series_df(
            weather_data_name, wind_farm_data_list)
        # if time_period is not None:
        #     time_series_df = tools.select_certain_time_steps(time_series_df,
        #                                                      time_period)

        ################ simple validation ####################################
        if not os.path.exists(validation_folder):
            os.makedirs(validation_folder, exist_ok=True)
        filename = os.path.join(os.path.dirname(__file__), validation_folder,
                                'validation_{}_{}_{}.csv'.format(
                                    case, weather_data_name,
                                    year))
        sim_name = 'wind_speed' if 'wind_speed' in case else 'feedin'
        val_name = 'wind_speed_val' if 'wind_speed' in case else 'feedin_val'
        val_tools.calculate_validation_metrics(
            df=time_series_df_db_format, val_cols=[sim_name, val_name],
            metrics='standard', filter_cols=['turbine_or_farm', 'approach'],
            filename=filename)


        # if time_period is not None:
        #     time_series_df = tools.select_certain_time_steps(time_series_df,
        #                                                      time_period)

        # # Create list of time series data frames (for each wind farm for each
        # # approach) - measured and calculated data
        # time_series_df_parts = [
        #     time_series_df.loc[:, [
        #         column_name for column_name in list(time_series_df) if
        #         '{}_'.format(wf_name) in column_name]] for
        #             wf_name in wind_farm_names if
        #     wf_name not in restriction_list]
        # time_series_pairs = [time_series_df.loc[:, [
        #     '{0}_measured'.format(wf_name), '{0}_calculated_{1}'.format(
        #         wf_name, approach)]] for
        #     wf_name in wind_farm_names for approach in approach_list if
        #     '{0}_calculated_{1}'.format(wf_name, approach) in list(
        #         time_series_df)]

        # Initialize dictionary for annual energy output
        # annual_energy_dict_weather = initialize_dictionary(
        #     dict_type='annual_energy', time_series_pairs=time_series_pairs)
        # if ('annual_energy_approaches' in latex_output or
        #         'annual_energy_weather' in latex_output):
        #     # Write annual energy outputs and deviations into
        #     # `annual_energy_dict`
        #     for time_series_df_part in time_series_df_parts:
        #         wf_string = '_'.join(
        #             list(time_series_df_part)[0].split('_')[:2])
        #         # Measured annual energy output
        #         measured_output = tools.annual_energy_output(
        #             time_series_df_part.loc[:,
        #                                     '{0}_measured'.format(wf_string)])
        #         annual_energy_dict_weather[
        #             wf_string]['measured_annual_energy'] = measured_output
        #         # Calculated annual energy output and deviation from measured
        #         # in %
        #         for column_name in list(time_series_df_part):
        #             if 'measured' not in column_name:
        #                 approach_string = '_'.join(column_name.split('_')[3:])
        #                 calculated_output = tools.annual_energy_output(
        #                     time_series_df_part.loc[
        #                         :, '{0}_calculated_{1}'.format(
        #                             wf_string, approach_string)])
        #                 annual_energy_dict_weather[wf_string][
        #                     approach_string]['[MWh]'] = (
        #                     calculated_output)
        #                 annual_energy_dict_weather[wf_string][
        #                     approach_string]['deviation [%]'] = (
        #                     (calculated_output - measured_output) /
        #                     measured_output * 100)
        #     # Add dictionary to `annual_energy_dicts`
        #     annual_energy_dicts[weather_data_name] = annual_energy_dict_weather
        # for time_series_pair in time_series_pairs:
        #     wf_string = '_'.join(list(time_series_pair)[0].split('_')[:2])
        #     approach_string = '_'.join(
        #         list(time_series_pair)[1].split('_')[3:])
        #     if 'half_hourly' in output_methods:
        #         if weather_data_name == 'open_FRED':
        #             val_obj_dict[weather_data_name]['half_hourly'][
        #                 approach_string].append(ValidationObject(
        #                     name=wf_string, data=time_series_pair,
        #                     output_method='half_hourly',
        #                     weather_data_name=weather_data_name,
        #                     approach=approach_string,
        #                     min_periods_pearson=min_periods_pearson))
        #     if 'hourly' in output_methods:
        #         if weather_data_name == 'open_FRED':
        #             hourly_series = tools.resample_with_nan_theshold(
        #                 df=time_series_pair, frequency='H',
        #                 threshold=get_threshold('H',
        #                                         time_series_pair.index.freq.n))
        #         else:
        #             hourly_series = time_series_pair
        #         val_obj_dict[weather_data_name]['hourly'][
        #             approach_string].append(ValidationObject(
        #                 name=wf_string, data=hourly_series,
        #                 output_method='hourly',
        #                 weather_data_name=weather_data_name,
        #                 approach=approach_string,
        #                 min_periods_pearson=min_periods_pearson))
        #     if 'monthly' in output_methods:
        #         if case not in [
        #                 'weather_wind_speed_3', 'wind_speed_5',
        #                 'wind_speed_6', 'wind_speed_7', 'wind_speed_8']:
        #             monthly_series = tools.resample_with_nan_theshold(
        #                 df=time_series_pair, frequency='M',
        #                 threshold=get_threshold(
        #                     'M', time_series_pair.index.freq.n))
        #             val_obj_dict[weather_data_name]['monthly'][
        #                 approach_string].append(ValidationObject(
        #                     name=wf_string, data=monthly_series,
        #                     output_method='monthly',
        #                     weather_data_name=weather_data_name,
        #                     approach=approach_string,
        #                     min_periods_pearson=min_periods_pearson))
        # # Delete entry in dict if half_hourly resolution not possible
        # if (time_series_pairs[0].index.freq == 'H' and
        #         'half_hourly' in val_obj_dict[weather_data_name]):
        #     del val_obj_dict[weather_data_name]['half_hourly']

        # ###### Visualization ######
        # # Define folder
        # if ('wind_speed' in case and 'weather' not in case):
        #     folder = 'wind_speed'
        # elif ('power_output' in case and 'weather' not in case):
        #     folder = 'power_output'
        # elif ('single_turbine' in case and 'weather' not in case):
        #     folder = 'single_turbine'
        # # elif 'smoothing' in case:
        # #     folder = 'smoothing'
        # # elif 'wake_losses' in case:
        # #     folder = 'wake_losses'
        # # elif ('wind_farm' in case and 'weather' not in case):
        # #     folder = 'wind_farm'
        # elif 'weather_wind_speed' in case:
        #     folder = 'weather_wind_speed'
        # elif 'weather_wind_farm' in case:
        #     folder = 'weather_wind_farm'
        # elif (case == 'weather_single_turbine_1' or
        #       case == 'weather_single_turbine_2'):
        #     folder = 'weather_single_turbine'
        # else:
        #     folder = ''
        # # Define y label add on
        # if 'wind_speed' in case:
        #     examined_value = 'wind speed'
        #     y_label_add_on = '{0} in m/s'.format(examined_value)
        # else:
        #     examined_value = 'power output'
        #     y_label_add_on = '{0} in MW'.format(examined_value)
        #
        # if 'feedin_comparison' in visualization_methods:
        #     # time series pair/part and approach string multiple
        #     if feedin_comparsion_all_in_one:
        #         plot_dfs = time_series_df_parts
        #         approach_string = 'multiple'
        #         # Bring df into order
        #         cols = [col for col in list(plot_dfs[0]) if 'measured' in col]
        #         others = [col for col in list(plot_dfs[0]) if
        #                   'measured' not in col]
        #         cols.extend(others)
        #         plot_dfs = [plot_dfs[0][cols]]
        #     else:
        #         plot_dfs = time_series_pairs
        #         approach_string = None
        #     for plot_df in plot_dfs:
        #         # Specify save folder and title add on
        #         if time_period is not None:
        #             add_on = (
        #                 '{0}_{1}'.format(time_period[0], time_period[1]))
        #             title_add_on = ' time of day: {0}:00 - {1}:00'.format(
        #                 time_period[0], time_period[1])
        #         else:
        #             add_on = 'None'
        #             title_add_on = ''
        #         save_folder = ('../../../User-Shares/Masterarbeit/Latex/inc/' +
        #                        'images/Plots/{0}/'.format(folder))
        #         for method in output_methods:
        #             # Resample if necessary
        #             if method == 'hourly':
        #                 if weather_data_name == 'open_FRED':
        #                     plot_df = tools.resample_with_nan_theshold(
        #                         df=plot_df, frequency='H',
        #                         threshold=get_threshold('H',
        #                                                 plot_df.index.freq.n))
        #             if method == 'monthly':
        #                 plot_df = tools.resample_with_nan_theshold(
        #                     df=plot_df, frequency='M',
        #                     threshold=get_threshold('M', plot_df.index.freq.n))
        #             # Set approach string and wind farm name string
        #             if approach_string != 'multiple':
        #                 approach_string = '_'.join(list(plot_df)[1].split(
        #                     '_')[3:])
        #             wf_string = '_'.join(list(plot_df)[0].split(
        #                 '_')[:2])
        #             for start_end in start_end_list:
        #                 if (method == 'monthly' and start_end[0] is not None):
        #                     # Do not plot
        #                     pass
        #                 elif (method == 'half_hourly' and
        #                         weather_data_name == 'MERRA'):
        #                     pass
        #                 else:
        #                     feedin_filename = (
        #                             save_folder +
        #                             '{0}_{1}_feedin_{2}_{3}_{4}_{5}_{6}_{7}{8}.png'.format(
        #                                 case, method, wf_string, year,
        #                                 weather_data_name, add_on,
        #                                 approach_string,
        #                                 (start_end[0].split(':')[0] if
        #                                  start_end[0] else ''),
        #                                 (start_end[1].split(':')[0] if
        #                                  start_end[0] else '')))
        #                     feedin_title = (
        #                             '{0} {1} of {2} calculated with {3} data\n in {4} ({5} approach)'.format(
        #                                 method.replace('_', ' '),
        #                                 examined_value, wf_string,
        #                                 weather_data_name, year,
        #                                 approach_string) + title_add_on)
        #                     visualization_tools.plot_feedin_comparison(
        #                         data=plot_df, method=method,
        #                         filename=feedin_filename, title=feedin_title,
        #                         tick_label=None, start=start_end[0],
        #                         end=start_end[1],
        #                         y_label_add_on=y_label_add_on)
        #                     # Also plot as pdf
        #                     visualization_tools.plot_feedin_comparison(
        #                         data=plot_df, method=method,
        #                         filename=feedin_filename.replace(
        #                             '.png', '.pdf'), title=feedin_title,
        #                         tick_label=None, start=start_end[0],
        #                         end=start_end[1],
        #                         y_label_add_on=y_label_add_on)
        #
        # if 'plot_correlation' in visualization_methods:
        #     for time_series_pair in time_series_pairs:
        #         # Specify save folder and title add on
        #         if time_period is not None:
        #             add_on = (
        #                 '{0}_{1}'.format(time_period[0], time_period[1]))
        #             title_add_on = ' time of day: {0}:00 - {1}:00'.format(
        #                 time_period[0], time_period[1])
        #         else:
        #             add_on = 'None'
        #             title_add_on = ''
        #         save_folder = ('../../../User-Shares/Masterarbeit/Latex/inc/' +
        #                        'images/Plots/{0}/'.format(folder))
        #         for method in output_methods:
        #             if (method == 'half_hourly' and
        #                     weather_data_name == 'MERRA'):
        #                 # Do not plot
        #                 pass
        #             elif method == 'monthly':
        #                 time_series_pair = tools.resample_with_nan_theshold(
        #                     df=time_series_pair, frequency='M',
        #                     threshold=get_threshold(
        #                         'M', time_series_pair.index.freq.n))
        #             else:
        #                 approach_string = '_'.join(
        #                     list(time_series_pair)[1].split('_')[3:])
        #                 wf_string = '_'.join(
        #                     list(time_series_pair)[0].split('_')[:2])
        #                 corr_filename = (
        #                         save_folder +
        #                         '{0}_{1}_Correlation_{1}_{2}_{3}_{4}_{5}_{6}.png'.format(
        #                             case, method, wf_string, year,
        #                             weather_data_name, approach_string,
        #                             add_on))
        #                 corr_title = (
        #                         '{0} {1} of {2} calculated with {3} data\n in {4} ({5} '.format(
        #                             method.replace('_', ' '), examined_value,
        #                             wf_string, weather_data_name, year,
        #                             approach_string) +
        #                         'approach)' + title_add_on)
        #                 visualization_tools.plot_correlation(
        #                     data=time_series_pair, method=method,
        #                     filename=corr_filename, title=corr_title,
        #                     color='darkblue', marker_size=3,
        #                     y_label_add_on=y_label_add_on)
        #                 # Also plot as pdf
        #                 visualization_tools.plot_correlation(
        #                     data=time_series_pair, method=method,
        #                     filename=corr_filename.replace(
        #                         '.png', '.pdf'), title=corr_title,
        #                     color='darkblue', marker_size=3,
        #                     y_label_add_on=y_label_add_on)
        # if 'subplots_correlation' in visualization_methods:
        #     if len(approach_list) <= 4:
        #         for time_series_df_part in time_series_df_parts:
        #             if weather_data_name == 'open_FRED':
        #                 # Resample the DataFrame columns
        #                 time_series_df_part = tools.resample_with_nan_theshold(
        #                     df=time_series_df_part, frequency='H',
        #                     threshold=get_threshold(
        #                         'H', time_series_df_part.index.freq.n))
        #             wf_name = '_'.join(list(
        #                 time_series_df_part)[0].split('_')[0:2])
        #             sub_filename = os.path.join(
        #                     os.path.dirname(__file__),
        #                     '../../../User-Shares/Masterarbeit/Latex/inc/' +
        #                     'images/correlation_sub',
        #                     'Correlation_{}_{}_{}_{}'.format(
        #                         case, weather_data_name, year, wf_name))
        #             visualization_tools.correlation_subplot(
        #                 time_series_df_part, filename=sub_filename)
        #             # Also plot as pdf
        #             visualization_tools.correlation_subplot(
        #                 time_series_df_part, filename=sub_filename.replace(
        #                     '.png', '.pdf'))

    # ------------------------------ LaTeX Output --------------------------- #
    # path_latex_tables = os.path.join(os.path.dirname(__file__),
    #                                  latex_tables_folder)
    # if time_period is not None:
    #     filename_add_on = '_{0}_{1}'.format(time_period[0], time_period[1])
    # else:
    #     filename_add_on = ''

    # Write latex output
    # latex_tables.write_latex_output(
    #     latex_output=latex_output, weather_data_list=weather_data_list,
    #     approach_list=approach_list, restriction_list=restriction_list,
    #     val_obj_dict=val_obj_dict, annual_energy_dicts=annual_energy_dicts,
    #     wind_farm_names=wind_farm_names, key_figures_print=key_figures_print,
    #     output_methods=output_methods, path_latex_tables=path_latex_tables,
    #     filename_add_on=filename_add_on, year=year, case=case,
    #     replacement=replacement, csv_folder=csv_folder)

    logging.info("--- Simulation with case {0} in year {1} end ---".format(
        case, year))

if __name__ == "__main__":
    for case in cases:
        # Get parameters from config file (they are set below)
        parameters = get_configuration(case)
        years = parameters['years']
        for year in years:
            run_main(case=case, year=year, parameters=parameters)

    # ---- Further latex tables and plots ----#
    # logging.info(
    #     "--- Depending on the cases further latex tables are created. ---")
    # if 'power_output_1' in cases:
    #     latex_tables.mean_annual_energy_deviation_tables(
    #         latex_tables_folder, 'power_output_1', csv_folder=csv_folder)
    #     latex_tables.carry_out_mean_figure_tables(
    #         latex_tables_folder, cases=['power_output_1'],
    #         csv_folder=csv_folder)
    #     latex_tables.annual_energy_deviation(
    #         latex_tables_folder, csv_folder=csv_folder,
    #         case='power_output_1', single=True)
    #     latex_tables.annual_energy_deviation_wfs(
    #         latex_tables_folder, csv_folder=csv_folder, case='power_output_1')
    # if 'smoothing_1' in cases:
    #     latex_tables.concat_std_dev_tables_smoothing_1(
    #         latex_tables_folder, csv_folder=csv_folder)
    #     latex_tables.concat_key_figures_tables_smoothing_1(
    #         latex_tables_folder, csv_folder=csv_folder)
    # if 'smoothing_2' in cases:
    #     latex_tables.mean_std_dev_smoothing_2(latex_tables_folder,
    #                                           csv_folder=csv_folder)
    # if 'single_turbine_1' in cases:
    #     latex_tables.carry_out_mean_figure_tables(
    #         latex_tables_folder, cases=['single_turbine_1'],
    #         csv_folder=csv_folder)
    #     latex_tables.annual_energy_deviation(
    #         latex_tables_folder, case='single_turbine_1', single=True,
    #         csv_folder=csv_folder)
    #     latex_tables.annual_energy_deviation_wfs(
    #         latex_tables_folder, case='single_turbine_1',
    #         csv_folder=csv_folder)
    #     latex_tables.mean_annual_energy_deviation_tables(
    #         latex_tables_folder, 'single_turbine_1', csv_folder=csv_folder)
    # if 'weather_wind_speed_1' in cases:
    #     latex_tables.carry_out_mean_figure_tables(
    #         latex_tables_folder, cases=['weather_wind_speed_1'],
    #         csv_folder=csv_folder)
    # if 'weather_wind_farm' in cases:
    #     latex_tables.carry_out_mean_figure_tables(
    #         latex_tables_folder, cases=['weather_wind_farm'],
    #         csv_folder=csv_folder)
    #     latex_tables.annual_energy_deviation(
    #         latex_tables_folder, case='weather_wind_farm', single=True,
    #         csv_folder=csv_folder)
    #     latex_tables.annual_energy_deviation_wfs(
    #         latex_tables_folder, case='weather_wind_farm',
    #         csv_folder=csv_folder)
    # if 'wind_farm_2' in cases:
    #     latex_tables.annual_energy_deviation(
    #         latex_tables_folder, case='wind_farm_2', single=True,
    #         csv_folder=csv_folder)
    #     latex_tables.annual_energy_deviation_wfs(
    #         latex_tables_folder, case='wind_farm_2', csv_folder=csv_folder)
    #     latex_tables.mean_annual_energy_deviation_tables(
    #         latex_tables_folder, 'wind_farm_2', csv_folder=csv_folder)
    # if 'wind_farm_gw' in cases:
    #     latex_tables.annual_energy_deviation(
    #         latex_tables_folder, case='wind_farm_gw', single=True,
    #         csv_folder=csv_folder)
    #     latex_tables.annual_energy_deviation_wfs(
    #         latex_tables_folder, case='wind_farm_gw', csv_folder=csv_folder)
    #     latex_tables.mean_annual_energy_deviation_tables(
    #         latex_tables_folder, 'wind_farm_gw', csv_folder=csv_folder)
    # logging.info(
    #     "--- Depending on the cases further plots are created. ---")
    # if plot_single_func:
    #     plots_single_functionalities.run_all_plots()
    # logging.info("--- Done ---")
