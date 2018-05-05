# Imports from Windpowerlib
from windpowerlib import tools
from windpowerlib.power_curves import smooth_power_curve
from windpowerlib.wind_farm import WindFarm

# Imports from lib_validation
from wind_farm_specifications import initialize_turbines, get_wind_farm_data
import tools as lib_tools

# Other imports
from matplotlib import pyplot as plt
import os
import pandas as pd
import numpy as np

def plot_smoothed_pcs(standard_deviation_method, block_width,
                      wind_speed_range, turbines, weather_data_name,
                      grouped=False, mean_roughness_length=None,
                      turbulence_intensity=None, mean=0):
    for turbine in turbines:
        if standard_deviation_method == 'turbulence_intensity':
            if not turbulence_intensity:
                turbulence_intensity = tools.estimate_turbulence_intensity(
                    turbine.hub_height, mean_roughness_length)
        else:
            turbulence_intensity = None
        # Start figure with original power curve
        fig = plt.figure()
        wind_speeds = turbine.power_curve['wind_speed']
        p_values = turbine.power_curve['power'] / 1000
        p_values = p_values.append(pd.Series(0.0, index=[p_values.index[-1] + 1]))
        wind_speeds = wind_speeds.append(pd.Series(40.0, index=[wind_speeds.index[-1] + 1]))
        a, = plt.plot(wind_speeds, p_values, label='Original')
        # Get smoothed power curve
        if grouped is False:
            smoothed_power_curve = smooth_power_curve(
                turbine.power_curve.wind_speed, turbine.power_curve['power'],
                block_width=block_width,
                standard_deviation_method=standard_deviation_method,
                turbulence_intensity=turbulence_intensity,
                wind_speed_range=wind_speed_range, mean_gauss=mean)
            b, = plt.plot(smoothed_power_curve['wind_speed'],
                          smoothed_power_curve['power'] / 1000,
                          label='Smoothed')
            handles = [a, b]
        if grouped == 'wind_speed_range':
            handles = [a]
            for range in wind_speed_range:
                smoothed_power_curve = smooth_power_curve(
                    turbine.power_curve.wind_speed,
                    turbine.power_curve['power'], block_width=block_width,
                    standard_deviation_method=standard_deviation_method,
                    turbulence_intensity=turbulence_intensity,
                    wind_speed_range=range)
                handle, = plt.plot(
                    smoothed_power_curve['wind_speed'],
                    smoothed_power_curve['power'] / 1000,
                    label='Range {} m/s'.format(int(range)))
                handles.append(handle)
        if grouped == 'block_width':
            handles = [a]
            for width in block_width:
                smoothed_power_curve = smooth_power_curve(
                    turbine.power_curve.wind_speed,
                    turbine.power_curve['power'],
                    block_width=width,
                    standard_deviation_method=standard_deviation_method,
                    turbulence_intensity=turbulence_intensity,
                    wind_speed_range=wind_speed_range)
                handle, = plt.plot(smoothed_power_curve['wind_speed'],
                                   smoothed_power_curve['power'] / 1000,
                                   label='Block width {} m/s'.format(width))
                handles.append(handle)
        if grouped == 'std_dev':
            handles = [a]
            for std_dev_method in standard_deviation_method:
                if std_dev_method == 'turbulence_intensity':
                    turbulence_intensity = tools.estimate_turbulence_intensity(
                        turbine.hub_height, mean_roughness_length)
                else:
                    turbulence_intensity = None
                smoothed_power_curve = smooth_power_curve(
                    turbine.power_curve.wind_speed,
                    turbine.power_curve['power'],
                    block_width=block_width,
                    standard_deviation_method=std_dev_method,
                    turbulence_intensity=turbulence_intensity,
                    wind_speed_range=wind_speed_range)
                handle, = plt.plot(smoothed_power_curve['wind_speed'],
                                   smoothed_power_curve['power'] / 1000,
                                   label=std_dev_method.replace(
                                       'turbulence_intensity', 'TI').replace(
                                       'Staffell_Pfenninger', 'SP'))
                handles.append(handle)
        plt.ylabel('Power in kW')
        plt.xlabel('Wind speed in m/s')
        # plt.title(turbine.name)
        plt.legend(handles=handles)
        fig.savefig(os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/inc/images/power_curves/smoothed_pc',
            '{}_{}_{}_{}_blockwidth{}_range{}.pdf'.format(
                'single' if grouped is False else grouped, turbine.name,
                weather_data_name,standard_deviation_method.replace(
                    'turbulence_intensity', 'TI').replace(
                    'Staffell', 'ST').replace('Pfenninger', 'Pf') if
                grouped != 'std_dev' else standard_deviation_method,
                block_width, wind_speed_range).replace(
                '.', '_').replace(' ', '_').replace('pdf', '.pdf').replace(
                ',', '_').replace('[', '').replace(']', '')))
        plt.close()


