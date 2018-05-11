from windpowerlib import wind_farm, wake_losses

from greenwind_data import (get_first_row_turbine_time_series,
                            get_greenwind_data)
from wind_farm_specifications import get_wind_farm_data

# Other imports
from matplotlib import pyplot as plt
import os
import pandas as pd
import numpy as np
import math
import pickle

# Parameters
wind_farm_pickle_folder = os.path.join(os.path.dirname(__file__),
                                       'dumps/wind_farm_data')
validation_pickle_folder = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'dumps/validation_data'))


def evaluate_power_efficiency_curves(years, pickle_filename_add_on,
                                    drop_higher_one=False, plot=True,
                                    exact_degrees=False, csv_folder=''):
    for year in years:
        # Get wind farm data
        wind_farm_data_gw = get_wind_farm_data(
            'farm_specification_greenwind_{0}.p'.format(year),
            wind_farm_pickle_folder, pickle_load=True)
        # Get Greenwind data
        greenwind_data = get_greenwind_data(
            year, pickle_load=True, resample=False,
            filename=os.path.join(
                validation_pickle_folder,
                'greenwind_data_{0}_raw_resolution.p'.format(year)))   #
        # Select aggregated power output of wind farm (rename)
        greenwind_power_data = greenwind_data[[
            '{0}_power_output'.format(data['name']) for
            data in wind_farm_data_gw]]
        if exact_degrees:
            pickle_filename_add_on_2 = '_exact_degrees'
        else:
            pickle_filename_add_on_2 = ''
        pickle_filename = os.path.join(
            os.path.dirname(__file__), 'dumps/validation_data',
            'greenwind_data_first_row_{0}{1}{2}.p'.format(
                year, pickle_filename_add_on, pickle_filename_add_on_2))
        gw_first_row = get_first_row_turbine_time_series(
            year=year, pickle_load=True,
            pickle_filename=pickle_filename, resample=False, frequency='30T',
            threshold=2)
        if greenwind_power_data.index.freq != gw_first_row.index.freq:
            raise ValueError('Attention - different frequencies: ' +
                             'wf data: {}, first row data: {}'.format(
                                 greenwind_power_data.index.freq,
                                 gw_first_row.index.freq))
        if exact_degrees:
            folder = 'exact_degrees/'
            title_add_on_3 = ' exact degrees'
        else:
            folder = ''
            title_add_on_3 = ''
        if 'mean_wind_dir' in pickle_filename:
            folder += 'mean_wind_dir/'
        if 'bias' in pickle_filename:
            folder += 'bias/'
        if 'dir_real' in pickle_filename:
            wfs = ['BS', 'BNW']
            numbers = [14, 2]
            title_add_on = 'real wind directions'
            folder += 'real_wind_dir'
        elif ('_3' in pickle_filename and 'real' not in pickle_filename):
            wfs = ['BE', 'BS']
            numbers = [9, 14]
            title_add_on = 'gondel pos. north west'
            folder += 'gondel_position_north_west'
        elif '_3_real' in pickle_filename:
            wfs = ['BS']
            numbers = [14]
            title_add_on = 'real wind dir. north west'
            folder += 'real_wind_dir_north_west'
        elif '_highest_power' in pickle_filename:
            wfs = ['BE', 'BS', 'BNW']
            numbers = [9, 14, 2]
            title_add_on = 'highest power'
            folder += 'highest_power'
        else:
            wfs = ['BE', 'BS', 'BNW']
            numbers = [9, 14, 2]
            title_add_on = 'gondel position'
            folder += 'gondel_position'
        for wf, number_of_turbines in zip(wfs, numbers):
            cols_first_row = [col for col in gw_first_row.columns if wf in col]
            first_row_data = gw_first_row[cols_first_row].rename(columns={
                [col for col in cols_first_row if 'wind_speed' in col][0]:
                'wind_speed',
                [col for col in cols_first_row if 'power_output' in col][0]:
                'single_power_output'})
            cols_wf = [col for col in greenwind_power_data.columns if wf in col]
            wind_farm_power_output = greenwind_power_data[cols_wf].rename(columns={
                'wf_{}_power_output'.format(wf): 'wind_farm_power_output'})
            df = pd.concat([first_row_data, wind_farm_power_output], axis=1)
            # df.index = df.index.tz_convert('Europe/Berlin')
            # Rename columns to standard names
            # df.rename
            # Set values of columns to nan if one of the other columns' value is nan
            column_names = df.columns
            for column_name in column_names:
                alter_cols = [col for col in column_names if
                              col != column_name]
                for col in alter_cols:
                    # Values in alter_cols[i] to nan where values in column_name nan
                    df.loc[:, col].loc[df.loc[:, column_name].loc[
                        df.loc[:,
                        column_name].isnull() == True].index] = np.nan
            df.dropna(inplace=True)
            # Get maximum wind speed rounded to the next integer
            maximum_v_int = math.ceil(df['wind_speed'].max())
            # Get maximum standard wind speed rounded to next 0.5 m/s
            maximum_v_std = (maximum_v_int if
                             maximum_v_int - df['wind_speed'].max() < 0.5 else
                             maximum_v_int - 0.5)
            # Add v_std (standard wind speed) column to data frame
            df['v_std'] = np.nan
            standard_wind_speeds = np.arange(0.0, maximum_v_std + 0.5, 0.5)
            for v_std in standard_wind_speeds:
                # Set standard wind speeds depending on wind_speed column value
                indices = df.loc[(df.loc[:, 'wind_speed'] <= v_std) &
                                 (df.loc[:, 'wind_speed'] > (
                                 v_std - 0.5))].index
                df['v_std'].loc[indices] = v_std
            df['efficiency'] = df['wind_farm_power_output'] / (
                number_of_turbines * df['single_power_output'])
            ##### This is only used teporaryly: todo
            higher_one_df = df.loc[df['efficiency'] > 1.0]
            v_std_amount = higher_one_df.groupby(['v_std']).agg(['count'])[
                'efficiency']
            highest = get_first_row_turbine_time_series(
                year=year, pickle_load=True,
                pickle_filename=os.path.join(
                    os.path.dirname(__file__), 'dumps/validation_data',
                    'greenwind_data_first_row_{0}_highest_powerwith_info.p'.format(
                        year)), resample=False, frequency='30T', threshold=2)
            highest_wf_cols = [col for col in list(highest) if
                               (wf in col and 'wind_speed' not in col)]
            highest_wf = highest[highest_wf_cols]
            first_row = get_first_row_turbine_time_series(
            year=year, pickle_load=True,
            pickle_filename=pickle_filename.replace('.p', 'with_info.p'),
                resample=False, frequency='30T', threshold=2, add_info=True)
            first_row_wf_cols = [col for col in list(first_row) if wf in col]
            first_row_wf = first_row[first_row_wf_cols]
            evaluation_df = pd.concat([df, highest_wf, first_row_wf], axis=1)
            if exact_degrees:
                add_string = 'exact_degrees'
            else:
                add_string = ''
            evaluation_df.to_csv(os.path.join(
                csv_folder, 'evaluation_power_eff_curve_wf_{}_{}_{}.csv'.format(
                    wf, year, add_string)))
            v_std_amount.to_csv(os.path.join(
                csv_folder, 'higher_one_amount_wf_{}_{}_{}.csv'.format(
                    wf, year, add_string)))
            #####
            if drop_higher_one:
                # Set efficiency to nan where it is greater than 1.0
                indices = df[df.loc[:, 'efficiency'] > 1.0].index
                title_add_on_2 = ' > 1 dropped: {} of {}'.format(
                    len(indices),
                    len(df[df.loc[:, 'efficiency'] != np.nan].index))
                df['efficiency'].loc[indices] = np.nan
                filename_add_one = '_drop_higher_one'
            else:
                title_add_on_2 = ''
                filename_add_one = ''
            df.set_index('v_std', inplace=True)
            df2 = df[['efficiency']]
            df2 = df2.groupby(df.index).mean()

            empty_curve = pd.DataFrame([
                np.nan for i in range(len(standard_wind_speeds))],
                index=standard_wind_speeds)
            efficiency_curve = pd.concat([empty_curve, df2], axis=1)
            efficiency_curve.drop([col for col in efficiency_curve.columns if
                                   col != 'efficiency'], axis=1, inplace=True)
            # Interpolate between values
            efficiency_curve.interpolate(method='index', inplace=True)
            appendix = pd.DataFrame([
                np.nan for i in np.arange(efficiency_curve.index[-1] + 0.5, 26.0, 0.5)],
                index= np.arange(efficiency_curve.index[-1] + 0.5, 26.0, 0.5))
            efficiency_curve = pd.concat([efficiency_curve, appendix])
            efficiency_curve.drop([col for col in efficiency_curve.columns if
                                   col != 'efficiency'], axis=1, inplace=True)
            efficiency_curve.fillna(1.0, inplace=True)
            dena_mean_curve = wake_losses.get_wind_efficiency_curve('dena_mean')
            dena_mean_curve.set_index('wind_speed', inplace=True)
            dena_mean_curve.rename(columns={'efficiency': 'dena mean curve'},
                                   inplace=True)
            if plot:
                fig, ax = plt.subplots()
                efficiency_curve.plot(ax=ax, legend=True)
                dena_mean_curve.plot(ax=ax, legend=True)
                plt.title('WF {} --- {}{}{}'.format(
                    wf, title_add_on,  title_add_on_2, title_add_on_3))
                plt.ylabel('Efficiency')
                plt.xlabel('Wind speed')
                fig.savefig(os.path.join(
                    os.path.dirname(__file__),
                    '../../../User-Shares/Masterarbeit/Latex/inc/images/evaluation_wind_eff_curves',
                    folder, 'Efficiency_curve_{}_{}{}'.format(
                        wf, year, filename_add_one)))
                plt.close()


