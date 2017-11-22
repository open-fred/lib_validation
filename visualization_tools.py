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
            plt.close()
    if print_out:
        for farm in wind_farms:
            print(farm.power_output)


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
# TODO: write small tool for display of all turbines of a wind farm


def plot_feedin_comparison(validation_object, filename='Tests/feedin_test.pdf',
                           title='Test', tick_label=None):
    r"""
    Plot simulation and validation feedin time series.

    These time series are extracted from a
    :class:`~.analysis_tools.ValidationObject` object.

    Parameters
    ----------
    validation_object : Object
        A :class:`~.analysis_tools.ValidationObject` object representing the
        comparison of simulated feedin time series with validation feedin time
        series.
    filename : String
        Filename including path relatively to the active folder for saving
        the figure. Default: 'Tests/feedin_test.pdf'.
    title : String
        Title of figure. Default: 'Test'.
    tick_label : List
        Tick labels for x-ticks. Default: None.

    """
    # TODO: start end point for period default: 1 year
    fig = plt.figure()
    if 'energy' in validation_object.output_method:
        label_part = 'MWh'
    if 'power' in validation_object.output_method:
        label_part = 'MW'
    if 'monthly' in validation_object.output_method:
        validation_object.simulation_series.plot(
            kind='bar', width=0.25, align='edge', tick_label=tick_label,
            color='blue', legend=True,
            label=validation_object.weather_data_name)
        validation_object.validation_series.plot(
            kind='bar', width=-0.25, align='edge', color='orange',
            legend=True, label=validation_object.validation_name)
    else:
        validation_object.simulation_series.plot(
            legend=True, label=validation_object.weather_data_name)
        validation_object.validation_series.plot(
            legend=True, label=validation_object.validation_name)
    plt.ylabel('{0} in {1}'.format(
        validation_object.output_method.replace('_', ' '), label_part))
    plt.xticks(rotation='vertical')
    plt.title(title)
    plt.tight_layout()
    fig.savefig(os.path.abspath(os.path.join(
                os.path.dirname(__file__), filename)))
    plt.close()


def plot_correlation(validation_object, filename='Tests/correlation_test.pdf',
                     title='Test'):
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
    if 'energy' in validation_object.output_method:
        label_part = 'MWh'
    if 'power' in validation_object.output_method:
        label_part = 'MW'
    fig = plt.figure()
    plt.scatter(validation_object.validation_series,
                validation_object.simulation_series)
    plt.ylabel('{0} of {1} in {2}'.format(
        validation_object.output_method.replace('_', ' '),
        validation_object.validation_name, label_part))
    plt.xlabel('{0} of {1} in {2}'.format(
        validation_object.output_method.replace('_', ' '),
        validation_object.weather_data_name, label_part))
    # Maximum value for xlim and ylim and line
    maximum = max(validation_object.validation_series.max(),
                  validation_object.simulation_series.max()) + 5
    plt.xlim(xmin=0, xmax=maximum)
    plt.ylim(ymin=0, ymax=maximum)
    ideal, = plt.plot([0, maximum], [0, maximum], color='black',
                      linestyle='--', label='ideal correlation')
    deviation_100, = plt.plot([0, maximum], [0, maximum * 2], color='purple',
                              linestyle='--', label='100 % deviation')
    plt.plot([0, maximum * 2], [0, maximum], color='purple', linestyle='--')
    plt.title(title)
    plt.legend(handles=[ideal, deviation_100])
    # Add certain values to plot as text
    plt.annotate('Pr = {0} \n mean bias = {1}{2} \n std dev = {3}'.format(
                 round(validation_object.pearson_s_r, 2),
                 round(validation_object.mean_bias, 2), label_part,
                 round(validation_object.standard_deviation, 2)),
                 xy=(1, 1), xycoords='axes fraction',
                 xytext=(-6, -6), textcoords='offset points',
                 ha='right', va='top', bbox=dict(facecolor='white', alpha=0.5))
    plt.tight_layout()
    fig.savefig(os.path.abspath(os.path.join(
                os.path.dirname(__file__), filename)))
    plt.close()
