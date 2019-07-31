# Imports from Windpowerlib
from windpowerlib import wind_turbine as wt
from windpowerlib import wind_farm as wf

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
        'vestasV90': {
            'name': 'V90/2000',
            'hub_height': 105,  # in m
            'rotor_diameter': 90,  # in m    source: www.wind-turbine-models.com
        },
        'vestasV80': {
            'name': 'V80/2000',
            'hub_height': 60,  # in m
            'rotor_diameter': 80,  # in m    source: www.wind-turbine-models.com
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
        #         'coordinates': []  # M6 turbine
        #     }
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


def initialize_wind_farms(wind_farm_data_list):
    wind_farm_list = []
    for wind_farm_data in wind_farm_data_list:
        wind_farm = wf.WindFarm(**wind_farm_data)
        wind_farm.coordinates = wind_farm_data['coordinates']
        wind_farm_list.append(wind_farm)
    return wind_farm_list


if __name__ == "__main__":
    save_folder = os.path.join(os.path.dirname(__file__),
                               'dumps/wind_farm_data')
    filenames = [
        'farm_specification_greenwind_2015.p',
        'farm_specification_greenwind_2016.p',
        'turbine_specification_greenwind_2015.p',
        'turbine_specification_greenwind_2016.p'
        ]
    for filename in filenames:
        get_wind_farm_data(filename, save_folder)
