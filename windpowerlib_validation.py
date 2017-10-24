from windpowerlib import wind_turbine
import small_tools

# Get all turbine types of windpowerlib
turbines = wind_turbine.get_turbine_types(print_out=False)
small_tools.print_all_turbine_types(turbines)

# Turbine data
enerconE70 = {
    'turbine_name': 'ENERCON E 70 2300',  # NOTE: Peak power should be 2.37 MW - is 2,31 for turbine in windpowerlib
    'hub_height': 64,  # in m
    'rotor_diameter': 71  # in m    source: www.wind-turbine-models.com
}
enerconE66 = {
    'turbine_name': 'ENERCON E 66 1800',  # NOTE: Peak power should be 1.86 MW - ist 1,8 for turbine in windpowerlib
    'hub_height': 65,  # in m
    'rotor_diameter': 70  # in m    source: www.wind-turbine-models.com
}

# Initialise WindTurbine objects
e70 = wind_turbine.WindTurbine(**enerconE70)
e66 = wind_turbine.WindTurbine(**enerconE66)

small_tools.plot_or_print(e70, e66)
