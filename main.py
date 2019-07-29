# Imports from Windpowerlib
from windpowerlib import wind_farm as wf

# Imports from lib_validation
import tools
from tools import preload_era5_weather
import modelchain_usage
from wind_farm_specifications import (get_joined_wind_farm_data,
                                      get_wind_farm_data)
from open_fred_weather_data import get_open_fred_data
from greenwind_data import (get_greenwind_data,
                            get_first_row_turbine_time_series)
from config_simulation_cases import get_configuration
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
    'wind_speed_1',
    'power_output_1',  #
    'single_turbine_1'  # Single Turbine Model
]

temporal_resolution = 'H'  # temporal resolution of time series at validation.
    # not fully implemented yet - only use 'H'
    # F.e.: if you enter open_FRED weather with half-hourly resolution -->
    # feed-in is calulated in half-hourly resolution and resampled to
    # `temporal_resolution`

min_periods_pearson = None  # Minimum amount of periods for correlation.

# Pickle load time series data frame - if one of the below pickle_load options
# is set to False, `pickle_load_time_series_df` is automatically set to False
pickle_load_time_series_df = False

pickle_load_open_fred = True
pickle_load_era5 = True
pickle_load_greenwind = True
pickle_load_wind_farm_data = True
pickle_load_wind_efficiency_curves = False

csv_load_time_series_df = False  # Load time series data frame from csv dump
if pickle_load_time_series_df:
    csv_dump_time_series_df = False
else:
    csv_dump_time_series_df = True  # Dump df as csv

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

# Threshold factor. F.e. if threshold_factor is 0.5 resampling is only done, if
# more than 50 percent of the values are not nan.
threshold_factor = 0.5

# If pickle_load options not all True:
if (not pickle_load_open_fred or not
        pickle_load_greenwind or not pickle_load_wind_farm_data):
    pickle_load_time_series_df = False


