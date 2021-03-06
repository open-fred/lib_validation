# Imports from Windpowerlib
from windpowerlib import wind_turbine as wt

# Other imports
from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd
import os
from copy import deepcopy

# TODO's:
# write small tool for display of all turbines of a wind farm


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
                           start=None, end=None):
    r"""
    Plot simulation and validation feedin time series.

    These time series are extracted from a
    :class:`~.analysis_tools.ValidationObject` object.

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
#    def label_bars(bars, labels):
#        # TODO: Remove from here - but save for other possible labels
#        r"""
#        Attach a label above each bar.
#
#        Parameters
#        ----------
#        bars : List
#            Contains the patches of the axis (ax.patches).
#        labels : List
#            Contains the labels.
#
#        """
#        for bar, label in zip(bars, labels):
#            height = bar.get_height()
#            ax.text(bar.get_x() + bar.get_width()/2.,  height + 3, label,
#                    ha='center', va='bottom', fontsize=6)

    # Drop nans and rename columns
    data = deepcopy(data).rename(columns={ # TODO: remove deepcopy if not necessary
        old_name: new_name.replace('_', ' ') for old_name, new_name in
        zip(list(data), list(data))})
    fig, ax = plt.subplots()
    if method == 'hourly':
        data.resample('H').mean()
    if method == 'monthly':
        data = data.resample('M').mean().dropna() # TODO: remove months that only contain some values..
        # Create DataFrame for bar plot
        data.index = pd.Series(
            data.index).dt.strftime('%b')
        data.plot(kind='bar', ax=ax)
#        # Add RMSE labels to bars
#        rmse_labels = ['RMSE [{0}]\n{1}'.format(label_part, round(entry, 2))
#                       for entry in validation_object.rmse_monthly]
#        label_bars(ax.patches[:12], rmse_labels)
    else:
        data.plot(
            legend=True, ax=ax)
    plt.ylabel('Calculated and measured average power output in MW')
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
                     title='Test', color='darkblue', marker_size=3):
    r"""
    Visualize the correlation between two feedin time series.

    Parameters
    ----------
    validation_object : Object
        A :class:`~.analysis_tools.ValidationObject` object representing the
        comparison of simulated feedin time series with validation feedin time
        series.
    filename : String
        Filename including path relatively to the active folder for saving
        the figure. Default: 'Tests/correlation_test.pdf'.
    title : String
        Title of figure. Default: 'Test'.

    """
    # TODO: think of bins.. maybe like in Shap's phd
    # Maximum value for xlim and ylim and line
    maximum = max(data.iloc[:, 0].max(), data.iloc[:, 1].max())
    if method == 'hourly':
        data.resample('H').mean()
    if method == 'monthly':
        data = data.resample('M').mean().dropna() # TODO: remove months that only contain some values..
        marker_size = 10
    fig, ax = plt.subplots()
    data.plot.scatter(x=list(data)[1], y=list(data)[0],
                      ax=ax, c=color, s=marker_size)
    plt.xlabel('{0} {1} power output [MW] of {2}'.format(
        list(data)[1].split('_')[2], method.replace('_','-'),
        ' '.join(list(data)[1].split('_')[:2])))
    plt.ylabel('{0} {1} power output [MW] of {2}'.format(
        list(data)[0].split('_')[2], method.replace('_','-'),
        ' '.join(list(data)[0].split('_')[:2])))
    plt.xlim(xmin=0, xmax=maximum)
    plt.ylim(ymin=0, ymax=maximum)
    ideal, = plt.plot([0, maximum], [0, maximum], color='black',
                      linestyle='--', label='ideal correlation')
    deviation_100, = plt.plot([0, maximum], [0, maximum * 2], color='orange',
                              linestyle='--', label='100 % deviation')
    plt.plot([0, maximum * 2], [0, maximum], color='orange', linestyle='--')
    plt.title(title)
    plt.legend(handles=[ideal, deviation_100])
    # Add certain values to plot as text
    # plt.annotate(
    #     'RMSE = {0} \n Pr = {1} \n mean bias = {2}{3} \n std dev = {4}'.format(
    #         round(validation_object.rmse, 2),
    #         round(validation_object.pearson_s_r, 2),
    #         round(validation_object.mean_bias, 2), 'MW',
    #         round(validation_object.standard_deviation, 2)) + 'MW',
    #     xy=(1, 1), xycoords='axes fraction',
    #     xytext=(-6, -6), textcoords='offset points',
    #     ha='right', va='top', bbox=dict(facecolor='white', alpha=0.5))
    plt.tight_layout()
    fig.savefig(os.path.abspath(os.path.join(
                os.path.dirname(__file__), filename)))
    plt.close()

if __name__ == "__main__":
    # Get all turbine types of windpowerlib
    turbines = wt.get_turbine_types(print_out=False)
    print_whole_dataframe(turbines)
