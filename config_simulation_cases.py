"""
The ``config_simulation_cases`` module contains functions for the configuration
of simulations cases for main.py

"""



def get_standard_case_of_configuration():
    r"""
    Returns standard dictionary for configuration of parameters.

    """
    config_dict = {
        'restriction_list': [],
        'weather_data_list': [
            # 'MERRA',
            'open_FRED'
        ],
        'validation_data_list': [
            # 'ArgeNetz',
            # 'Enertrag',
            'GreenWind'
        ],
        'output_methods': ['half_hourly',  # Only if possible
                           'hourly', 'monthly'],
        'visualization_methods': [
           # 'box_plots',
           #  'feedin_comparison',
           #  'plot_correlation',  # This takes a long time for high resolution
           #  'subplots_correlation'
           ],
        'latex_output': [
            'annual_energy_weather',  # Annual energy output all weather sets
            'annual_energy_approaches',  # AEO all approaches
            'annual_energy_weather_approaches',
            'key_figures_weather',     # Key figures of all weather sets
            'key_figures_approaches',  # Key figures of all approaches
            'std_dev_time_series'  # Standard deviation of time series
            ],
        'key_figures_print': ['rmse',
                              'rmse_normalized',
                              'pearson',
                              'mean_bias',
                              # 'standard_deviation' # std dev of bias
                              ],
        'replacement': [('_', ' ')],
        'years': [2015, 2016]
    }
    return config_dict