def create_power_efficiency_curve(first_row_data, wind_farm_power_output,
                               number_of_turbines, drop_higher_one=True):
    r"""
    first_row_data : pd.DataFrame
        Measured power output and wind speed of first row single turbine in
        columns 'single_power_output' and 'wind_speed'.
    wind_farm_power_output : pd.DataFrame
        Measured power output of wind farm in column 'wind_farm_power_output'.
    number_of_turbines : integer
        Amount of turbines in wind farm
    drop_higher_one : boolean
        If True wind farm efficiencies > 1.0 are dropped before the averaging.

    """
    df = pd.concat([first_row_data, wind_farm_power_output], axis=1)
    # df.index = df.index.tz_convert('Europe/Berlin')
    # Rename columns to standard names
    # df.rename
    # Set values of columns to nan if one of the other columns' value is nan
    column_names = df.columns
    for column_name in column_names:
        alter_cols = [col for col in column_names if
                      col != column_name]
        for col in alter_cols:
            # Values in alter_cols[i] to nan where values in column_name nan
            df.loc[:, col].loc[df.loc[:, column_name].loc[
                df.loc[:,
                column_name].isnull() == True].index] = np.nan
    df.dropna(inplace=True)
    # Get maximum wind speed rounded to the next integer
    maximum_v_int = math.ceil(df['wind_speed'].max())
    # Get maximum standard wind speed rounded to next 0.5 m/s
    maximum_v_std = (maximum_v_int if
                     maximum_v_int - df['wind_speed'].max() < 0.5 else
                     maximum_v_int - 0.5)
    # Add v_std (standard wind speed) column to data frame
    df['v_std'] = np.nan
    standard_wind_speeds = np.arange(0.0, maximum_v_std + 0.5, 0.5)
    for v_std in standard_wind_speeds:
        # Set standard wind speeds depending on wind_speed column value
        indices = df.loc[(df.loc[:, 'wind_speed'] <= v_std) &
                         (df.loc[:, 'wind_speed'] > (
                             v_std - 0.5))].index
        df['v_std'].loc[indices] = v_std
    # Add column with calculated efficiency
    df['efficiency'] = df['wind_farm_power_output'] / (
        number_of_turbines * df['single_power_output'])
    if drop_higher_one:
        # Set efficiency to nan where it is greater than 1.0
        indices = df[df.loc[:, 'efficiency'] > 1.0].index
        df['efficiency'].loc[indices] = np.nan
    df.set_index('v_std', inplace=True)
    df2 = df[['efficiency']]
    df2 = df2.groupby(df.index).mean()
    empty_curve = pd.DataFrame([
        np.nan for i in range(len(standard_wind_speeds))],
        index=standard_wind_speeds)
    efficiency_curve = pd.concat([empty_curve, df2], axis=1)
    efficiency_curve.drop([col for col in efficiency_curve.columns if
                           col != 'efficiency'], axis=1, inplace=True)
    # Interpolate between values
    efficiency_curve.interpolate(method='index', inplace=True)
    appendix = pd.DataFrame([
        np.nan for i in
        np.arange(efficiency_curve.index[-1] + 0.5, 26.0, 0.5)],
        index=np.arange(efficiency_curve.index[-1] + 0.5, 26.0, 0.5))
    efficiency_curve = pd.concat([efficiency_curve, appendix])
    efficiency_curve.drop([col for col in efficiency_curve.columns if
                           col != 'efficiency'], axis=1, inplace=True)
    efficiency_curve.fillna(1.0, inplace=True)
    return efficiency_curve


