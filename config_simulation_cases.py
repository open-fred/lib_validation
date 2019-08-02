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
            'open_FRED',
            'ERA5'
        ],
        'validation_data_list': ['GreenWind'],
        'visualization_methods': [
           # 'box_plots',
           #  'feedin_comparison',
           #  'plot_correlation',  # This takes a long time for high resolution
           #  'subplots_correlation'
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
        config_dict['weather_data_list'] = [
            'open_FRED',
            'ERA5'
        ]
        config_dict['replacement'] = [('_', ' '), ('log', 'Log')]

    # ---- Single functions - power output ---- #
    if case == 'power_output_1':  # measured wind speeds as weather data
        # Folie 5: Hiermit soll Fehler durch Leistungskurve, welche durch Fitten einer Punktewolke abgeleitet wird, aufgezeigt werden.
        # gemessene Windgeschwindigkeiten (Twele), Validierung: Einspeisung Einzelanlagen Twele
        config_dict['approach_list'] = ['p-curve']
        config_dict['validation_data_list'] = ['gw_wind_speeds']
        config_dict['weather_data_list'] = [
            'open_FRED',
            'ERA5'
        ]
        config_dict['replacement'] = [('p-curve', 'P'), ('_', ' ')]

    # ---- Single Turbine Model ---- #
    if case == 'single_turbine_1':
        # Folie 7: Hiermit soll Gesamtfehler durch Reanalysedaten, Extrapolation auf Nabenhöhe
        # und Leistungskurve aufgezeigt werden und untersucht werden, ob sich Fehler ausgleichen oder aufaddieren.
        # wetterdaten ---> Einspeisung (single turbine model)
        config_dict['approach_list'] = ['p-curve']
        config_dict['validation_data_list'] = ['single']
        config_dict['replacement'] = [('p-curve', 'P'), ('_', ' ')]

    return config_dict