def plot_smoothed_pc_turbines(standard_deviation_method, block_width,
                              wind_speed_range, turbines,
                              weather_data_name,
                              mean_roughness_lengths=None):
    fig = plt.figure()
    handles = []
    for turbine, mean_roughness_length in zip(
            turbines, mean_roughness_lengths):
        if turbine.name == 'GE 1,5 SLE':
            name = 'GE 1.5'
        else:
            name = ' '.join(turbine.name.split(' ')[1:3])
        if standard_deviation_method == 'turbulence_intensity':
            turbulence_intensity = tools.estimate_turbulence_intensity(
                turbine.hub_height, mean_roughness_length)
        else:
            turbulence_intensity = None
        # Plot original curve
        a, = plt.plot(turbine.power_curve['wind_speed'],
                      turbine.power_curve['power'] / 1000,
                      label='{} original'.format(name))
        handles.append(a)
        # Plot smoothed curve
        smoothed_power_curve = smooth_power_curve(
            turbine.power_curve.wind_speed, turbine.power_curve['power'],
            block_width=block_width,
            standard_deviation_method=standard_deviation_method,
            turbulence_intensity=turbulence_intensity,
            wind_speed_range=wind_speed_range)
        b, = plt.plot(smoothed_power_curve['wind_speed'],
                      smoothed_power_curve['power'] / 1000,
                      label='{} smoothed'.format(name))
        handles.append(b)
    plt.ylabel('Power in kW')
    plt.xlabel('Wind speed in m/s')
    # plt.title(turbine.name)
    plt.legend(handles=handles)
    fig.savefig(os.path.join(
        os.path.dirname(__file__),
        '../../../User-Shares/Masterarbeit/Latex/inc/images/power_curves/smoothed_pc/by_turbine',
        'turbines_{}_{}_blockwidth{}_range{}.pdf'.format(
            weather_data_name, standard_deviation_method,
            block_width, wind_speed_range).replace(
            '.', '_').replace(' ', '_').replace('pdf', '.pdf')))
    plt.close()

def get_roughness_length(weather_data_name, coordinates):
    z0 = pd.DataFrame()
    for year in [2015, 2016]:
        filename_weather = os.path.join(
            os.path.dirname(__file__), 'dumps/weather',
            'weather_df_{0}_{1}.p'.format(weather_data_name, year))
        # Get weather data
        temperature_heights = [60, 64, 65, 105, 114]
        weather = lib_tools.get_weather_data(
            weather_data_name, coordinates, pickle_load=True,
            filename=filename_weather, year=year,
            temperature_heights=temperature_heights)
        z0 = pd.concat([z0, weather['roughness_length']], axis=0)
    return z0.mean()


