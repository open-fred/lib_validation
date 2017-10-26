import pandas as pd
from matplotlib import pyplot as plt


def return_lats_lons(df):
    # Returns all latitudes and longitudes of DataFrame
    lats = df.lat.unique()
    lons = df.lon.unique()
    return lats, lons


def print_all_turbine_types(df):
    pd.set_option('display.max_rows', len(df))
    print(df)
    pd.reset_option('display.max_rows')


def plot_or_print(turbine_or_farm, plot=True, print_out=False):
    r"""
    Plots or prints power output and power (coefficient) curves.

    """
    if plot:
        if turbine_or_farm.power_coefficient_curve is not None:
            turbine_or_farm.power_coefficient_curve.plot(
                x='wind_speed', y='values', style='*', title=str(
                    turbine_or_farm.turbine_name) + ' power coefficient curve')
            plt.show()
        if turbine_or_farm.power_curve is not None:
            turbine_or_farm.power_curve.plot(
                x='wind_speed', y='values', style='*', title=str(
                    turbine_or_farm.turbine_name) + ' power curve')
            plt.show()
        if turbine_or_farm.power_output is not None:
            turbine_or_farm.power_output.plot(
                x='timestamp', y='power', style='*', title=str(
                    turbine_or_farm.turbine_name) + ' power output')
            plt.show()
    if print_out:
        if turbine_or_farm.power_coefficient_curve is not None:
            print(turbine_or_farm.power_coefficient_curve)
        if turbine_or_farm.power_curve is not None:
            print(turbine_or_farm.power_curve)
        if turbine_or_farm.power_output is not None:
