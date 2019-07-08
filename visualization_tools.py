# Imports from Windpowerlib
from windpowerlib import wind_turbine as wt

# Lib validation imports
# from analysis_tools import ValidationObject

# Other imports
from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os
from copy import deepcopy
from windrose import WindroseAxes
import matplotlib.cm as cm
import math


def print_whole_dataframe(df):
    r"""
    Prints all entries of a pandas.DataFrame or pandas.Series.

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


def plot_or_print_farm(wind_farm, save_folder, plot=True,
                       print_out=False, y_limit=None, x_limit=None):
    """
    Plot power output and/or power curves of wind farm.

    Parameters:
    -----------
    wind_farm : Object
        Wind farm object.
    save_folder : String
        Name of Folder for saving the plots.
    """
    if plot:
        fig = plt.figure()
        wind_farm.power_output.plot()
        plt.xticks(rotation='vertical')
        plt.title(wind_farm.wind_farm_name, fontsize=20)
        plt.ylabel('Power output in MW')
        if y_limit:
            plt.ylim(ymin=y_limit[0], ymax=y_limit[1])
        if x_limit:
            plt.xlim(xmin=x_limit[0], xmax=x_limit[1])
        plt.tight_layout()
        fig.savefig(os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../Plots', save_folder,
            str(wind_farm.wind_farm_name) + '.pdf')))
        plt.close()
    if print_out:
        print(wind_farm.power_output)


def box_plots_bias(df, filename='Tests/test.pdf', title='Test'):
    r"""
    Creates boxplots of the columns of a DataFrame.

    This function is mainly used for creating boxplots of the biases of time
    series.

    Parameters
    ----------
    df : pd.DataFrame
        Columns contain Series to be plotted as Box plots.
    filename : String
        Filename including path relatively to the active folder for saving
        the figure. Default: 'Tests/test.pdf'.
    title : String
        Title of figure. Default: 'Test'.

    """
    fig = plt.figure()
    g = sns.boxplot(data=df, palette='Set3')
    g.set_ylabel('Deviation in MW')
    g.set_title(title)
    fig.savefig(os.path.abspath(os.path.join(
                os.path.dirname(__file__), filename)))
    plt.close()


def plot_feedin_comparison(data, method=None, filename='Tests/feedin_test.pdf',
                           title='Test', tick_label=None,
                           start=None, end=None, y_label_add_on='values'):
    r"""
    Plot simulation and validation feedin time series.

    Parameters
    ----------
    data : pd.DataFrame
        Contains data for plot with column names as label names.
    method: String
        Contains method for resampling. Options: 'monthly', 'hourly'.
        Default: None.
    filename : String
        Filename including path relatively to the active folder for saving
        the figure. Default: 'Tests/feedin_test.pdf'.
    title : String
        Title of figure. Default: 'Test'.
    tick_label : List
        Tick labels for x-ticks. Default: None.
    start : String
        Start date of time period to be plotted in the format 'yyyy-mm-dd' or
        'yyyy-mm-dd hh:mm:ss' or 'yyyy-mm-dd hh:mm:ss+hh:mm'.
        Default: None.
    end : String
        End date of time period to be plotted in the format 'yyyy-mm-dd' or
        'yyyy-mm-dd hh:mm:ss' or 'yyyy-mm-dd hh:mm:ss+hh:mm'. If `start`
        and/or `end` is None the whole time series is plotted. Default: None.

    """
    # Drop nans and rename columns
    data = deepcopy(data).rename(columns={
        old_name: new_name.replace('_', ' ') for old_name, new_name in
        zip(list(data), list(data))})
    fig, ax = plt.subplots()
    if method == 'monthly':
        # Create DataFrame for bar plot
        data.index = pd.Series(
            data.index).dt.strftime('%b')
        data.plot(kind='bar', ax=ax)
    else:
        data.plot(
            legend=True, ax=ax)
    plt.ylabel('Calculated and measured average {}'.format(y_label_add_on))
    plt.xticks(rotation='vertical')
    if (start is not None and end is not None and
            method is not 'monthly'):
        plt.xlim(pd.Timestamp(start), pd.Timestamp(end))
    plt.title(title)
    plt.tight_layout()
    fig.savefig(os.path.abspath(os.path.join(
                os.path.dirname(__file__), filename)))
    plt.close()


def plot_correlation(data, method=None, filename='Tests/correlation_test.pdf',
                     title='Test', color='darkblue', marker_size=3,
                     y_label_add_on='values'):
    r"""
    Visualize the correlation between two feedin time series.

    Parameters
    ----------

    filename : String
        Filename including path relatively to the active folder for saving
        the figure. Default: 'Tests/correlation_test.pdf'.
    title : String
        Title of figure. Default: 'Test'.

    """
    # Maximum value for xlim and ylim and line
    maximum = max(data.iloc[:, 0].max(), data.iloc[:, 1].max())
    if method == 'monthly':
        marker_size = 10
    fig, ax = plt.subplots()
    x_value = [col for col in list(data) if 'calculated' in col][0]
    y_value = [col for col in list(data) if 'measured' in col][0]
    data.plot.scatter(x=x_value, y=y_value, ax=ax, c=color, s=marker_size)
    plt.xlabel('{0} {1} {2} of {3}'.format(
        list(data)[1].split('_')[2], method.replace('_', '-'),
        y_label_add_on, ' '.join(list(data)[1].split('_')[:2])))
    plt.ylabel('{0} {1} {2} of {3}'.format(
        list(data)[0].split('_')[2], method.replace('_', '-'),
        y_label_add_on, ' '.join(list(data)[0].split('_')[:2])))
    plt.xlim(xmin=0, xmax=maximum)
    plt.ylim(ymin=0, ymax=maximum)
    ideal, = plt.plot([0, maximum], [0, maximum], color='black',
                      linestyle='--', label='ideal correlation')
    deviation_100, = plt.plot([0, maximum], [0, maximum * 2], color='orange',
                              linestyle='--', label='100 % deviation')
    plt.plot([0, maximum * 2], [0, maximum], color='orange', linestyle='--')
    plt.title(title)
    plt.legend(handles=[ideal, deviation_100])
    plt.tight_layout()
    fig.savefig(os.path.abspath(os.path.join(
                os.path.dirname(__file__), filename)))
    plt.close()


def correlation_subplot(df, filename):
    if 'wind_speed' in filename:
        unit = 'm/s'
        term = 'v'
    else:
        unit = 'MW'
        term = 'feed-in'
    measured_column = [col for col in list(df) if 'measured' in col][0]
    calculated_columns = [col for col in list(df) if 'measured' not in col]
    pairs = [df.loc[:, [measured_column, calculated_column]] for
             calculated_column in calculated_columns]
    if 'wind_speed_4' in filename:
        # Change order of pairs
        pairs_ordered = []
        approaches = ['log_10', 'log_80', 'log_100', 'log._interp.']
        for approach in approaches:
            pairs_ordered.append([df for df in pairs if '_'.join(list(df)[1].split('_')[3:]) == approach][0])
        pairs = pairs_ordered
    col_row_subplots = math.ceil(np.sqrt(len(list(pairs))))
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
        col_row_subplots, col_row_subplots, sharey='row', sharex='col')
    axes = [ax1, ax2, ax3, ax4]
    maxima = []
    for df, ax in zip(pairs, axes):
        val_obj = ValidationObject(
            name='plot', data=df)
        maximum = max(df.iloc[:, 0].max(), df.iloc[:, 1].max())
        maxima.append(maximum)
        ideal, = ax.plot([0, maximum], [0, maximum], color='black',
                         linestyle='--', linewidth=1,
                         label='ideal correlation')
        ax.set_title([' '.join(col.split('_')[3:] ) for
                      col in df.columns if 'calculated' in col][0])
        # Rename columns for x and y labels
        df.rename(columns={old_col: 'calculated {} in {}'.format(
            term, unit) if 'calculated' in old_col
        else 'measured {} in {}'.format(term, unit) for old_col in df.columns},
                  inplace=True)
        # Choose x and y values column name
        x_value = [col for col in list(df) if 'calculated' in col][0]
        y_value = [col for col in list(df) if 'measured' in col][0]
        df.plot.scatter(x=x_value, y=y_value, ax=ax, c='darkblue', s=2)
        ax.annotate('Pr = {}'.format(round(val_obj.pearson_s_r, 3)),
                    xy=(1, 0), xycoords='axes fraction',
                    xytext=(-1, -1), textcoords='offset points',
                    ha='right', va='bottom')
    if 'power_output_1' in filename:
        limit = max(maxima)
    else:
        limit = math.ceil(max(maxima)) + 1
    for ax in axes:
        ax.set_xlim(xmin=0, xmax=limit)
        ax.set_ylim(ymin=0, ymax=limit)
    plt.tight_layout()
    fig.savefig(filename)
    fig.savefig(filename + '.pdf')
    plt.close()


def plot_wind_rose(wind_speed, wind_direction, filename, title):
    ax = WindroseAxes.from_ax()
    ax.contourf(wind_direction, wind_speed, bins=np.arange(0.01, 26, 2),
                cmap=cm.Blues)
    ax.set_legend()
    plt.title(title)
    plt.savefig(filename)
    plt.close()


if __name__ == "__main__":
    # Get all turbine types of windpowerlib
    turbines = wt.get_turbine_types(print_out=False)
    print_whole_dataframe(turbines)