def plot_aggregated_vs_smoothed_pc():
    # Initialise WindTurbine objects
    wind_farm_data = get_wind_farm_data(
        'farm_specification_enertrag_2016.p')
    # WF BNE
    wf = WindFarm(**wind_farm_data[0])
    wf.mean_hub_height()
    df = pd.DataFrame()
    for fleet in wf.wind_turbine_fleet:
        # Put aggregated turbine (type) power curves to data frame for
        # aggregation
        curve = fleet['wind_turbine'].power_curve.set_index('wind_speed') * fleet['number_of_turbines']
        df = pd.concat([df, curve], axis=1)
    # Aggregated power curve
    df.interpolate(method='index', inplace=True)
    aggregated_curve = pd.DataFrame(df.sum(axis=1), columns=['power'])
    smoothed_curve = smooth_power_curve(
                pd.Series(aggregated_curve.index), aggregated_curve['power'],
                turbulence_intensity=tools.estimate_turbulence_intensity(
                    height=wf.hub_height, roughness_length=get_roughness_length(
                        'open_FRED', wf.coordinates)[0]))
    smoothed_curve.set_index('wind_speed', inplace=True)
    smoothed_curve_sp = smooth_power_curve(
        pd.Series(aggregated_curve.index), aggregated_curve['power'],
        standard_deviation_method='Staffell_Pfenninger')
    smoothed_curve_sp.set_index('wind_speed', inplace=True)
    smoothed_curve.columns = ['Farm TI']
    smoothed_curve_sp.columns = ['Farm SP']
    aggregated_curve.columns = ['Simple Aggregation']
    # Get aggregated power curve from smoothed turbine power curves
    df_2 = pd.DataFrame()
    df_3 = pd.DataFrame()
    for fleet in wf.wind_turbine_fleet:
        # TI approach
        smoothed_turbine_curve = smooth_power_curve(
            fleet['wind_turbine'].power_curve['wind_speed'],
            fleet['wind_turbine'].power_curve['power'],
                turbulence_intensity=tools.estimate_turbulence_intensity(
                    wf.hub_height, get_roughness_length(
                        'open_FRED', wf.coordinates)[0]))
        smoothed_turbine_curve = smoothed_turbine_curve.set_index('wind_speed') * fleet['number_of_turbines']
        df_2 = pd.concat([df_2, smoothed_turbine_curve], axis=1)
        # SP approach
        smoothed_turbine_curve_sp = smooth_power_curve(
            fleet['wind_turbine'].power_curve['wind_speed'],
            fleet['wind_turbine'].power_curve['power'],
            standard_deviation_method='Staffell_Pfenninger')
        smoothed_turbine_curve_sp = smoothed_turbine_curve_sp.set_index(
            'wind_speed') * fleet['number_of_turbines']
        df_3 = pd.concat([df_3, smoothed_turbine_curve_sp], axis=1)
    df_2.interpolate(method='index', inplace=True)
    aggregated_smoothed_curves = pd.DataFrame(df_2.sum(axis=1), columns=['Turbine TI'])
    df_3.interpolate(method='index', inplace=True)
    aggregated_smoothed_curves_sp = pd.DataFrame(df_3.sum(axis=1),
                                                 columns=['Turbine SP'])
    fig, ax = plt.subplots()
    aggregated_curve.plot(ax=ax, legend=True)
    smoothed_curve.plot(ax=ax, legend=True)
    aggregated_smoothed_curves.plot(ax=ax, legend=True)
    smoothed_curve_sp.plot(ax=ax, legend=True)
    aggregated_smoothed_curves_sp.plot(ax=ax, legend=True)
    plt.legend()
    fig.savefig(os.path.join(
        os.path.dirname(__file__),
        '../../../User-Shares/Masterarbeit/Latex/inc/images/power_curves/smoothed_vs_agg',
        'smoothed_vs_agg_wf_BNE.pdf'))