def run_main(case, parameters, year):
    logging.info("--- Simulation with case {0} in year {1} starts ---".format(
        case, year))

    # Get parameters
    restriction_list = parameters['restriction_list']
    validation_data_list = parameters['validation_data_list']
    weather_data_list = parameters['weather_data_list']
    approach_list = parameters['approach_list']

    # ------------------------ Validation Feedin Data ----------------------- #
    def get_threshold(out_frequency, original_resolution):
        if out_frequency == 'H' or out_frequency == '60T':
            resolution = 60
        elif out_frequency == 'M':
            resolution = 31 * 24 * 60
        else:
            resolution = out_frequency.n
        if original_resolution == 1:
            original_resolution = 60
        return resolution / original_resolution * threshold_factor

    def get_validation_data():
        r"""
        Writes all measured power output time series into one DataFrame.

        All time series are resampled to the given `temporal_resolution`.

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
        if 'single' in validation_data_list:
            filename = os.path.join(
                os.path.dirname(__file__), validation_pickle_folder,
                'greenwind_data_first_row_{0}.p'.format(year))
            single_data = get_first_row_turbine_time_series(  # todo check frequency!!
                year=year, filter_errors=True, print_error_amount=False,
                pickle_filename=filename, pickle_load_raw_data=True,
                pickle_load=pickle_load_greenwind,
                filename_raw_data=os.path.join(
                    validation_pickle_folder,
                    'greenwind_data_{0}.p'.format(year)),
                case=case)
            single_data = single_data[[col for
                                       col in list(single_data) if
                                       'power_output' in col]].rename(
                columns={column: column.replace(
                    'power_output', 'measured').replace(
                    'wf', 'single') for column in list(single_data)})
            # Resample the DataFrame columns with `frequency` and add to list
            threshold = get_threshold(temporal_resolution,
                                      single_data.index.freq.n)
            validation_df_list.append(tools.resample_with_nan_theshold(
                df=single_data, frequency=temporal_resolution,
                threshold=threshold))
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
            threshold = get_threshold(temporal_resolution,
                                      turbine_power_output.index.freq.n)
            validation_df_list.append(tools.resample_with_nan_theshold(
                df=turbine_power_output, frequency=temporal_resolution,
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
        return validation_df_db_format

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
        else:
            filenames = ['farm_specification_{0}_{1}.p'.format(
                validation_data_name.replace('GreenWind', 'greenwind'), year)
                for validation_data_name in validation_data_list]
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
        if weather_data_name == 'open_FRED':
            if not pickle_load_open_fred:
                fred_path = '~/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_{0}_sh.csv'.format(year) # todo adapt
                get_open_fred_data(
                    filename=fred_path, pickle_filename=filename_weather,
                    pickle_load=False)
        if weather_data_name == 'ERA5':
            if not pickle_load_era5:
                era5_path = '~/virtualenvs/lib_validation/lib_validation/dumps/weather/era5_wind_bb_{}.csv'.format(year)
                preload_era5_weather(
                    filename=era5_path, pickle_filename=filename_weather,
                    pickle_load=False)
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
                # temperature_heights=temperature_heights,
            )
            if 'log_100' in approach_list:
                calculated_value = modelchain_usage.wind_speed_to_hub_height(
                    wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                    weather_df=weather, wind_speed_model='logarithmic',
                    obstacle_height=0)
                df = calculated_value.to_frame(name='wind_speed')
                # If necessary resample to `temporal_resolution`
                if not df.index.freq == temporal_resolution:
                    df = tools.resample_with_nan_theshold(
                        df=df, frequency=temporal_resolution,
                        threshold=get_threshold(
                            out_frequency=temporal_resolution,
                            original_resolution=df.index.freq.n))
                df['turbine_or_farm'] = wind_farm.name
                df['approach'] = 'log_100'
                calculation_df_db_format = pd.concat(
                    [calculation_df_db_format, df], axis=0)
            if 'log_80' in approach_list and weather_data_name != 'ERA5':
                modified_weather = weather[['roughness_length', 'wind_speed']]
                modified_weather.drop([100, 120, 10], axis=1, level=1,
                                      inplace=True)
                calculated_value = modelchain_usage.wind_speed_to_hub_height(
                        wind_turbine_fleet=wind_farm.wind_turbine_fleet,
                        weather_df=modified_weather,
                        wind_speed_model='logarithmic',
                        obstacle_height=0)
                df = calculated_value.to_frame(name='wind_speed')
                # If necessary resample to `temporal_resolution`
                if not df.index.freq == temporal_resolution:
                    df = tools.resample_with_nan_theshold(
                        df=df, frequency=temporal_resolution,
                        threshold=get_threshold(
                            out_frequency=temporal_resolution,
                            original_resolution=df.index.freq.n))
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
                df = calculated_value.to_frame(name='wind_speed')
                # If necessary resample to `temporal_resolution`
                if not df.index.freq == temporal_resolution:
                    df = tools.resample_with_nan_theshold(
                        df=df, frequency=temporal_resolution,
                        threshold=get_threshold(
                            out_frequency=temporal_resolution,
                            original_resolution=df.index.freq.n))
                df['turbine_or_farm'] = wind_farm.name
                df['approach'] = 'log_10'
                calculation_df_db_format = pd.concat(
                    [calculation_df_db_format, df], axis=0)

            # --- wind speed definition for next cases --- #
            if (case == 'wind_farm_3' or case == 'weather_single_turbine_2' or
                    case == 'wake_losses_1'):
                print('unused lines?')
                # # Use wind speed from first row GreenWind data as weather data
                # single_data_raw = get_first_row_turbine_time_series(
                #     year=year, filter_errors=True, print_error_amount=False,
                #     pickle_filename=os.path.join(
                #         os.path.dirname(__file__), 'dumps/validation_data',
                #         'greenwind_data_first_row_{0}.p'.format(year)),
                #     pickle_load=pickle_load_greenwind, case=case)
                # wind_speed = single_data_raw[['wf_{}_wind_speed'.format(
                #     wind_farm.name.split('_')[1])]]
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
                # temporal resolution as desired temporal resolution
                wind_speed = (
                    wind_speed if
                    wind_speed.index.freq == temporal_resolution else
                    tools.resample_with_nan_theshold(
                        df=wind_speed, frequency=temporal_resolution,
                        threshold=get_threshold(
                            out_frequency=temporal_resolution,
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
                df = calculated_value.to_frame(name='feedin')
                # If necessary resample to `temporal_resolution`
                if not df.index.freq == temporal_resolution:
                    df = tools.resample_with_nan_theshold(
                        df=df, frequency=temporal_resolution,
                        threshold=get_threshold(
                            out_frequency=temporal_resolution,
                            original_resolution=df.index.freq.n))
                df['turbine_or_farm'] = wind_farm.name
                df['approach'] = 'p-curve'
                calculation_df_db_format = pd.concat(
                    [calculation_df_db_format, df], axis=0)

        # Join DataFrames - power output in MW - wind speed in m/s
        if not 'wind_speed' in case:
            calculation_df_db_format['feedin'] = (
                    calculation_df_db_format['feedin'] / (1 * 10 ** 6))
        return calculation_df_db_format.dropna()

    def get_time_series_df(weather_data_name, wind_farm_data_list):
        r"""

        """
        time_series_filename = os.path.join(
            time_series_dump_folder, 'time_series_df_{0}_{1}_{2}.p'.format(
                case, weather_data_name, year))
        csv_filename = time_series_filename.replace('.p', '.csv')
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
            calculation_df_db_format = get_calculated_data(
                weather_data_name, wind_farm_data_list)
            validation_df_db_format = get_validation_data()
            # Join data frames
            time_series_df_db_format = pd.merge(
                calculation_df_db_format.reset_index(),
                validation_df_db_format.reset_index().rename(
                    columns={'timeindex': 'time'}),
                on=['time', 'turbine_or_farm']).set_index('time')
            # Set value of measured series to nan if respective calculated
            # value is nan and the other way round and drop nans
            sim_name = 'wind_speed' if 'wind_speed' in case else 'feedin'
            val_name = 'wind_speed_val' if 'wind_speed' in case else 'feedin_val'
            time_series_df_db_format[sim_name].loc[
                time_series_df_db_format[
                    val_name].isnull() == True] = np.nan
            time_series_df_db_format[val_name].loc[
                time_series_df_db_format[
                    sim_name].isnull() == True] = np.nan
            time_series_df_db_format.dropna(inplace=True)
        if csv_dump_time_series_df:
            time_series_df_db_format.to_csv(csv_filename)
        return time_series_df_db_format

    ###########################################################################
    # ---------------------------- Data Evaluation -------------------------- #
    ###########################################################################
    # Get wind farm data
    if 'single' in validation_data_list:
        wind_farm_data_list = return_wind_farm_data(single=True)
    elif 'gw_wind_speeds' in validation_data_list:
        wind_farm_data_list = return_wind_farm_data(single=False,
                                                    gw_wind_speeds=True)
    else:
        wind_farm_data_list = return_wind_farm_data()

    for weather_data_name in weather_data_list:
        time_series_df_db_format = get_time_series_df(
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

    logging.info("--- Simulation with case {0} in year {1} end ---".format(
        case, year))

if __name__ == "__main__":
    for case in cases:
        # Get parameters from config file (they are set below)
        parameters = get_configuration(case)
        years = parameters['years']
        for year in years:
            run_main(case=case, year=year, parameters=parameters)
