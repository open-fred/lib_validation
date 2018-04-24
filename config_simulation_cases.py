import numpy as np


def get_standard_case_of_configuration():
    r"""
    Returns standard dictionary for configuration of parameters.

    """
    config_dict = {
        'restriction_list' : [],
        # 'restriction_list': [
        #     'simple',
        #     'density_correction',
        #     'smooth_wf',
        #     'constant_efficiency_90_%',
        #     'constant_efficiency_80_%',
        #     'efficiency_curve',
        # #    'eff_curve_smooth',
        # #    'linear_interpolation'
        # #    'wf_1',
        # #    'wf_2',
        # #     'wf_3',
        # #     'wf_4', 'wf_5'
        #     ],
        # 'approach_list': [  # TODO: wahrscheinlich nicht hier - immer unterschiedlich
        #     'simple',  # logarithmic wind profile, simple aggregation for farm output
        #     'density_correction',  # density corrected power curve, simple aggregation
        #     'smooth_wf',  # Smoothed power curves at wind farm level
        #     'constant_efficiency_90_%',  # Constant wind farm efficiency of 90 % without smoothing
        #     'constant_efficiency_80_%',  # Constant wind farm efficiency of 80 % without smoothing
        #     'efficiency_curve',  # Wind farm efficiency curve without smoothing
        #     'eff_curve_smooth',   # Wind farm efficiency curve with smoothing
        #     'lin._interp.',
        #     'test_cluster'
        #     ],
        'weather_data_list': ['MERRA', 'open_FRED'],
        'validation_data_list': ['ArgeNetz', 'Enertrag', 'GreenWind'],
        'output_methods': ['half_hourly',  # Only if possible
                           'hourly', 'monthly'],
        'visualization_methods': [
           # 'box_plots',
            'feedin_comparison',
            'plot_correlation',  # Attention: this takes a long time for high resolution
            'subplots_correlation'
           ],
        'latex_output': [
            'annual_energy_weather',  # Annual energy output all weather sets
            'annual_energy_approaches',  # AEO all approaches
            'annual_energy_weather_approaches',  # AEO all approaches and weather sets
            'key_figures_weather',     # Key figures of all weather sets
            'key_figures_approaches'  # Key figures of all approaches
            ],
        'key_figures_print': ['rmse',
                              'rmse_normalized',
                              'pearson',
                              'mean_bias',
                              # 'standard_deviation' # is std dev of bias!
                              ],
        'replacement': [('_', ' ')],   # ('_wf', '')
        'years': [
            2015,
            2016
            ]
        }
    return config_dict