if __name__ == "__main__":
    single_plots = False
    grouped_plots = False
    turbine_plots = False
    plot_gauss = False
    plot_aggregated_vs_smoothed = True

    if (single_plots or grouped_plots or turbine_plots):
        # turbulence_intensity = 0.15  # Only for single plot
        turbulence_intensity = None
        mean = 0  # Only for single plot

        standard_deviaton_methods = [
            'turbulence_intensity',
            'Staffell_Pfenninger'
        ]
        block_widths = [
            0.1, 1.0,
            0.5]
        wind_speed_ranges = [
            5.0, 10.0, 20.0,
            15.0
        ]
        weather_data_names = ['MERRA', 'open_FRED']

        # Initialise WindTurbine objects
        e70, v90, v80, ge, e82 = initialize_turbines(
            ['enerconE70', 'vestasV90', 'vestasV80', 'ge_1500',
             # 'enerconE66_1800_65', # Note: war nur für wf_3
             'enerconE82_2000'])
        # Wind farm data
        wind_farm_data = {
            'wf_BE': [52.564506, 13.724137],
            'wf_BS': [51.785053, 14.456623],
            'wf_BNW': [53.128206, 12.114433],
            'wf_BNE': [53.4582543833, 13.8976882575],
            'wf_SH': [54.509708, 8.9007]}
        for weather_data_name in weather_data_names:
            turbines_list = []
            z0_list = []
            for wf_data in wind_farm_data:
                z0 = get_roughness_length(weather_data_name,
                                          wind_farm_data[wf_data])[0]
                z0_list.append(z0)
                if (wf_data == 'wf_BE' or wf_data == 'wf_BS'):
                    turbines = [v90]
                elif wf_data == 'wf_BNW':
                    turbines = [v80]
                elif wf_data == 'wf_BNE':
                    turbines = [ge, e82]
                    # append z0 a second time
                    z0_list.append(z0)
                elif wf_data == 'wf_SH':
                    turbines = [e70]
                turbines_list.extend(turbines)
                if single_plots:
                    for std_dev_method in standard_deviaton_methods:
                        for block_width in block_widths:
                            for wind_speed_range in wind_speed_ranges:
                                plot_smoothed_pcs(
                                    standard_deviation_method=std_dev_method,
                                    block_width=block_width,
                                    wind_speed_range=wind_speed_range,
                                    turbines=turbines, mean_roughness_length=z0,
                                    weather_data_name=weather_data_name,
                                    turbulence_intensity=turbulence_intensity,
                                    mean=mean)
                if grouped_plots:
                    # different block widths:
                    for std_dev_method in standard_deviaton_methods:
                        for range in [10.0, 15.0, 20.0]:
                            plot_smoothed_pcs(
                                standard_deviation_method=std_dev_method,
                                block_width=block_widths,
                                wind_speed_range=range,
                                turbines=turbines, mean_roughness_length=z0,
                                grouped='block_width',
                                weather_data_name=weather_data_name)
                    # different standard deviation methods
                    for range in [10.0, 15.0, 20.0]:
                        plot_smoothed_pcs(
                            standard_deviation_method=standard_deviaton_methods,
                            block_width=0.5,
                            wind_speed_range=range,
                            turbines=turbines, mean_roughness_length=z0,
                            grouped='std_dev',
                            weather_data_name=weather_data_name)
                    # different block ranges
                    for std_dev_method in standard_deviaton_methods:
                        plot_smoothed_pcs(
                            standard_deviation_method=std_dev_method,
                            block_width=0.5,
                            wind_speed_range=wind_speed_ranges,
                            turbines=turbines, mean_roughness_length=z0,
                            grouped='wind_speed_range',
                            weather_data_name=weather_data_name)
            if turbine_plots:
                for std_dev in standard_deviaton_methods:
                    plot_smoothed_pc_turbines(
                        standard_deviation_method=std_dev, block_width=0.5,
                        wind_speed_range=15.0, turbines=turbines_list,
                        weather_data_name=weather_data_name,
                        mean_roughness_lengths=z0_list)

    if plot_gauss:
        variables = pd.Series(data=np.arange(-7.0, 7.5, 0.1),
                              index=np.arange(-7.0, 7.5 , 0.1))
        wind_speed = 8
        # variables = np.arange(-15.0, 15.0, 0.5)
        std_dev = 0.15
        mean = 0.0
        gauss = tools.gaussian_distribution(
            variables, standard_deviation=std_dev*wind_speed, mean=0)
        # gauss.index = gauss.index + wind_speed
        gauss_percentage = gauss * 100
        fig = plt.figure()
        gauss_percentage.plot(color='darkblue')
        plt.xlabel('Wind speed in m/s')
        plt.ylabel('Probability in %')
        fig.savefig(os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/inc/images/gauss',
            'gauss_std_dev{}_mean{}.pdf'.format(
                std_dev, mean).replace(
                '.', '_').replace(' ', '_').replace('pdf', '.pdf')))
        plt.close()

    if plot_aggregated_vs_smoothed:
        plot_aggregated_vs_smoothed_pc()
