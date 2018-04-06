from wind_farm_specifications import initialize_turbines
from matplotlib import pyplot as plt
import pandas as pd

turbines = initialize_turbines([
    'enerconE70', 'vestasV90', 'vestasV80', 'ge_1500',
    # 'enerconE66_1800_65', # TODO: war nur für wf_3
    'enerconE82_2000'])

for turbine in turbines:
    fig, ax = plt.subplots()
    power_curve = pd.DataFrame(turbine.power_curve)
    power_curve.set_index('wind_speed', inplace=True)
    power_coefficient_curve = pd.DataFrame(turbine.power_coefficient_curve)
    power_coefficient_curve.set_index('wind_speed', inplace=True)
    power_curve.plot(ax=ax, legend=True)
    power_coefficient_curve.plot(ax=ax, legend=True)

    plt.close()