def get_power_efficiency_curves(drop_higher_one=True, pickle_load=False,
                               filename='power_efficiency_curves.p',
                               highest_power_output=False):
    if highest_power_output:
        filename = '{}_{}'.format(filename.split('.')[0], 'highest_power.p')
    if pickle_load:
        power_efficiency_curves = pickle.load(open(filename, 'rb'))
    else:
        curves = {}
        power_efficiency_curves = pd.DataFrame()
        for year in [2015, 2016]:
            # Get wind farm data
            wind_farm_data_gw = get_wind_farm_data(
                'farm_specification_greenwind_{0}.p'.format(year),
                wind_farm_pickle_folder, pickle_load=True)
            # Get Greenwind data
            greenwind_data = get_greenwind_data(
                year, pickle_load=True, resample=False,
                filename=os.path.join(
                    validation_pickle_folder,
                    'greenwind_data_{0}_raw_resolution.p'.format(year)))  #
            # Select aggregated power output of wind farm (rename)
            greenwind_power_data = greenwind_data[[
                '{0}_power_output'.format(data['name']) for
                data in wind_farm_data_gw]]
            if highest_power_output:
                gw_first_row = get_first_row_turbine_time_series(
                    year=year, pickle_load=True,
                    pickle_filename= os.path.join(
                    os.path.dirname(__file__), 'dumps/validation_data',
                    'greenwind_data_first_row_{0}_highest_power.p'.format(
                        year)), resample=False, frequency='30T', threshold=2)
            elif '_weather_wind_speed_3_real' in filename:
                gw_first_row = get_first_row_turbine_time_series(
                    year=year, pickle_load=True,
                    pickle_filename=os.path.join(
                        os.path.dirname(__file__), 'dumps/validation_data',
                        'greenwind_data_first_row_{0}_weather_wind_speed_3_real.p'.format(
                            year)), resample=False, frequency='30T',
                    threshold=2)
            else:
                gw_first_row = get_first_row_turbine_time_series(
                    year=year, pickle_load=True,
                    pickle_filename=os.path.join(
                        os.path.dirname(__file__), 'dumps/validation_data',
                        'greenwind_data_first_row_{0}.p'.format(year)),
                    resample=False, frequency='30T', threshold=2)
            if greenwind_power_data.index.freq != gw_first_row.index.freq:
                raise ValueError('Attention - different frequencies: ' +
                                 'wf data: {}, first row data: {}'.format(
                                     greenwind_power_data.index.freq,
                                     gw_first_row.index.freq))
            if '_weather_wind_speed_3_real' in filename:
                wfs = ['BS']
                numbers = [14]
            else:
                wfs = ['BE', 'BS', 'BNW']
                numbers = [9, 14, 2]
            for wf, number_of_turbines in zip(wfs, numbers):
                cols_first_row = [col for col in gw_first_row.columns if
                                  wf in col]
                first_row_data = gw_first_row[cols_first_row].rename(columns={
                    [col for col in cols_first_row if 'wind_speed' in col][0]:
                        'wind_speed',
                    [col for col in cols_first_row if 'power_output' in col][
                        0]:
                        'single_power_output'})
                cols_wf = [col for col in greenwind_power_data.columns if
                           wf in col]
                wind_farm_power_output = greenwind_power_data[cols_wf].rename(
                    columns={
                        'wf_{}_power_output'.format(
                            wf): 'wind_farm_power_output'})
                if year == 2015:
                    curve = create_power_efficiency_curve(
                        first_row_data=first_row_data,
                        wind_farm_power_output=wind_farm_power_output,
                        number_of_turbines=number_of_turbines,
                        drop_higher_one=drop_higher_one)
                    curve.columns = ['efficiency 2015']
                    curves[wf] = curve
                elif year == 2016:
                    wf_curve = pd.concat([create_power_efficiency_curve(
                        first_row_data=first_row_data,
                        wind_farm_power_output=wind_farm_power_output,
                        number_of_turbines=number_of_turbines,
                        drop_higher_one=drop_higher_one), curves[wf]],
                        axis=1)
                    wf_curve = pd.DataFrame(
                        wf_curve.mean(axis=1), columns=['wf_{}'.format(wf)])
                    power_efficiency_curves = pd.concat([power_efficiency_curves, wf_curve], axis=1)
                else:
                    print('Adjust function!')
        pickle.dump(power_efficiency_curves, open(filename, 'wb'))
        power_efficiency_curves.to_csv(
            'helper_files/calculated_power_efficiency_curves.csv')
    return power_efficiency_curves


