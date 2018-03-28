# Imports from Windpowerlib
from windpowerlib import wind_farm as wf
from windpowerlib import wind_turbine_cluster as wtc

# Imports from lib_validation
import visualization_tools
import tools
import latex_tables
import modelchain_usage
from wind_farm_specifications import (get_joined_wind_farm_data,
                                      get_wind_farm_data)
from merra_weather_data import get_merra_data
from open_fred_weather_data import get_open_fred_data
from argenetz_data import get_argenetz_data
from enertrag_data import get_enertrag_data, get_enertrag_curtailment_data
from analysis_tools import ValidationObject
from greenwind_data import (get_greenwind_data,
                            get_first_row_turbine_time_series)
from config_simulation_cases import get_configuration

# Other imports
import os
import pandas as pd
import numpy as np
import pickle
import logging

logging.getLogger().setLevel(logging.INFO)

# ----------------------------- Set parameters ------------------------------ #
cases = [
    # 'wind_speed_1',
    # 'wind_speed_2',
    # 'single_turbine_1',
    # 'single_turbine_2',
    'smoothing_1'
]
years = [
    2015,
    2016
]

min_periods_pearson = None  # Integer

# Pickle load time series data frame - if one of the below pickle_load options
# is set to False, `pickle_load_time_series_df` is automatically set to False
pickle_load_time_series_df = False

pickle_load_merra = True
pickle_load_open_fred = True
pickle_load_arge = True
pickle_load_enertrag = True
pickle_load_greenwind = True
pickle_load_wind_farm_data = True

csv_load_time_series_df = False  # Load time series data frame from csv dump
csv_dump_time_series_df = True  # Dump df as csv

feedin_comparsion_all_in_one = True  # Plots all calculated series for one
                                      # wind farm in one plot

# Select time of day you want to observe or None for all day
time_period = (
#       6, 22  # time of day to be selected (from h to h)
         None   # complete time series will be observed
        )

# Relative path to latex tables folder
latex_tables_folder = ('../../../User-Shares/Masterarbeit/Latex/Tables/' +
                       'automatic/')

# Other plots
plot_arge_feedin = False  # If True plots each column of ArgeNetz data frame

# Filename specifications
validation_pickle_folder = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'dumps/validation_data'))
wind_farm_pickle_folder = os.path.join(os.path.dirname(__file__),
                                       'dumps/wind_farm_data')
time_series_df_folder = os.path.join(os.path.dirname(__file__),
                                     'dumps/time_series_dfs')

# Heights for which temperature of MERRA shall be calculated
temperature_heights = [60, 64, 65, 105, 114]

# Threshold factor. F.e. if threshold_factor is 0.5 resampling is only done, if
# more than 50 percent of the values are not nan.
threshold_factor = 0.5

# If pickle_load options not all True:
if (not pickle_load_merra or not pickle_load_open_fred or not
        pickle_load_arge or not pickle_load_enertrag or not
        pickle_load_greenwind or not pickle_load_wind_farm_data):
    pickle_load_time_series_df = False

