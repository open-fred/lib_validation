import pandas as pd
try:
    from matplotlib import pyplot as plt
except ImportError:
    plt = None


def print_all_turbine_types(df):
    pd.set_option('display.max_rows', len(df))
    print(df)
    pd.reset_option('display.max_rows')


def plot_or_print(turbine_1, turbine_2):
    r"""
    Plots or prints power output and power (coefficient) curves.

    """
    if plt:
        if turbine_2.power_coefficient_curve is not None:
            turbine_2.power_coefficient_curve.plot(
                x='wind_speed', y='values', style='*',
                title=str(turbine_2.turbine_name) + ' power coefficient curve')
            plt.show()
        if turbine_2.power_curve is not None:
            turbine_2.power_curve.plot(x='wind_speed', y='values', style='*',
                                       title=str(turbine_2.turbine_name) +
                                       ' power curve')
            plt.show()
        if turbine_1.power_coefficient_curve is not None:
            turbine_1.power_coefficient_curve.plot(
                x='wind_speed', y='values', style='*',
                title=str(turbine_1.turbine_name) + ' power coefficient curve')
            plt.show()
        if turbine_1.power_curve is not None:
            turbine_1.power_curve.plot(x='wind_speed', y='values', style='*',
                                       title=str(turbine_1.turbine_name) +
                                       ' power coefficient curve')
            plt.show()
    else:
        if turbine_2.power_coefficient_curve is not None:
            print(turbine_2.power_coefficient_curve)
        if turbine_2.power_curve is not None:
            print(turbine_2.power_curve)