def plot_calculated_and_dena():
    calculated_curves = pd.read_csv(
        'helper_files/calculated_power_efficiency_curves.csv', index_col=0)
    calculated_curves.rename(
        columns={col: '{} power eff.'.format(col.replace('wf_', 'WF ')) for
                 col in calculated_curves.columns},
                             inplace=True)
    dena_mean_curve = wake_losses.get_wind_efficiency_curve('dena_mean')
    dena_mean_curve.set_index('wind_speed', inplace=True)
    dena_mean_curve.rename(columns={'efficiency': 'dena mean wind eff.'},
                           inplace=True)
    knorr_extreme = wake_losses.get_wind_efficiency_curve('knorr_extreme2')
    knorr_extreme.set_index('wind_speed', inplace=True)
    knorr_extreme.rename(columns={'efficiency': 'knorr extreme2 wind eff.'},
                           inplace=True)
    fig, ax = plt.subplots()
    dena_mean_curve.plot(ax=ax, legend=True)
    knorr_extreme.plot(ax=ax, legend=True)
    calculated_curves.plot(ax=ax, legend=True)
    plt.xlabel('Wind speed in m/s')
    plt.ylabel('Efficiency (power or  wind)')
    fig.savefig(os.path.join(
        os.path.dirname(__file__),
        '../../../User-Shares/Masterarbeit/Latex/inc/images/',
        'wind_efficiency_curves_calculated_dena_knorr.pdf'))
    plt.close()

