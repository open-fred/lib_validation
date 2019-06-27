# Imports from Windpowerlib
from windpowerlib import wind_turbine as wt

# Imports from lib_validation
import visualization_tools

# Other imports
import os
import pickle


def initialize_turbines(turbine_types, plot_wind_turbines=False):
    """
    Initializes specified turbine types and returns them as objects in a list.

    Parameters
    ----------
    turbine_types : List
        Contains strings of turbine types to be initialized.
        Options: 'enerconE70', ... feel free to add.
    plot_wind_turbines : Boolean
        Decision of plotting (or printing) turbine data (True) or not (False).
        Default: False.

    Returns
    -------
    turbine_list : list
        Containing wind turbine objects.

    """
    # Turbine data specification - feel free to add
    turbine_dict = {
        'enerconE70': {
            'name': 'E-70/2300', # NOTE: Peak power should be 2.37 MW - is 2,31 for turbine in windpowerlib
            'hub_height': 64,  # in m
            'rotor_diameter': 71,  # in m    source: www.wind-turbine-models.com
            'fetch_curve': 'power_curve'
        },
        # 'enerconE66_1800_65': {
        #     'name': 'ENERCON E 66 1800', # NOTE: Peak power should be 1.86 MW - ist 1,8 for turbine in windpowerlib
        #     'hub_height': 65,  # in m
        #     'rotor_diameter': 70,  # in m    source: www.wind-turbine-models.com
        #     'fetch_curve': 'power_curve'
        # },
        'enerconE66_1800_98': {
            'name': 'E-66/1800 ',
            'hub_height': 98,  # in m
            'rotor_diameter': 70,  # in m
            'fetch_curve': 'power_curve'
        },
        'enerconE66_2000': {
            'name': 'E-66/2000',
            'hub_height': 114,  # in m
            'rotor_diameter': 70,  # in m
            'fetch_curve': 'power_curve'
        },
        'enerconE82_2000': {
            'name': 'E-82/2000',
            'hub_height': 138.3,  # in m
            'rotor_diameter': 82,  # in m
            'fetch_curve': 'power_curve'
        },
        'vestasV90': {
            'name': 'V90/2000',
            'hub_height': 105,  # in m
            'rotor_diameter': 90,  # in m    source: www.wind-turbine-models.com
            'fetch_curve': 'power_curve'
        },
        'vestasV80': {
            'name': 'V80/2000',
            'hub_height': 60,  # in m
            'rotor_diameter': 80,  # in m    source: www.wind-turbine-models.com
            'fetch_curve': 'power_curve'
        },
        'ge_1500': {
            'name': 'GE 1,5 SLE',
            'hub_height': 100,  # in m
            'rotor_diameter': 77,  # in m
            'fetch_curve': 'power_curve'
        }
    }

    turbine_list = []
    # Initialize WindTurbine objects
    for turbine_type in turbine_types:
        turbine = wt.WindTurbine(**turbine_dict[turbine_type])
        # if (turbine_type == 'vestasV90' or turbine_type == 'vestasV80'):
        # # Add power coefficient curve
        # if (turbine_type is not 'enerconE66_1800_98' and
        #         turbine_type is not 'enerconE66_2000'):
        #     turbine.fetch_curve = 'power_coefficient_curve'
        #     turbine.fetch_turbine_data()
        turbine_list.append(turbine)
        if plot_wind_turbines:
            visualization_tools.plot_or_print_turbine(turbine)
    return turbine_list