def get_configuration(case=None):
    r"""
    Returns configuration depending on the case.

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
    latex_output : list
        Type of latex tables to take into consideration.
    key_figures_print : list
        Key figures to be printed if a key figures table in `latex_output`.

    """
    # Get standard case that will remain if the entries are not overwritten
    config_dict = get_standard_case_of_configuration()

    # ---- Single functions - wind speed ---- # (only open_FRED)
    if case == 'wind_speed_1':
        # Folie 6: Kombination Windgeschwindigkeit aus Reanalysemodell + Extrapolation der Windgeschwindigkeit auf Nabenhöhe
        # --> Validierung mit gemessener Windgeschwindigkeit 1. Reihe Anlagen
        config_dict['approach_list'] = [
            'log_100', 'log_80', 'log_10']
        config_dict['validation_data_list'] = ['single']
        config_dict['weather_data_list'] = ['open_FRED']
        config_dict['latex_output'] = ['key_figures_approaches']
        config_dict['replacement'] = [('_', ' '), ('log', 'Log')]
    # if case == 'wind_speed_2':
    #     config_dict['approach_list'] = [
    #         'hellman_100', 'hellman_80', 'hellman_10']
    #     config_dict['validation_data_list'] = ['single']
    #     config_dict['weather_data_list'] = ['open_FRED']
    #     config_dict['latex_output'] = ['key_figures_approaches']
    #     config_dict['replacement'] = [
    #         ('_', ' '), ('hellman', 'H')]
    # if case == 'wind_speed_3':
    #     config_dict['approach_list'] = [
    #         'hellman2_100', 'hellman2_80', 'hellman2_10']
    #     config_dict['validation_data_list'] = ['single']
    #     config_dict['weather_data_list'] = ['open_FRED']
    #     config_dict['latex_output'] = ['key_figures_approaches']
    #     config_dict['replacement'] = [
    #         ('_', ' '), ('hellman', 'H')]
    # if case == 'wind_speed_4':
    #     config_dict['approach_list'] = [
    #         'log._interp.', 'log_100', 'log_80', 'log_10']
    #     config_dict['validation_data_list'] = ['single']
    #     config_dict['weather_data_list'] = ['open_FRED']
    #     config_dict['latex_output'] = ['key_figures_approaches']
    #     config_dict['replacement'] = [('_', ' '), ('log', 'Log')]
    # if case == 'wind_speed_5':  # first row north/west
    #     config_dict['approach_list'] = [
    #         'log_100', 'log_80', 'log_10']
    #     config_dict['validation_data_list'] = ['single']
    #     config_dict['weather_data_list'] = ['open_FRED']
    #     config_dict['latex_output'] = ['key_figures_approaches']
    #     config_dict['replacement'] = [('_', ' '), ('log', 'Log')]
    # if case == 'wind_speed_6':  # first row north/west
    #     config_dict['approach_list'] = [
    #         'hellman_100', 'hellman_80', 'hellman_10']
    #     config_dict['validation_data_list'] = ['single']
    #     config_dict['weather_data_list'] = ['open_FRED']
    #     config_dict['latex_output'] = ['key_figures_approaches']
    #     config_dict['replacement'] = [('_', ' '), ('hellman', 'H')]
    # if case == 'wind_speed_7':  # first row north/west
    #     config_dict['approach_list'] = [
    #         'hellman2_100', 'hellman2_80', 'hellman2_10']
    #     config_dict['validation_data_list'] = ['single']
    #     config_dict['weather_data_list'] = ['open_FRED']
    #     config_dict['latex_output'] = ['key_figures_approaches']
    #     config_dict['replacement'] = [('_', ' '), ('hellman', 'H')]
    # if case == 'wind_speed_8':  # first row north/west
    #     config_dict['approach_list'] = [
    #         'log._interp.', 'log_100', 'log_80', 'log_10']
    #     config_dict['validation_data_list'] = ['single']
    #     config_dict['weather_data_list'] = ['open_FRED']
    #     config_dict['latex_output'] = ['key_figures_approaches']
    #     config_dict['replacement'] = [('_', ' '), ('log', 'Log')]

    # ---- Single functions - power output ---- #
    if case == 'power_output_1':  # measured wind speeds as weather data
        # Folie 5: Hiermit soll Fehler durch Leistungskurve, welche durch Fitten einer Punktewolke abgeleitet wird, aufgezeigt werden.
        # gemessene Windgeschwindigkeiten (Twele), Validierung: Einspeisung Einzelanlagen Twele
        config_dict['approach_list'] = [
            'p-curve',
            # 'cp-curve', 'p-curve_(d._c.)'
        ]
        config_dict['validation_data_list'] = ['gw_wind_speeds']
        config_dict['weather_data_list'] = [
            # 'MERRA',
            # 'open_FRED',
            'ERA5'
        ]
        config_dict['latex_output'] = ['key_figures_approaches',
                                       'annual_energy_approaches']
        config_dict['output_methods'] = ['hourly', 'monthly']
        config_dict['restriction_list'] = ['cp-curve_(d._c.)']
        config_dict['replacement'] = [
            ('cp-curve', 'Cp'), ('p-curve', 'P'),
            ('(d._c.)', '(d.-c.)'), ('_', ' ')]

    # ---- Single functions - Smoothing ---- #
    # if case == 'smoothing_1':  # NOTE: not used anymore
    #     config_dict['approach_list'] = ['Turbine_TI', 'Farm_TI',
    #                                     'Turbine_SP', 'Farm_SP']
    #     config_dict['validation_data_list'] = ['Enertrag']
    #     config_dict['latex_output'] = ['key_figures_approaches',
    #                                    'annual_energy_approaches',
    #                                    'std_dev_time_series']
    #     config_dict['key_figures_print'] = ['rmse',
    #                                         'pearson',
    #                                         'mean_bias']
    #     config_dict['years'] = [2016]  # Enertrag data only for 2016
    #     config_dict['replacement'] = [
    #         ('_', '-'), ('Turbine', 'T'), ('Farm', 'F')]

    # if case == 'smoothing_2':
    #     # GW wind speeds are used. Open_FRED and MERRA only if other weather
    #     # data needed
    #     config_dict['approach_list'] = ['TI', 'SP', 'aggregation']
    #     config_dict['latex_output'] = ['key_figures_approaches',
    #                                    'annual_energy_approaches',
    #                                    'std_dev_time_series']
    #     config_dict['replacement'] = [
    #         ('_', ' '), ('aggregation', 'Agg.')]

    # ---- Single functions - Wake losses ---- #
    # if case == 'wake_losses_1':
    #     config_dict['approach_list'] = ['aggregation', 'No_losses']
    #     config_dict['validation_data_list'] = ['GreenWind']
    #     # GW wind speeds are used. Open_FRED only if other weather data needed
    #     config_dict['weather_data_list'] = ['open_FRED']
    #     config_dict['latex_output'] = ['key_figures_approaches',
    #                                    'annual_energy_approaches']
    #     config_dict['output_methods'] = ['half_hourly',  # Only if possible
    #                                      'hourly']
    #     config_dict['replacement'] = [
    #         ('_', ' '), ('Calculated', 'Calc.'), ('Constant', 'Const.')]
    # if case == 'wake_losses_3':
    #     config_dict['approach_list'] = ['Dena', 'Calculated', 'Constant',
    #                                     'No_losses']
    #     config_dict['validation_data_list'] = ['GreenWind']
    #     config_dict['latex_output'] = ['key_figures_approaches',
    #                                    'annual_energy_approaches']
    #     config_dict['replacement'] = [
    #         ('_', ' '), ('Calculated', 'Calc.'), ('Constant', 'Const.')]

    # ---- Single Turbine Model ---- #
    if case == 'single_turbine_1':
        # Folie 7: Hiermit soll Gesamtfehler durch Reanalysedaten, Extrapolation auf Nabenhöhe
        # und Leistungskurve aufgezeigt werden und untersucht werden, ob sich Fehler ausgleichen oder aufaddieren.
        # wetterdaten ---> Einspeisung (single turbine model)
        config_dict['approach_list'] = [
            'p-curve',
            # 'cp-curve', 'p-curve_(d._c.)'
        ]
        config_dict['validation_data_list'] = ['single']
        config_dict['replacement'] = [
            # ('cp-curve', 'Cp'),
            ('p-curve', 'P'),
            # ('(d._c.)', '(d.-c.)'),
            ('_', ' ')]

    # ---- Wind Farm Model ---- #
    # if case == 'wind_farm_final':
    #     config_dict['approach_list'] = ['Dena', 'Dena-TI',
    #                                     'Constant', 'aggregation']
    #     config_dict['replacement'] = [
    #         ('_', ' '), ('aggregation', 'Agg.'),  ('Constant', 'Const.')]

    # ---- weather data ---- #
    # if case == 'weather_wind_speed_1':
    #     config_dict['approach_list'] = [
    #         'logarithmic', 'hellman', 'hellman_2', 'log._interp.']
    #     config_dict['validation_data_list'] = ['single']
    #     config_dict['latex_output'] = ['key_figures_weather',
    #                                    'key_figures_approaches']
    #     config_dict['replacement'] = [
    #         ('_', ' '), ('hellman', 'H'),
    #         ('logarithmic', 'Log'), ('interp', 'int')]
    # if case == 'weather_wind_farm':
    #     config_dict['approach_list'] = ['Dena-TI', 'Const.-TI']
    return config_dict