def run_main(case, year):
    logging.info("--- Simulation with case {0} in year {1} starts ---".format(
        case, year))
    # Get parameters from config file (they are set below)
    parameters = get_configuration(case)

    # Start and end date for time period to be plotted when 'feedin_comparison'
    # is selected. (not for monthly output).
    start_end_list = [
        (None, None),
    #    ('{0}-10-01 11:00:00+00:00'.format(year), '{0}-10-01 16:00:00+00:00'.format(year)),
        ('{0}-10-01'.format(year), '{0}-10-07'.format(year)),
        ('{0}-06-01'.format(year), '{0}-06-07'.format(year))
        ]

    #extra_plots = np.array([ # NOTE: not working
    ##    'annual_bars_weather'  # Bar plot of annual energy output for all weather data and years
    #    ])

    # Set paramters
    restriction_list = parameters['restriction_list']
    validation_data_list = parameters['validation_data_list']
    weather_data_list = parameters['weather_data_list']
    approach_list = parameters['approach_list']
    output_methods = parameters['output_methods']
    visualization_methods = parameters['visualization_methods']
    latex_output = parameters['latex_output']
    key_figures_print = parameters['key_figures_print']

    # -------------------------------- Warning ------------------------------ #
    if (year == 2015 and validation_data_list[0] == 'Enertrag' and
            validation_data_list[-1] == 'Enertrag'):
        raise ValueError("Enertrag data not available for 2015 - select other " +
                         "validation data or year 2016")


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
            'wf_1_measured', 'wf_2_measured', etc. OR 'single_6_measured',
            'single_7_measured', 'single_6_measured_wind' etc.

        """
        validation_df_list = []
        if 'ArgeNetz' in validation_data_list:
            # Get wind farm data
            wind_farm_data_arge = get_wind_farm_data(
                'farm_specification_argenetz_{0}.p'.format(year),
                wind_farm_pickle_folder, pickle_load_wind_farm_data)
            # Get ArgeNetz Data
            arge_data = get_argenetz_data(
                year, pickle_load=pickle_load_arge,
                filename=os.path.join(validation_pickle_folder,
                                      'arge_netz_data_{0}.p'.format(year)),
                csv_dump=False, plot=plot_arge_feedin)
            # Select only columns containing the power output and rename them
            arge_data = arge_data[[
                '{0}_power_output'.format(data['object_name']) for
                data in wind_farm_data_arge]].rename(
                columns={col: col.replace('power_output', 'measured') for
                         col in arge_data.columns})
            # Set negative values to nan (for Enertrag and GreenWind this
            # happens in the separate modules)
            arge_data = tools.negative_values_to_nan(arge_data)
            # Resample the DataFrame columns with `frequency` and `threshold`
            # and add to list
            threshold = get_threshold(frequency, arge_data.index.freq.n)
            validation_df_list.append(tools.resample_with_nan_theshold(
                df=arge_data, frequency=frequency, threshold=threshold))
        if ('Enertrag' in validation_data_list and year == 2016):
            # Get Enertrag Data
            enertrag_data = get_enertrag_data(
                pickle_load=pickle_load_enertrag,
                filename=os.path.join(validation_pickle_folder,
                                      'enertrag_data.p'))
            # Select aggregated power output of wind farm (rename)
            enertrag_data = enertrag_data[['wf_9_power_output']].rename(
                columns={'wf_9_power_output': 'wf_9_measured'})
            # Resample the DataFrame columns with `frequency` and add to list
            threshold = get_threshold(frequency, enertrag_data.index.freq.n)
            validation_df_list.append(tools.resample_with_nan_theshold(
                df=enertrag_data, frequency=frequency, threshold=threshold))
        if 'GreenWind' in validation_data_list:
            # Get wind farm data
            wind_farm_data_gw = get_wind_farm_data(
                'farm_specification_greenwind_{0}.p'.format(year),
                wind_farm_pickle_folder, pickle_load_wind_farm_data)
            # Get Greenwind data
            greenwind_data = get_greenwind_data(
                year, pickle_load=pickle_load_greenwind,
                filename=os.path.join(validation_pickle_folder,
                                      'greenwind_data_{0}.p'.format(year)),
                filter_errors=True, threshold=threshold)
            # Select aggregated power output of wind farm (rename)
            greenwind_data = greenwind_data[[
                '{0}_power_output'.format(data['object_name']) for
                data in wind_farm_data_gw]].rename(
                columns={col: col.replace('power_output', 'measured') for
                         col in greenwind_data.columns})
            # Resample the DataFrame columns with `frequency` and add to list
            threshold = get_threshold(frequency, greenwind_data.index.freq.n)
            validation_df_list.append(tools.resample_with_nan_theshold(
                df=greenwind_data, frequency=frequency, threshold=threshold))
        if 'single' in validation_data_list:
            single_data = get_first_row_turbine_time_series(
                year=year, filter_errors=True, print_error_amount=False,
                pickle_filename=os.path.join(
                    os.path.dirname(__file__), 'dumps/validation_data',
                    'greenwind_data_first_row_{0}.p'.format(year)),
                pickle_load=pickle_load_greenwind)
            if 'wind_speed' in case:
                # Get first row single turbine wind speed and rename columns
                single_data = single_data[[col for col in list(single_data) if
                                           'wind_speed' in col]].rename(
                    columns={column: column.replace(
                        'wind_speed', 'measured').replace('wf', 'single') for
                        column in list(single_data)})
            else:
                single_data = single_data[[col for col in list(single_data) if
                                           'power_output' in col]].rename(
                    columns={column: column.replace(
                        'power_output', 'measured').replace('wf', 'single') for
                        column in list(single_data)})
            # Resample the DataFrame columns with `frequency` and add to list
            threshold = get_threshold(frequency, single_data.index.freq.n)
            validation_df_list.append(tools.resample_with_nan_theshold(
                df=single_data, frequency=frequency, threshold=threshold))
        # Join DataFrames - power output in MW - wind speed in m/s
        if (case == 'wind_speed_1' or case == 'wind_speed_2'):
            validation_df = pd.concat(validation_df_list, axis=1)
        else:
            validation_df = pd.concat(validation_df_list, axis=1) / 1000
        return validation_df


    # ---------------------------- Wind farm data --------------------------- #
    def return_wind_farm_data(single=False):
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
                    item['object_name'] = 'single_{}'.format(
                        item['object_name'].split('_')[1])
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
    def get_calculated_data(weather_data_name):
        r"""
        Calculates time series with different approaches.

        Data is saved in a DataFrame that can later be joined with the
        validation data frame.

        Parameters
        ----------
        weather_data_name : String
            Weather data for which the feed-in is calculated.

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
        if weather_data_name == 'MERRA':
            if not pickle_load_merra:
                get_merra_data(year, heights=temperature_heights,
                               filename=filename_weather)
        if weather_data_name == 'open_FRED':
            if not pickle_load_open_fred:
                fred_path = os.path.join(
                    os.path.dirname(__file__), 'data/open_FRED',
                    'fred_data_{0}_sh.csv'.format(year))
                get_open_fred_data(
                    filename=fred_path, pickle_filename=filename_weather,
                    pickle_load=False)

        # Get wind farm data
        if 'single' in validation_data_list:
            wind_farm_data_list = return_wind_farm_data(single=True)
        else:
            wind_farm_data_list = return_wind_farm_data()
        # Initialise calculation_df_list and calculate power output
        calculation_df_list = []
        # Initialise wind farms
        wind_farm_list = [wf.WindFarm(**wind_farm_data) for
                          wind_farm_data in wind_farm_data_list]
        for wind_farm in wind_farm_list:
            # Get weather data for specific coordinates
            weather = tools.get_weather_data(
                weather_data_name, wind_farm.coordinates, pickle_load=True,
                filename=filename_weather, year=year,
                temperature_heights=temperature_heights)
            if case == 'single_turbine_2':
                # Use wind speed from first row GreenWind data as weather data
                single_data_raw = get_first_row_turbine_time_series(
                    year=year, filter_errors=True, print_error_amount=False,
                    pickle_filename=os.path.join(
                        os.path.dirname(__file__), 'dumps/validation_data',
                        'greenwind_data_first_row_{0}.p'.format(year)),
                    pickle_load=pickle_load_greenwind)
                wind_speed_data = single_data_raw[['wf_{}_wind_speed'.format(
                    wind_farm.object_name.split('_')[1])]]
            # Calculate power output and store in list
            if 'logarithmic' in approach_list:
            # if (case == 'wind_speed_1' and 'logarithmic' in approach_list):  # TODO: if logarithmic in other case
                calculation_df_list.append(
                    modelchain_usage.wind_speed_to_hub_height(
                        wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                        weather_df=weather, wind_speed_model='logarithmic',
                        obstacle_height=0).to_frame(
                        name='{0}_calculated_logarithmic'.format(
                            wind_farm.object_name)))
            # if 'logarithmic_obstacle' in approach_list:
            #     # TODO: add obstacle height per wind farm (if wf == ... oh = )
            if 'hellman' in approach_list:
                calculation_df_list.append(
                    modelchain_usage.wind_speed_to_hub_height(
                        wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                        weather_df=weather, wind_speed_model='hellman',
                        hellman_exp=None).to_frame(
                        name='{0}_calculated_hellman'.format(
                            wind_farm.object_name)))
            if 'hellman_2' in approach_list:
                calculation_df_list.append(
                    modelchain_usage.wind_speed_to_hub_height(
                        wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                        weather_df=weather, wind_speed_model='hellman',
                        hellman_exp=1 / 7).to_frame(
                        name='{0}_calculated_hellman_2'.format(
                            wind_farm.object_name)))
            if 'lin._interp.' in approach_list:
                if len(list(weather['wind_speed'])) > 1:
                    calculation_df_list.append(
                        modelchain_usage.wind_speed_to_hub_height(
                            wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                            weather_df=weather,
                            wind_speed_model='interpolation_extrapolation').to_frame(
                            name='{0}_calculated_lin._interp.'.format(
                                wind_farm.object_name)))
            if 'log._interp.' in approach_list:
                if len(list(weather['wind_speed'])) > 1:
                    calculation_df_list.append(
                        modelchain_usage.wind_speed_to_hub_height(
                            wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                            weather_df=weather,
                            wind_speed_model='log_interpolation_extrapolation').to_frame(
                            name='{0}_calculated_log._interp.'.format(
                                wind_farm.object_name)))
            if case == 'single_turbine_2':
                wind_speed = (wind_speed_data if
                              weather_data_name == 'open_FRED' else
                              tools.resample_with_nan_theshold(
                                  df=wind_speed_data,
                                  frequency=weather.index.freq,
                                  threshold=get_threshold(
                                      out_frequency=weather.index.freq,
                                      original_resolution=wind_speed_data.index.freq.n)))
            else:
                wind_speed = None
            if 'p-curve' in approach_list:
                calculation_df_list.append(
                    modelchain_usage.power_output_simple(
                        wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                        weather_df=weather, wind_speed=wind_speed,
                        wind_speed_model='logarithmic',
                        density_model='ideal_gas',
                        temperature_model='linear_gradient',
                        power_output_model='power_curve',
                        density_correction=False, obstacle_height=0,
                        hellman_exp=None).to_frame(
                        name='{0}_calculated_p-curve'.format(
                            wind_farm.object_name)))
            if 'cp-curve' in approach_list:
                calculation_df_list.append(
                    modelchain_usage.power_output_simple(
                        wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                        weather_df=weather, wind_speed=wind_speed,
                        wind_speed_model='logarithmic',
                        density_model='ideal_gas',
                        temperature_model='linear_gradient',
                        power_output_model='power_coefficient_curve',
                        density_correction=False,
                        obstacle_height=0, hellman_exp=None).to_frame(
                        name='{0}_calculated_cp-curve'.format(
                            wind_farm.object_name)))
            if 'p-curve_(d._c.)' in approach_list:
                calculation_df_list.append(
                    modelchain_usage.power_output_simple(
                        wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                        weather_df=weather, wind_speed=wind_speed,
                        wind_speed_model='logarithmic',
                        density_model='ideal_gas',
                        temperature_model='linear_gradient',
                        power_output_model='power_coefficient_curve',
                        density_correction=True,
                        obstacle_height=0, hellman_exp=None).to_frame(
                        name='{0}_calculated_p-curve_(d._c.)'.format(
                            wind_farm.object_name)))
            if 'cp-curve_(d._c.)' in approach_list:
                calculation_df_list.append(
                    modelchain_usage.power_output_simple(
                        wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                        weather_df=weather, wind_speed=wind_speed,
                        wind_speed_model='logarithmic',
                        density_model='ideal_gas',
                        temperature_model='linear_gradient',
                        power_output_model='power_coefficient_curve',
                        density_correction=True,
                        obstacle_height=0, hellman_exp=None).to_frame(
                        name='{0}_calculated_cp-curve_(d._c.)'.format(
                            wind_farm.object_name)))
            if ('turbine' in approach_list and case == 'smoothing_1'):
                calculation_df_list.append(
                    modelchain_usage.power_output_cluster(
                        wind_farm, weather, density_correction=False,
                        wake_losses_method=None, smoothing=True,
                        block_width=0.5,
                        standard_deviation_method='turbulence_intensity',
                        smoothing_order='turbine_power_curves',
                        roughness_length=weather[
                            'roughness_length'][0].mean()).to_frame(
                            name='{0}_calculated_turbine'.format(
                                wind_farm.object_name)))


        #     if 'simple' in approach_list:
        #         calculation_df_list.append(modelchain_usage.power_output_simple(
        #             wind_farm.wind_turbine_fleet, weather).to_frame(
        #                 name='{0}_calculated_simple'.format(
        #                     wind_farm.object_name)))
        #     if 'density_correction' in approach_list:
        #         calculation_df_list.append(modelchain_usage.power_output_simple(
        #             wind_farm.wind_turbine_fleet, weather,
        #             density_correction=True).to_frame(
        #                 name='{0}_calculated_density_correction'.format(
        #                     wind_farm.object_name)))
        #     if 'smooth_wf' in approach_list:
        #         calculation_df_list.append(modelchain_usage.power_output_cluster(
        #             wind_farm, weather, density_correction=False,
        #             wake_losses_method=None, smoothing=True,
        #             block_width=0.5,
        #             standard_deviation_method='turbulence_intensity',
        #             smoothing_order='wind_farm_power_curves',
        #             roughness_length=weather[
        #                 'roughness_length'][0].mean(),
        #             wind_speed_model='logarithmic').to_frame(
        #                     name='{0}_calculated_smooth_wf'.format(
        #                         wind_farm.object_name)))
        #     if 'constant_efficiency_90_%' in approach_list:
        #         wind_farm.efficiency = 0.8
        #         calculation_df_list.append(modelchain_usage.power_output_cluster(
        #             wind_farm, weather, density_correction=False,
        #             wake_losses_method='constant_efficiency', smoothing=False).to_frame(
        #                 name='{0}_calculated_constant_efficiency_90_%'.format(
        #                     wind_farm.object_name)))
        #     if 'constant_efficiency_80_%' in approach_list:
        #         wind_farm.efficiency = 0.8
        #         calculation_df_list.append(modelchain_usage.power_output_cluster(
        #             wind_farm, weather, density_correction=False,
        #             wake_losses_method='constant_efficiency', smoothing=False).to_frame(
        #                 name='{0}_calculated_constant_efficiency_80_%'.format(
        #                     wind_farm.object_name)))
        #     if 'efficiency_curve' in approach_list:
        #         wind_farm.efficiency = wf.read_wind_efficiency_curve(
        #             curve_name='dena_mean', plot=False)
        #         calculation_df_list.append(modelchain_usage.power_output_cluster(
        #             wind_farm, weather, density_correction=False,
        #             wake_losses_method='wind_efficiency_curve', smoothing=False).to_frame(
        #             name='{0}_calculated_efficiency_curve'.format(
        #                 wind_farm.object_name)))
        #     if 'eff_curve_smooth' in approach_list:
        #         wind_farm.efficiency = wf.read_wind_efficiency_curve(
        #             curve_name='dena_mean', plot=False)
        #         calculation_df_list.append(modelchain_usage.power_output_cluster(
        #             wind_farm, weather, density_correction=False,
        #             wake_losses_method='wind_efficiency_curve', smoothing=True,
        #             density_correction_order='wind_farm_power_curves',
        #             smoothing_order='wind_farm_power_curves',
        #             roughness_length=weather[
        #                 'roughness_length'][0].mean()).to_frame(
        #             name='{0}_calculated_eff_curve_smooth'.format(
        #                 wind_farm.object_name)))
        #     if 'lin._interp.' in approach_list:
        #         if len(list(weather['wind_speed'])) > 1:
        #             wind_farm.efficiency = wf.read_wind_efficiency_curve(
        #                 curve_name='dena_mean', plot=False)
        #             calculation_df_list.append(
        #                 modelchain_usage.power_output_cluster(
        #                     wind_farm, weather,
        #                     density_correction=False,
        #                     wake_losses_method='wind_efficiency_curve',
        #                     smoothing=True,
        #                     wind_speed_model='interpolation_extrapolation',
        #                     roughness_length=weather[
        #                         'roughness_length'][0].mean()).to_frame(
        #                     name='{0}_calculated_lin._interp.'.format(
        #                         wind_farm.object_name)))
        # if 'test_cluster' in approach_list:
        #     test_cluster = wtc.WindTurbineCluster('test', wind_farm_list)
        #     calculation_df_list.append(modelchain_usage.power_output_cluster(
        #         test_cluster, weather, density_correction=False,
        #         wake_losses_method=None, smoothing=True,
        #         block_width=0.5,
        #         standard_deviation_method='turbulence_intensity',
        #         smoothing_order='wind_farm_power_curves',
        #         roughness_length=weather[
        #             'roughness_length'][0].mean(),
        #         wind_speed_model='logarithmic').to_frame(
        #         name='{0}_calculated_test_cluster'.format(
        #             wind_farm.object_name)))
        # Join DataFrames - power output in MW - wind speed in m/s
        if (case == 'wind_speed_1' or case == 'wind_speed_2'):
            calculation_df = pd.concat(calculation_df_list, axis=1)
        else:
            calculation_df = pd.concat(
                calculation_df_list, axis=1) / (1 * 10 ** 6)
        # Add curtailment for Enertrag wind farm
        for column_name in list(calculation_df):
            if column_name.split('_')[1] == '9':
                curtailment = get_enertrag_curtailment_data(weather.index.freq)
                # Replace values of 0 with nan as they should not be considered
                # in the validation
                curtailment.replace(0.0, np.nan, inplace=True)
                # Add curtailment to data frame
                df = pd.concat([calculation_df[[column_name]], curtailment],
                               axis=1)
                calculation_df[column_name] = df[column_name] * df[
                    'curtail_rel']
        return calculation_df

    def get_time_series_df(weather_data_name):
        r"""
        If there are any values in restriction_list, the columns containing
        these strings are dropped. This takes place after dumping.

        """
        time_series_filename = os.path.join(
            time_series_df_folder, 'time_series_df_{0}_{1}_{2}.p'.format(
                case, weather_data_name, year))
        if pickle_load_time_series_df:
            time_series_df = pickle.load(open(time_series_filename, 'rb'))
        elif csv_load_time_series_df:
            time_series_df = pd.read_csv(time_series_filename.replace('.p',
                                                                      '.csv'))
            pickle.dump(time_series_df, open(time_series_filename, 'wb'))
        else:
            # Get validation and calculated data
            calculation_df = get_calculated_data(weather_data_name)
            validation_df = get_validation_data(
                frequency=calculation_df.index.freq)
            # Join data frames
            time_series_df = pd.concat([validation_df, calculation_df], axis=1)
            # Set value of measured series to nan if respective calculated
            # value is nan and the other way round
            column_name_lists = [
                [name for name in list(time_series_df) if wf_name in name] for
                wf_name in wind_farm_names]
            for column_name in column_name_lists:
                # Nans of calculated data to measured data
                time_series_df.loc[:, column_name[0]].loc[
                    time_series_df.loc[:, column_name[1]].loc[
                        time_series_df.loc[
                            :, column_name[1]].isnull() == True].index] = np.nan
                # Nans of calculated data to measured data
                for i in range(len(column_name) - 1):
                    time_series_df.loc[:, column_name[i+1]].loc[
                        time_series_df.loc[:, column_name[0]].loc[
                            time_series_df.loc[
                            :, column_name[0]].isnull() == True].index] = np.nan
            # Only keep columns within the right year
            time_series_df['boolean'] = (time_series_df.index.year == year)
            time_series_df = time_series_df.loc[
               time_series_df.loc[time_series_df['boolean']].index].drop(
                    ['boolean'], axis=1)
            pickle.dump(time_series_df, open(time_series_filename, 'wb'))
        if csv_dump_time_series_df:
            time_series_df.to_csv(time_series_filename.replace('.p', '.csv'))
        # Drop columns that contain at least one item of `restriction_list` in
        # their name
        drop_list = []
        for restriction in restriction_list:
            drop_list.extend(
                [column_name for column_name in list(time_series_df) if
                 restriction in column_name])
        time_series_df.drop([column_name for column_name in drop_list],
                            axis=1, inplace=True)
        return time_series_df

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


    def join_dictionaries(list_of_dicts): # TODO: delete if not needed
        # Start with copy of first entry
        z = list_of_dicts[0].copy()
        # Update with the remaining dictionaries
        for i in range(len(list_of_dicts) - 1):
            z.update(list_of_dicts[i + 1])
        return z


    # ---------------------------- Data Evaluation -------------------------- #
    # Create list of wind farm names
    if 'single' in validation_data_list:
        wind_farm_names = [data['object_name'] for data in return_wind_farm_data(
            single=True)]
    else:
        wind_farm_names = [data['object_name'] for
                           data in return_wind_farm_data()]
    # Initialize dictionary for validation objects
    val_obj_dict = initialize_dictionary(dict_type='validation_objects')
    # Initialize dict for annual energy output of each weather data set
    annual_energy_dicts = {weather_data_name: None
                           for weather_data_name in weather_data_list}
    for weather_data_name in weather_data_list:
        time_series_df = get_time_series_df(weather_data_name)
        if time_period is not None:
            # TODO: is now for all wind farms. if decided to use time period for argenetz -
            # TODO: only apply on arge (put values to nan, that are outside the period)- leave this for times of day evaluation
            time_series_df = tools.select_certain_time_steps(time_series_df,
                                                             time_period)
        # Create list of time series data frames (for each wind farm for each
        # approach) - measured and calculated data
        time_series_df_parts = [
            time_series_df.loc[:, [
                column_name for column_name in list(time_series_df)
                if wf_name in column_name]] for wf_name in wind_farm_names
            if wf_name not in restriction_list]
        time_series_pairs = [time_series_df.loc[:, [
            '{0}_measured'.format(wf_name), '{0}_calculated_{1}'.format(
                wf_name, approach)]] for
            wf_name in wind_farm_names for approach in approach_list if
            '{0}_calculated_{1}'.format(wf_name, approach) in list(
                time_series_df)]

        # Initialize dictionary for annual energy output
        annual_energy_dict_weather = initialize_dictionary(
            dict_type='annual_energy', time_series_pairs=time_series_pairs)
        if ('annual_energy_approaches' in latex_output or
                'annual_energy_weather' in latex_output):
            # Write annual energy outputs and deviations into
            # `annual_energy_dict`
            for time_series_df_part in time_series_df_parts:
                wf_string = '_'.join(
                    list(time_series_df_part)[0].split('_')[:2])
                # Measured annual energy output
                measured_output = tools.annual_energy_output(
                    time_series_df_part.loc[:,
                                            '{0}_measured'.format(wf_string)])
                annual_energy_dict_weather[
                    wf_string]['measured_annual_energy'] = measured_output
                # Calculated annual energy output and deviation from measured
                # in %
                for column_name in list(time_series_df_part):
                    if column_name != '{0}_measured'.format(wf_string):
                        approach_string = '_'.join(column_name.split('_')[3:])
                        calculated_output = tools.annual_energy_output(
                            time_series_df_part.loc[:,'{0}_calculated_{1}'.format(
                                wf_string, approach_string)])
                        annual_energy_dict_weather[wf_string][
                            approach_string]['[MWh]'] = (
                            calculated_output)
                        annual_energy_dict_weather[wf_string][
                            approach_string]['deviation [%]'] = (
                            (calculated_output - measured_output) /
                            measured_output * 100)
            # Add dictionary to `annual_energy_dicts`
            annual_energy_dicts[weather_data_name] = annual_energy_dict_weather
        for time_series_pair in time_series_pairs:
            wf_string = '_'.join(list(time_series_pair)[0].split('_')[:2])
            approach_string = '_'.join(
                list(time_series_pair)[1].split('_')[3:])
            if 'half_hourly' in output_methods:
                if weather_data_name == 'open_FRED':
                    val_obj_dict[weather_data_name]['half_hourly'][
                        approach_string].append(ValidationObject(
                            object_name=wf_string, data=time_series_pair,
                            output_method='half_hourly',
                            weather_data_name=weather_data_name,
                            approach=approach_string,
                            min_periods_pearson=min_periods_pearson))
            if 'hourly' in output_methods:
                if weather_data_name == 'open_FRED':
                    hourly_series = tools.resample_with_nan_theshold(
                        df=time_series_pair, frequency='H',
                        threshold=get_threshold('H',
                                                time_series_pair.index.freq.n))
                else:
                    hourly_series = time_series_pair
                val_obj_dict[weather_data_name]['hourly'][
                    approach_string].append(ValidationObject(
                        object_name=wf_string, data=hourly_series,
                        output_method='hourly',
                        weather_data_name=weather_data_name,
                        approach=approach_string,
                        min_periods_pearson=min_periods_pearson))
            if 'monthly' in output_methods:
                monthly_series = tools.resample_with_nan_theshold(
                    df=time_series_pair, frequency='M',
                    threshold=get_threshold('M',
                                            time_series_pair.index.freq.n))
                val_obj_dict[weather_data_name]['monthly'][
                    approach_string].append(ValidationObject(
                        object_name=wf_string, data=monthly_series,
                        output_method='monthly',
                        weather_data_name=weather_data_name,
                        approach=approach_string,
                        min_periods_pearson=min_periods_pearson))
        # Delete entry in dict if half_hourly resolution not possible
        if (time_series_pairs[0].index.freq == 'H' and
                'half_hourly' in val_obj_dict[weather_data_name]):
            del val_obj_dict[weather_data_name]['half_hourly']

        ###### Visualization ######
        # Define folder
        if (case == 'wind_speed_1' or case == 'wind_speed_2'):
            folder = 'wind_speed'
        elif (case == 'single_turbine_1' or case == 'single_turbine_2'):
            folder = 'single_turbine'
        else:
            folder = ''
        # Define y label add on
        if (case == 'wind_speed_1' or case == 'wind_speed_2'):
            examined_value = 'wind speed'
            y_label_add_on = '{0} in m/s'.format(examined_value)
        else:
            examined_value = 'power output'
            y_label_add_on = '{0} in MW'.format(examined_value)

        if 'feedin_comparison' in visualization_methods:
            # Specify folder and title add on for saving the plots
            if feedin_comparsion_all_in_one:
                plot_dfs = time_series_df_parts
                approach_string = 'multiple'
            else:
                plot_dfs = time_series_pairs
                approach_string = None
            for plot_df in plot_dfs:
                # Specify save folder and title add on
                if time_period is not None:
                    add_on = (
                        '{0}_{1}'.format(time_period[0], time_period[1]))
                    title_add_on = ' time of day: {0}:00 - {1}:00'.format(
                        time_period[0], time_period[1])
                else:
                    add_on = 'None'
                    title_add_on = ''
                save_folder = 'Plots/{0}/'.format(folder)
                for method in output_methods:
                    if approach_string != 'multiple':
                        approach_string = '_'.join(list(plot_df)[1].split(
                            '_')[3:])
                    wf_string = '_'.join(list(plot_df)[0].split(
                        '_')[:2])
                    for start_end in start_end_list:
                        if (method == 'monthly' and start_end[0] is not None):
                            # Do not plot
                            pass
                        elif (method == 'half_hourly' and
                                weather_data_name == 'MERRA'):
                            pass
                        else:
                            visualization_tools.plot_feedin_comparison(
                                data=plot_df, method=method,
                                filename=(
                                    save_folder +
                                    '{0}_{1}_feedin_{2}_{3}_{4}_{5}_{6}_{7}{8}.png'.format(
                                        case, method, wf_string, year,
                                        weather_data_name, add_on,
                                        approach_string,
                                        (start_end[0].split(':')[0] if
                                         start_end[0] else ''),
                                        (start_end[1].split(':')[0] if
                                         start_end[0] else ''))),
                                title=(
                                    '{0} {1} of {2} calculated with {3} data\n in {4} ({5} approach)'.format(
                                        method.replace('_', ' '),
                                        examined_value, wf_string,
                                        weather_data_name, year,
                                        approach_string) + title_add_on),
                                tick_label=None, start=start_end[0],
                                end=start_end[1],
                                y_label_add_on=y_label_add_on)

        if 'plot_correlation' in visualization_methods:
            for time_series_pair in time_series_pairs:
                # Specify save folder and title add on
                if time_period is not None:
                    add_on = (
                        '{0}_{1}'.format(time_period[0], time_period[1]))
                    title_add_on = ' time of day: {0}:00 - {1}:00'.format(
                        time_period[0], time_period[1])
                else:
                    add_on = 'None'
                    title_add_on = ''
                save_folder = 'Plots/{0}/'.format(folder)
                for method in output_methods:
                    if (method == 'half_hourly' and
                            weather_data_name == 'MERRA'):
                        # Do not plot
                        pass
                    else:
                        approach_string = '_'.join(
                            list(time_series_pair)[1].split('_')[3:])
                        wf_string = '_'.join(
                            list(time_series_pair)[0].split('_')[:2])
                        visualization_tools.plot_correlation(
                            data=time_series_pair, method=method,
                            filename=(
                                save_folder +
                                '{0}_{1}_Correlation_{1}_{2}_{3}_{4}_{5}_{6}.png'.format(
                                    case, method, wf_string, year,
                                    weather_data_name, approach_string,
                                    add_on)),
                            title=(
                                '{0} {1} of {2} calculated with {3} data\n in {4} ({5} '.format(
                                    method.replace('_', ' '), examined_value,
                                    wf_string, weather_data_name, year,
                                    approach_string) +
                                'approach)' + title_add_on),
                            color='darkblue', marker_size=3,
                            y_label_add_on=y_label_add_on)

    #         if 'box_plots' in visualization_methods:
    #             # Store all bias time series of a validation set in one
    #             # DataFrame for Boxplot
    #             bias_df = pd.DataFrame()
    #             for validation_object in validation_set:
    #                 if 'all' not in validation_object.object_name:
    #                     df_part = pd.DataFrame(
    #                         data=validation_object.bias,
    #                         columns=[validation_object.object_name])
    #                     bias_df = pd.concat([bias_df, df_part], axis=1)
    #             # Specify filename
    #             filename = (save_folder +
    #                         '{0}_Boxplot_{1}_{2}_{3}_{4}.pdf'.format(
    #                             validation_set[0].output_method, year,
    #                             validation_data_name,
    #                             weather_data_name, approach))
    #             title = (
    #                 'Deviation of ' +
    #                 '{0} {1} from {2}\n in {3} ({4} approach)'.format(
    #                     weather_data_name,
    #                     validation_set[0].output_method.replace('_',
    #                                                             ' '),
    #                     validation_data_name, year, approach) +
    #                 title_add_on)
    #             visualization_tools.box_plots_bias(
    #                 bias_df, filename=filename, title=title)

    # ---------------------------------- LaTeX Output --------------------------- #
    path_latex_tables = os.path.join(os.path.dirname(__file__),
                                     latex_tables_folder)
    if time_period is not None:
        filename_add_on = '_{0}_{1}'.format(time_period[0], time_period[1])
    else:
        filename_add_on = ''


    # Write latex output
    latex_tables.write_latex_output(
        latex_output=latex_output, weather_data_list=weather_data_list,
        approach_list=approach_list, restriction_list=restriction_list,
        val_obj_dict=val_obj_dict, annual_energy_dicts=annual_energy_dicts,
        wind_farm_names=wind_farm_names, key_figures_print=key_figures_print,
        output_methods=output_methods, path_latex_tables=path_latex_tables,
        filename_add_on=filename_add_on, year=year, case=case)

    # ------------------------------- Extra plots ------------------------------- #
    # if 'annual_bars_weather' in extra_plots:
    #     years = [2015, 2016]
    #     if 'annual_energy_output' not in output_methods:
    #         raise ValueError("'annual_energy_output' not in `output_methods` - " +
    #                          "cannot generate 'annual_bars_weather' plot")
    #     for approach in approach_list:
    #         for validation_data_name in validation_data_list:
    #             filenames = []
    #             for year in years:
    #                 validation_sets = []
    #                 filenames.extend(['validation_sets_{0}_{1}_{2}_{3}'.format(
    #                     year, weather_data_name,
    #                     validation_data_name, approach) +
    #                              '_annual_energy_output.p'
    #                              for weather_data_name in weather_data_list])
    #                 for filename in filenames:
    #                     if (approach in filename and 'annual_energy_output' in filename
    #                             and validation_data_name in filename
    #                             and str(year) in filename):
    #                         validation_sets.append(pickle.load(open(filename, 'rb')))
    #                     index = [year]
    #                     columns = [validation_data_name]
    #                     columns.extend([name for name in weather_data_list])
    #                     data = []

    logging.info("--- Simulation with case {0} in year {1} end ---".format(
        case, year))

if __name__ == "__main__":
    for year in years:
        for case in cases:
            run_main(case, year)