def standardize_wind_eff_curves_dena_knorr(curve_names, plot=False):
    path = os.path.join(os.path.dirname(__file__), 'helper_files',
                        'wind_efficiency_curves_raw.csv')
    # Read all curves from file
    wind_efficiency_curves = pd.read_csv(path)
    # Create wind speed series with standard wind speeds in 0.5 m/s step size
    wind_speed = pd.Series(np.arange(0, 25.5, 0.5))
    # Initialize data frame for all wind efficiency curves
    eff_curves_df = pd.DataFrame()
    for curve_name in curve_names:
        # Get x values depending on curve name
        if 'dena' in curve_name:
            x_values = wind_efficiency_curves['x_dena']
        if 'knorr' in curve_name:
            x_values = wind_efficiency_curves['x_knorr']
        # Interpolate between the x values and create data frame
        efficiency = np.interp(
            wind_speed, x_values.dropna(),
            wind_efficiency_curves[curve_name].dropna())
        efficiency_curve = pd.DataFrame(data=[wind_speed.values,
                                              efficiency], ).transpose()
        efficiency_curve.columns = ['wind_speed', curve_name]
        efficiency_curve.set_index('wind_speed', inplace=True)
        eff_curves_df = pd.concat([eff_curves_df, efficiency_curve], axis=1)
        eff_curves_df.to_csv(
            os.path.join(os.path.dirname(__file__), 'helper_files',
                         'wind_efficiency_curves.csv'))
    if plot: # TODO add (outside) plot for all curves.
        eff_curves_df.plot(
            legend=True, title="Wind efficiency curves")
        plt.ylabel('Efficiency')
        plt.show()

