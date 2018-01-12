# Imports from Windpowerlib
from windpowerlib import wind_turbine as wt

# Imports from lib_validation
import visualization_tools

# Other imports
import os
import pickle


def initialize_turbines(turbine_types, plot_wind_turbines=False):
    # TODO: scale power curves??
    """
    Initializes specified turbine types and returns them as objects in a list.

    Parameters
    ----------
    turbine_types : List
        Contains strings of turbine types to be initialized.
        Options: 'enerconE70', 'enerconE66' feel free to add.
    plot_wind_turbines : Boolean
        Decision of plotting (or printing) turbine data (True) or not (False).
        Default: False.

    """
    # Turbine data specification - feel free to add
    turbine_dict = {
        'enerconE70': {
            'turbine_name': 'ENERCON E 70 2300', # NOTE: Peak power should be 2.37 MW - is 2,31 for turbine in windpowerlib
            'hub_height': 64,  # in m
            'rotor_diameter': 71  # in m    source: www.wind-turbine-models.com
        },
        'enerconE66': {
            'turbine_name': 'ENERCON E 66 1800', # NOTE: Peak power should be 1.86 MW - ist 1,8 for turbine in windpowerlib
            'hub_height': 65,  # in m
            'rotor_diameter': 70  # in m    source: www.wind-turbine-models.com
        },
        'vestasV90': {
            'turbine_name': 'VESTAS V 90 2000',
            'hub_height': 105,  # in m
            'rotor_diameter': 90  # in m    source: www.wind-turbine-models.com
        },
        'vestasV80': {
            'turbine_name': 'VESTAS V 80 2000',
            'hub_height': 60,  # in m
            'rotor_diameter': 80  # in m    source: www.wind-turbine-models.com
        }
    }

    turbine_list = []
    # Initialize WindTurbine objects
    for turbine_type in turbine_types:
        turbine = wt.WindTurbine(**turbine_dict[turbine_type])
        turbine_list.append(turbine)
        if plot_wind_turbines:
            visualization_tools.plot_or_print_turbine(turbine)
    return turbine_list


def get_wind_farm_data(filename, save_folder='', pickle_load=False):
    """
    Get wind farm specifications for specified validation data.

    Data is either loaded from pickle files or specified in this function and
    then dumped with pickle.

    Parameters
    ----------
    name

    """
    pickle_path = os.path.join(save_folder, filename)
    if pickle_load:
        wind_farm_data = pickle.load(open(pickle_path, 'rb'))
    else:
        if (filename == 'farm_specification_argenetz_2015.p' or
                filename == 'farm_specification_argenetz_2016.p'):
            # Initialize turbines
            e70, e66 = initialize_turbines(['enerconE70', 'enerconE66'])
            wf_1 = {
                'wind_farm_name': 'WF_1',
                'wind_turbine_fleet': [{'wind_turbine': e70,
                                        'number_of_turbines': 16}],
                'coordinates': []
            }
            wf_2 = {
                'wind_farm_name': 'WF_2',
                'wind_turbine_fleet': [{'wind_turbine': e70,
                                        'number_of_turbines': 6}],
                'coordinates': []
            }
            wf_3 = {
                'wind_farm_name': 'WF_3',
                'wind_turbine_fleet': [{'wind_turbine': e70,
                                        'number_of_turbines': 13},
                                       {'wind_turbine': e66,
                                        'number_of_turbines': 4}],
                'coordinates': []
            }
            wf_4 = {
                'wind_farm_name': 'WF_4',
                'wind_turbine_fleet': [{'wind_turbine': e70,
                                        'number_of_turbines': 22}],
                'coordinates': []
            }
            wf_5 = {
                'wind_farm_name': 'WF_5',
                'wind_turbine_fleet': [{'wind_turbine': e70,
                                        'number_of_turbines': 14}],
                'coordinates': []
            }
            if filename == 'farm_specification_argenetz_2015.p':
                wind_farm_data = [wf_1, wf_2, wf_3, wf_4, wf_5]
            if filename == 'farm_specification_argenetz_2016.p':
                wind_farm_data = [wf_1, wf_3, wf_4, wf_5]  # no wf_2 for 2016
        if filename == 'farm_specification_green_wind.p':
            v90, v80 = initialize_turbines(['vestasV90', 'vestasV80'])
            wf_6 = {
                'wind_farm_name': 'WF_6',
                'wind_turbine_fleet': [{'wind_turbine': v90,
                                        'number_of_turbines': 9}],
                #                'coordinates': []
            }
            wf_7 = {
                'wind_farm_name': 'WF_7',
                'wind_turbine_fleet': [{'wind_turbine': v90,
                                        'number_of_turbines': 14}],
                #                'coordinates': []
            }
            wf_8 = {
                'wind_farm_name': 'WF_8',
                'wind_turbine_fleet': [{'wind_turbine': v80,
                                        'number_of_turbines': 2}],
                #                'coordinates': []
            }
            wind_farm_data = [wf_6, wf_7, wf_8]
        pickle.dump(wind_farm_data, open(pickle_path, 'wb'))
    return wind_farm_data

if __name__ == "__main__":
    save_folder = os.path.join(os.path.dirname(__file__),
                               'dumps/wind_farm_data')
    filenames = [
        'farm_specification_argenetz_2015.p',
        'farm_specification_argenetz_2016.p'
        ]
    for filename in filenames:
        get_wind_farm_data(filename, save_folder)
