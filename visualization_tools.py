import pandas as pd
from matplotlib import pyplot as plt
import os
import seaborn as sns


def return_lats_lons(df):
    r"""
    Returns all latitudes and longitudes of DataFrame.

    """
    lats = df.lat.unique()
    lons = df.lon.unique()
    return lats, lons


def print_whole_dataframe(df):
    r"""
    Prints all entries of a pandas.DataFrame.

    """
    pd.set_option('display.max_rows', len(df))
    print(df)
    pd.reset_option('display.max_rows')


def plot_or_print_turbine(wind_turbine, plot=True, print_out=False):
    r"""
    Plots or prints power output and power (coefficient) curves.

    """
    if plot:
        if wind_turbine.power_coefficient_curve is not None:
            wind_turbine.power_coefficient_curve.plot(
                x='wind_speed', y='values', style='*', title=str(
                    wind_turbine.turbine_name) + ' power coefficient curve')
            plt.show()
        if wind_turbine.power_curve is not None:
            wind_turbine.power_curve.plot(
                x='wind_speed', y='values', style='*', title=str(
                    wind_turbine.turbine_name) + ' power curve')
            plt.show()
        if wind_turbine.power_output is not None:
            wind_turbine.power_output.plot(
                x='timestamp', y='power', style='*', title=str(
                    wind_turbine.turbine_name) + ' power output')
            plt.show()
    if print_out:
        if wind_turbine.power_coefficient_curve is not None:
            print(wind_turbine.power_coefficient_curve)
        if wind_turbine.power_curve is not None:
            print(wind_turbine.power_curve)
        if wind_turbine.power_output is not None:
            print(wind_turbine.power_output)


def plot_or_print_farm(wind_farms, save_folder, plot=True,
                       print_out=False, y_limit=None, x_limit=None):
    # TODO only for one farm!?
    """
    Plot power output and/or power curves of wind farm.

    Parameters:
    -----------
    wind_farms : List of objects
        List of wind farm objects.
    save_folder : String
        Name of Folder for saving the plots.
    """
    if plot:
        for farm in wind_farms:
            fig = plt.figure()
            farm.power_output.plot()
            plt.xticks(rotation='vertical')
            plt.title(farm.wind_farm_name, fontsize=20)
            plt.ylabel('Power output in MW')
            if y_limit:
                plt.ylim(ymin=y_limit[0], ymax=y_limit[1])
            if x_limit:
                plt.xlim(xmin=x_limit[0], xmax=x_limit[1])
            plt.tight_layout()
            fig.savefig(os.path.abspath(os.path.join(
                os.path.dirname(__file__), '../Plots', save_folder,
                str(farm.wind_farm_name) + '.pdf')))
    if print_out:
        for farm in wind_farms:
            print(farm.power_output)


def box_plots_deviation_df(df, save_folder='Tests',
                           filename='test.pdf', title='Test'):
    r"""

    Parameters
    ----------
    df : pd.DataFrame
        Columns contain Series to be plotted as Box plots.
    save_folder : String
        Name of Folder for saving the plots. Default: 'Tests'.
    filename : String
        Name of filename.
    title : String
        Title of figure.

    """
    fig = plt.figure()
    g = sns.boxplot(data=df, palette='Set3')
    g.set_ylabel('Deviation in MW')
    g.set_title(title)
    fig.savefig(os.path.abspath(os.path.join(
                os.path.dirname(__file__), '../Plots/Boxplots', save_folder,
                filename)))
# TODO: write small tool for display of all turbines of a wind farm