if __name__ == "__main__":
    load_curves = False
    plot_curves = False
    evaluate_curves = True
    standardize_curves = False

    if load_curves:
        get_power_efficiency_curves(drop_higher_one=True, pickle_load=False,
                                   filename=os.path.join(
                                       os.path.dirname(__file__), 'dumps',
                                       'power_efficiency_curves.p'))

    if plot_curves:
        plot_calculated_and_dena()

    years = [
        2015,
        2016
    ]

    if evaluate_curves:
        plot = False
        mean_wind_dir = False
        bias = False
        drop_higher_one_list = [
            True,
            # False
        ]
        exact_degrees_list = [
            # True,
            False
        ]
        pickle_filename_add_ons = [
            '',
            # '_wind_dir_real',
            # '_weather_wind_speed_3', '_weather_wind_speed_3_real',
            # '_highest_power'
        ]
        csv_folder = os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/Tables/Evaluation/power_eff_curves')
        if mean_wind_dir:
            pickle_filename_add_ons = [item + 'mean_wind_dir' for
                                       item in pickle_filename_add_ons if
                                       'highest' not in item]
        if bias:
            pickle_filename_add_ons = [item + '_bias' for
                                       item in pickle_filename_add_ons if
                                       'highest' not in item]
        for drop_higher_one in drop_higher_one_list:
            for add_on in pickle_filename_add_ons:
                for exact_degrees in exact_degrees_list:
                    if (mean_wind_dir and exact_degrees):
                        pass
                    else:
                        if not (exact_degrees and '_highest_power' in add_on):
                            evaluate_power_efficiency_curves(
                                years=years, drop_higher_one=drop_higher_one,
                                pickle_filename_add_on=add_on,
                                exact_degrees=exact_degrees, plot=plot,
                                csv_folder=csv_folder)

    # --- standardize curves --- #
    if standardize_curves:
        # wind_farm.read_power_efficiency_curve(curve_name='dena_mean', plot=True) # TODO delete
        curve_names = ['dena_mean', 'knorr_mean', 'dena_extreme1',
        'dena_extreme2', 'knorr_extreme1', 'knorr_extreme2', 'knorr_extreme3']
        standardize_wind_eff_curves_dena_knorr(curve_names)
