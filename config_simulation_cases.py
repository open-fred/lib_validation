import numpy as np


def get_standard_case_of_configuration():
    r"""
    Returns standard dictionary for configuration of parameters.

    """
    config_dict = {
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
           # 'feedin_comparison',
           # 'plot_correlation'  # Attention: this takes a long time for high resolution
           ],
        'latex_output': [
            'annual_energy_weather',  # Annual energy output all weather sets
            'annual_energy_approaches',  # AEO all approaches
            'annual_energy_weather_approaches',  # AEO all approaches and weather sets
            'key_figures_weather',     # Key figures of all weather sets
            'key_figures_approaches'  # Key figures of all approaches
            ],
        'key_figures_print': ['rmse', 'rmse_normalized', 'pearson',
                              'mean_bias',
                              # 'standard_deviation'
                              ],
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
    if case == 'wind_speed_1':
        config_dict['restriction_list'] = []
        config_dict['approach_list'] = [
            'logarithmic',
            # 'logarithmic_obstacle', # TODO: obstacle height
            'hellman', 'hellman_2']
        config_dict['validation_data_list'] = ['single']
        config_dict['latex_output'] = ['key_figures_weather',
                                       'key_figures_approaches']
    if case == 'wind_speed_2':
        config_dict['restriction_list'] = []
        config_dict['approach_list'] = [
            'logarithmic', 'lin._interp.', 'log._interp.']
        config_dict['validation_data_list'] = ['single']
        config_dict['latex_output'] = ['key_figures_weather',
                                       'key_figures_approaches']
    if case == 'single_turbine_1':
        config_dict['approach_list'] = [
            'p-curve', 'cp-curve', 'p-curve_(d._c.)', 'cp-curve_(d._c.)']
        config_dict['validation_data_list'] = ['single']
        config_dict['restriction_list'] = ['cp-curve_(d._c.)']
    if case == 'single_turbine_2':
        config_dict['approach_list'] = [
            'p-curve', 'cp-curve', 'p-curve_(d._c.)', 'cp-curve_(d._c.)']
        config_dict['validation_data_list'] = ['single']
        config_dict['restriction_list'] = ['cp-curve_(d._c.)']
    if case == 'smoothing_1':
        config_dict['restriction_list'] = []
        config_dict['approach_list'] = ['turbine', 'farm']
    if case == 'density_correction_1':
        config_dict['restriction_list'] = []
        config_dict['approach_list'] = ['turbine', 'farm']
    if case == 'highest_wind_speed':
        config_dict['restriction_list'] = []
        config_dict['approach_list'] = [
            'logarithmic', 'lin._interp.', 'log._interp.']
        config_dict['validation_data_list'] = ['single']
        config_dict['latex_output'] = ['key_figures_weather',
                                       'key_figures_approaches']
    return config_dict