def get_wind_farm_data(filename, save_folder='', pickle_load=False):
    """
    Get wind farm specifications for specified validation data.

    Data is either loaded from pickle files or specified in this function and
    then dumped with pickle.

    Returns
    -------
    wind_farm_data : list
        Containing dictionaries with a name, a wind turbine fleet and
        coordinates in the keys 'name', 'wind_turbine_fleet' and 'coordinates'.

    """
    pickle_path = os.path.join(save_folder, filename)
    if pickle_load:
        wind_farm_data = pickle.load(open(pickle_path, 'rb'))
    else:
        # if 'argenetz' in filename:
        #     e70 = initialize_turbines(['enerconE70'])[0]
        #     if (filename == 'farm_specification_argenetz_2015.p' or
        #             filename == 'farm_specification_argenetz_2016.p'):
        #         # wf_1 = {
        #         #     'name': 'wf_1',
        #         #     'wind_turbine_fleet': [{'wind_turbine': e70,
        #         #                             'number_of_turbines': 16}],
        #         #     'coordinates': []
        #         # }
        #         wf_SH = {
        #             'name': 'wf_SH',
        #             'wind_turbine_fleet': [{'wind_turbine': e70,
        #                                     'number_of_turbines': 6}],
        #             'coordinates': []
        #         }
        #         # wf_3 = {
        #         #     'name': 'wf_3',
        #         #     'wind_turbine_fleet': [{'wind_turbine': e70,
        #         #                             'number_of_turbines': 13},
        #         #                            {'wind_turbine': e66,
        #         #                             'number_of_turbines': 4}],
        #         #     'coordinates': []
        #         # }
        #         # wf_4 = {
        #         #     'name': 'wf_4',
        #         #     'wind_turbine_fleet': [{'wind_turbine': e70,
        #         #                             'number_of_turbines': 22}],
        #         # }
        #         # wf_5 = {
        #         #     'name': 'wf_5',
        #         #     'wind_turbine_fleet': [{'wind_turbine': e70,
        #         #                             'number_of_turbines': 14}],
        #         #              'coordinates': []
        #         # }
        #         # if filename == 'farm_specification_argenetz_2015.p':
        #         wind_farm_data = [wf_SH]
        #         # if filename == 'farm_specification_argenetz_2016.p':
        #         #     wind_farm_data = [wf_2]
        #     if (filename == 'turbine_specification_argenetz_2015.p' or
        #             filename == 'turbine_specification_argenetz_2016.p'):
        #         wind_farm_data = []
        #         for i in range(6):
        #             wind_farm_data.append({
        #                 'name': 'wf_SH',
        #                 'wind_turbine_fleet': [{'wind_turbine': e70,
        #                                         'number_of_turbines': 1}],
        #                 'coordinates': []})
        if 'greenwind' in filename:
            v90, v80 = initialize_turbines(['vestasV90', 'vestasV80'])
            if (filename == 'farm_specification_greenwind_2015.p' or
                    filename == 'farm_specification_greenwind_2016.p'):
                wf_BE = {
                    'name': 'wf_BE',
                    'wind_turbine_fleet': [{'wind_turbine': v90,
                                            'number_of_turbines': 9}],
                    'coordinates': []
                }
                wf_BS = {
                    'name': 'wf_BS',
                    'wind_turbine_fleet': [{'wind_turbine': v90,
                                            'number_of_turbines': 14}],
                    'coordinates': []
                }
                wf_BNW = {
                    'name': 'wf_BNW',
                    'wind_turbine_fleet': [{'wind_turbine': v80,
                                            'number_of_turbines': 2}],
                    'coordinates': []
                }
                wind_farm_data = [wf_BE, wf_BS, wf_BNW]
            if (filename == 'turbine_specification_greenwind_2015.p' or
                    filename == 'turbine_specification_greenwind_2016.p'):
                wind_farm_data = []
                for i in range(9):
                    wind_farm_data.append({
                        'name': 'BE_{}'.format(i+1),
                        'wind_turbine_fleet': [{'wind_turbine': v90,
                                                'number_of_turbines': 1}],
                        'coordinates': []})
                for i in range(14):
                    wind_farm_data.append({
                        'name': 'BS_{}'.format(i+1),
                        'wind_turbine_fleet': [{'wind_turbine': v90,
                                                'number_of_turbines': 1}],
                        'coordinates': []})
                for i in range(2):
                    wind_farm_data.append({
                        'name': 'BNW_{}'.format(i+1),
                        'wind_turbine_fleet': [{'wind_turbine': v80,
                                                'number_of_turbines': 1}],
                        'coordinates': []})
        # if filename == 'farm_specification_enertrag_2016.p':
        #     e66_1800, ge_1500, e66_2000, e82_2000 = initialize_turbines([
        #         'enerconE66_1800_98', 'ge_1500', 'enerconE66_2000',
        #         'enerconE82_2000'])
        #     wf_BNE = {
        #         'name': 'wf_BNE',
        #         'wind_turbine_fleet': [{'wind_turbine': e66_1800,
        #                                 'number_of_turbines': 7},
        #                                {'wind_turbine': ge_1500,
        #                                 'number_of_turbines': 7},
        #                                {'wind_turbine': e66_2000,
        #                                 'number_of_turbines': 1},
        #                                {'wind_turbine': e82_2000,
        #                                 'number_of_turbines': 2}
        #                                ],
        #         'coordinates': []  # M6 turbine
        #     }
        #     wind_farm_data = [wf_BNE]
        pickle.dump(wind_farm_data, open(pickle_path, 'wb'))
    return wind_farm_data


def get_joined_wind_farm_data(filenames, save_folder, pickle_load):
    r"""
    Join the wind farm data of different validation data sets.

    Returns
    -------
    wind_farm_data : list
        Containing wind farm data as in get_wind_farm_data() for several
        data origins defined in `filenames`.

    """
    # Initialize wind farm data list
    wind_farm_data = []
    for filename in filenames:
        wind_farm_data += get_wind_farm_data(filename, save_folder,
                                             pickle_load)
    return wind_farm_data


if __name__ == "__main__":
    save_folder = os.path.join(os.path.dirname(__file__),
                               'dumps/wind_farm_data')
    filenames = [
        # 'farm_specification_argenetz_2015.p',
        # 'farm_specification_argenetz_2016.p',
        # 'turbine_specification_argenetz_2015.p',
        # 'turbine_specification_argenetz_2016.p',
        # 'farm_specification_enertrag_2016.p',
        'farm_specification_greenwind_2015.p',
        'farm_specification_greenwind_2016.p',
        'turbine_specification_greenwind_2015.p',
        'turbine_specification_greenwind_2016.p'
        ]
    for filename in filenames:
        get_wind_farm_data(filename, save_folder)