def get_configuration(case=None):
    r"""
    ...

    Parameters
    ----------
    case : string or None
        Specifies case for which parameters are fetched. If None the standard
        parameters are used.

    Returns
    -------
    config_dict : dictionary
        Keys are explained in Notes.

    Notes
    -----
    Returned dictionary contains the following parameters as keys:

    restriction_list : list
        Wind farms and approaches that will not be examined also if they are in
        the time series df
    approach_list : list
        Approaches to be calculated.
    weather_data_list : list
        Weather data to take into consideration.
    validation_data_list : list
        Validation data to take into consideration.
    output_methods : list
        Temporal output resolutions to take into consideration.
    visualization_methods : list
        Plot applications to take into consideration.
        Options: 'feedin_comparison', ..
    latex_output : list
        Type of latex tables to take into consideration.
    key_figures_print : list
        Key figures to be printed if a key figures table in `latex_output`.

    """
    # Get standard case that will remain if the entries are not overwritten
    config_dict = get_standard_case_of_configuration()

    # ---- Single functions - wind speed ---- # (only open_FRED)
    if case == 'wind_speed_1':
        config_dict['approach_list'] = [
            'log_100', 'log_80', 'log_10']
        config_dict['validation_data_list'] = ['single']
        config_dict['weather_data_list'] = ['open_FRED']
        config_dict['latex_output'] = ['key_figures_approaches']
        config_dict['replacement'] = [('_', ' '), ('log', 'Log')]
    if case == 'wind_speed_2':
        config_dict['approach_list'] = [
            'hellman_100', 'hellman_80', 'hellman_10']
        config_dict['validation_data_list'] = ['single']
        config_dict['weather_data_list'] = ['open_FRED']
        config_dict['latex_output'] = ['key_figures_approaches']
        config_dict['replacement'] = [
            ('_', ' '), ('hellman', 'H')]
    if case == 'wind_speed_3':
        config_dict['approach_list'] = [
            'hellman2_100', 'hellman2_80', 'hellman2_10']
        config_dict['validation_data_list'] = ['single']
        config_dict['weather_data_list'] = ['open_FRED']
        config_dict['latex_output'] = ['key_figures_approaches']
        config_dict['replacement'] = [
            ('_', ' '), ('hellman', 'H')]
    if case == 'wind_speed_4':
        config_dict['approach_list'] = [
            'log._interp.', 'log_100', 'log_80', 'log_10']
        config_dict['validation_data_list'] = ['single']
        config_dict['weather_data_list'] = ['open_FRED']
        config_dict['latex_output'] = ['key_figures_approaches']
        config_dict['replacement'] = [('_', ' '), ('log', 'Log')]
    if case == 'wind_speed_5':  # first row like weather_wind_speed_3
        config_dict['approach_list'] = [
            'log_100', 'log_80', 'log_10']
        config_dict['validation_data_list'] = ['single']
        config_dict['weather_data_list'] = ['open_FRED']
        config_dict['latex_output'] = ['key_figures_approaches']
        config_dict['replacement'] = [('_', ' '), ('log', 'Log')]
    if case == 'wind_speed_6':  # first row like weather_wind_speed_3
        config_dict['approach_list'] = [
            'hellman_100', 'hellman_80', 'hellman_10']
        config_dict['validation_data_list'] = ['single']
        config_dict['weather_data_list'] = ['open_FRED']
        config_dict['latex_output'] = ['key_figures_approaches']
        config_dict['replacement'] = [('_', ' '), ('hellman', 'H')]
    if case == 'wind_speed_7':  # first row like weather_wind_speed_3
        config_dict['approach_list'] = [
            'hellman2_100', 'hellman2_80', 'hellman2_10']
        config_dict['validation_data_list'] = ['single']
        config_dict['weather_data_list'] = ['open_FRED']
        config_dict['latex_output'] = ['key_figures_approaches']
        config_dict['replacement'] = [('_', ' '), ('hellman', 'H')]
    if case == 'wind_speed_8':  # first row like weather_wind_speed_3
        config_dict['approach_list'] = [
            'log._interp.', 'log_100', 'log_80', 'log_10']
        config_dict['validation_data_list'] = ['single']
        config_dict['weather_data_list'] = ['open_FRED']
        config_dict['latex_output'] = ['key_figures_approaches']
        config_dict['replacement'] = [('_', ' '), ('log', 'Log')]

    # ---- Single functions - power output ---- #
    if case == 'power_output_1':  # gw wind speeds as validation data
        config_dict['approach_list'] = [
            'p-curve', 'cp-curve', 'p-curve_(d._c.)', 'cp-curve_(d._c.)']
        config_dict['validation_data_list'] = ['gw_wind_speeds']
        config_dict['weather_data_list'] = ['MERRA', 'open_FRED']
        config_dict['latex_output'] = ['key_figures_approaches',
                                       'annual_energy_approaches']
        config_dict['output_methods'] = ['hourly', 'monthly']
        config_dict['key_figures_print'] = ['rmse',
                                            'rmse_normalized',
                                            'pearson',
                                            'mean_bias']
        config_dict['replacement'] = [
            ('cp-curve', 'Cp'), ('p-curve', 'P'),
            ('(d._c.)', '(d.-c.)'), ('_', ' ')]
    # if case == 'power_output_2':  # wf SH wind speeds as validation data
    #     config_dict['approach_list'] = ['p-curve', 'cp-curve']
    #     config_dict['validation_data_list'] = ['sh_wind_speeds']
    #     config_dict['weather_data_list'] = ['MERRA', 'open_FRED']
    #     config_dict['latex_output'] = ['key_figures_approaches',
    #                                    'annual_energy_approaches']
    #     config_dict['output_methods'] = ['hourly', 'monthly']
    #     config_dict['replacement'] = [
    #         ('cp-curve', 'Cp'), ('p-curve', 'P')]
    #     config_dict['years'] = [2016]

    # ---- Single functions - Smoothing ---- #
    # if case == 'smoothing_1':
    #     config_dict['approach_list'] = ['turbine', 'farm']  # smoothing to farm pc or turbine pc
    #     config_dict['validation_data_list'] = ['Enertrag']
    #     config_dict['latex_output'] = ['key_figures_approaches',
    #                                    'annual_energy_approaches',
    #                                    'std_dev_time_series']
    #     config_dict['years'] = [2016]  # Enertrag data only for 2016
    if case == 'smoothing_1':
        config_dict['approach_list'] = ['Turbine_TI', 'Farm_TI',
                                        'Turbine_St._Pf.', 'Farm St._Pf.']  # smoothing to farm pc or turbine pc
        config_dict['validation_data_list'] = ['Enertrag']
        config_dict['latex_output'] = ['key_figures_approaches',
                                       'annual_energy_approaches',
                                       'std_dev_time_series']
        config_dict['years'] = [2016]  # Enertrag data only for 2016
    if case == 'smoothing_2':
        config_dict['approach_list'] = ['TI', 'St._Pf.', 'aggregation']  # Validation
        config_dict['latex_output'] = ['key_figures_approaches',
                                       'annual_energy_approaches',
                                       'std_dev_time_series']
        config_dict['replacement'] = [
            ('_', ' '), ('aggregation', 'Agg.')]
    # if case == 'density_correction_1':
    #     config_dict['approach_list'] = ['turbine', 'farm']

    # ---- Single functions - Wake losses ---- #
    if case == 'wake_losses_1':
        config_dict['approach_list'] = ['Dena', 'Calculated', 'Constant']
        config_dict['validation_data_list'] = ['GreenWind']
        config_dict['weather_data_list'] = ['open_FRED']
        config_dict['latex_output'] = ['key_figures_approaches',
                                       'annual_energy_approaches']
        config_dict['replacement'] = [
            ('_', ' '), ('Calculated', 'Calc.'), ('Constant', 'Const.')]

    # ---- Single Turbine Model ---- #
    if case == 'single_turbine_1':
        config_dict['approach_list'] = [
            'p-curve', 'cp-curve', 'p-curve_(d._c.)']
        config_dict['validation_data_list'] = ['single']
        config_dict['replacement'] = [
            ('cp-curve', 'Cp'), ('p-curve', 'P'),
            ('(d._c.)', '(d.-c.)'), ('_', ' ')]


    # ---- weather data ---- #
    if case == 'weather_wind_speed_1':
        config_dict['approach_list'] = [
            'logarithmic', 'hellman', 'hellman_2']
        config_dict['validation_data_list'] = ['single']
        config_dict['latex_output'] = ['key_figures_weather',
                                       'key_figures_approaches']
        config_dict['replacement'] = [('_', ' '), ('hellman', 'H'),
                                      ('logarithmic', 'Log')]
    if case == 'weather_wind_speed_2':
        config_dict['approach_list'] = [
            'logarithmic', 'lin._interp.', 'log._interp.']
        config_dict['validation_data_list'] = ['single']
        config_dict['weather_data_list'] = ['open_FRED']
        config_dict['latex_output'] = ['key_figures_weather',
                                       'key_figures_approaches']
        config_dict['replacement'] = [('_', ' '), ('logarithmic', 'Log'),
                                      ('interp', 'int')]
    # if case == 'weather_wind_speed_3': # less values (North ...)
    #     config_dict['approach_list'] = [
    #         'logarithmic', 'lin._interp.', 'log._interp.']
    #     config_dict['validation_data_list'] = ['single']
    #     config_dict['latex_output'] = ['key_figures_weather',
    #                                    'key_figures_approaches']
    #     config_dict['output_methods'] = ['half_hourly',  # Only if possible
    #                        'hourly']
    if case == 'weather_single_turbine_1':
        config_dict['approach_list'] = [
            'p-curve', 'cp-curve', 'p-curve_(d._c.)', 'cp-curve_(d._c.)']
        config_dict['validation_data_list'] = ['single']
        config_dict['restriction_list'] = ['cp-curve_(d._c.)']
    if case == 'weather_single_turbine_2':
        config_dict['approach_list'] = [
            'p-curve', 'cp-curve', 'p-curve_(d._c.)', 'cp-curve_(d._c.)']
        config_dict['validation_data_list'] = ['single']
        config_dict['restriction_list'] = ['cp-curve_(d._c.)']
    if case == 'highest_wind_speed':
        config_dict['approach_list'] = [
            'logarithmic', 'lin._interp.', 'log._interp.']
        config_dict['validation_data_list'] = ['single']
        config_dict['latex_output'] = ['key_figures_weather',
                                       'key_figures_approaches']

    return config_dict
