# Imports from Windpowerlib
from windpowerlib import wind_turbine as wt

# Other imports
from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os
from copy import deepcopy
from windrose import WindroseAxes
import matplotlib.cm as cm


def bar_plot_key_figures(year, output_method, key_figure, cases,
                         weather_data_name):
    plot_df = pd.DataFrame()
    for case in cases:
        filename_csv = os.path.join(
            os.path.dirname(__file__), 'csv_for_plots',
            'key_figures_approaches_{0}_{1}_{2}.csv'.format(
                case, year, weather_data_name))
        case_df = pd.read_csv(filename_csv, index_col=[1, 0],
                              header=[0, 1])
        figure_case_df = case_df.loc[output_method][key_figure]
        if (case == 'wind_speed_4' or case == 'wind_speed_8'):
            figure_case_df = figure_case_df.loc[:, ['log. interp.']]
        if (case is not 'wind_speed_4' and case is not 'weather_wind_speed_1'
            and case is not 'wind_speed_8'):
            # Order columns
            figure_case_df = figure_case_df[[
                '{} {}'.format(list(figure_case_df)[0].split(' ')[0],
                               height) for height in ['100', '80', '10']]]
        plot_df = pd.concat([plot_df, figure_case_df], axis=1)
    fig, ax = plt.subplots()
    plot_df.plot(kind='bar', ax=ax, legend=False)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.ylabel(key_figure.replace('coeff.', 'coefficient'))
    if key_figure == 'RMSE [m/s]':
        plt.ylim(ymin=0.0, ymax=2.5)
    # plt.xlabel('Wind farms')
    plt.xticks(rotation='vertical')
    # plt.title('{} of wind speed calculation with different methods in {}'.format(
    #     key_figure, year))
    plt.tight_layout()
    if 'wind_speed_5' in cases:
        filename_add_on = '_less_data_points'
    else:
        filename_add_on = ''
    fig.savefig(os.path.join(
        os.path.dirname(__file__),
        '../../../User-Shares/Masterarbeit/Latex/inc/images/wind_speeds',
        'Barplot_wind_speed_methods_{}_{}_{}_{}{}.pdf'.format(
            key_figure.replace(' ', '_').replace('/', '_').replace(
                '.', ''), year, weather_data_name, output_method,
            filename_add_on)),
        bbox_inches = "tight")
    plt.close()


def run_bar_plot_key_figures():
    weather_data_names = [
        # 'MERRA'
        'open_FRED'
    ]
    cases = [
        'wind_speed_1', 'wind_speed_2',
        'wind_speed_3',
        'wind_speed_4',  # from 4 only log.interp
        # 'wind_speed_5',  # first row like weather_wind_speed_3
        # 'wind_speed_6',  # first row like weather_wind_speed_3
        # 'wind_speed_7',  # first row like weather_wind_speed_3
        # 'wind_speed_8',  # first row like weather_wind_speed_3
        # 'weather_wind_speed_1'  # For best function for MERRA
    ]
    years = [
        2015,
        2016
    ]
    key_figures = [
        'RMSE [m/s]',
        'RMSE [%]',
        'Pearson coeff.',
        'mean bias [m/s]'
    ]
    output_methods = [
        'hourly',
        'monthly'
    ]
    for year in years:
        for weather_data_name in weather_data_names:
            for output_method in output_methods:
                for key_figure in key_figures:
                    bar_plot_key_figures(year, output_method, key_figure,
                                         cases, weather_data_name)

if __name__ == "__main__":
    run_bar_plot_key_figures()