# Imports
from matplotlib import pyplot as plt
import matplotlib.colors as colors
import pandas as pd
import numpy as np
import os


def get_cmap(minval=0, maxval=0.8, n=100):
    cmap = plt.get_cmap('Blues_r')
    new_cmap = colors.LinearSegmentedColormap.from_list(
            'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval,
                                                b=maxval),
            cmap(np.linspace(minval, maxval, n)))
    return new_cmap


def bar_plot_from_file(source_filename, output_filename, index=None,
                       index_cols=0, header_cols=0, ylabel=''):
    df = pd.read_csv(source_filename, index_col=index_cols, header=header_cols,
                     sep=',', decimal='.')
    df.index.set_names(['' for i in df.index[0]], inplace=True)
    if index:
        # Select only part of data frame
        plot_df = df.loc[index]
    else:
        # Select whole data frame
        plot_df = df
    fig, ax = plt.subplots()
    plot_df.plot(kind='bar', ax=ax, legend=False, zorder=3,
                 cmap='Blues_r', edgecolor=['black'] * len(plot_df),
                 linewidth=0.5)
    ax.grid(zorder=0)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.ylabel(ylabel)
    plt.xticks(rotation='horizontal')
    plt.tight_layout()
    fig.savefig(output_filename, bbox_inches="tight")
    plt.close()


def run_bar_plots_from_files():
    filenames = ['mean_std_dev_smoothing_2.csv']
    index_header_cols = [([1, 0], 1)]
    ylabels = ['Mean standard deviation in MW']
    output_methods = ['hourly', 'monthly', 'half-hourly']
    for output_method in output_methods:
        for filename, index_header_col, ylabel in zip(
                filenames, index_header_cols, ylabels):
            input_filename = os.path.join(
                os.path.dirname(__file__),
                '../../../User-Shares/Masterarbeit/Latex/csv_for_plots',
                filename)
            output_filename = os.path.join(
                os.path.dirname(__file__),
                '../../../User-Shares/Masterarbeit/Latex/inc/images/' +
                'bar_plots_others',
                'bar_plot_{}_{}.png'.format(filename.split('.')[0],
                                            output_method))
            bar_plot_from_file(
                input_filename, output_filename=output_filename,
                index_cols=index_header_col[0],
                header_cols=index_header_col[1], index=output_method,
                ylabel=ylabel)
            bar_plot_from_file(
                input_filename, output_filename=output_filename.replace(
                    '.png', '.pdf'),
                index_cols=index_header_col[0],
                header_cols=index_header_col[1], index=output_method,
                ylabel=ylabel)


def bar_plot_key_figures(years, output_method, key_figure, cases,
                         weather_data_names):
    # Initialize double plot (both weather data sets)
    weather_fig, axes = plt.subplots(1, 2, sharey='row')
    for weather_data_name, weather_ax in zip(weather_data_names, axes):
        if (('wind_speed_1' in cases or 'wind_speed_5' in cases or
             'wake_losses_1' in cases or
             'wake_losses_3' in cases) and weather_data_name == 'MERRA'):
            pass
        else:
            weather_df = pd.DataFrame()
            for year in years:
                plot_df = pd.DataFrame()
                for case in cases:
                    # Read data
                    filename_csv = os.path.join(
                        os.path.dirname(__file__),
                        '../../../User-Shares/Masterarbeit/Latex/csv_for_plots',
                        'key_figures_approaches_{0}_{1}_{2}.csv'.format(
                            case, year, weather_data_name))
                    case_df = pd.read_csv(filename_csv, index_col=[1, 0],
                                          header=[0, 1])
                    # Choose data with output method and key figure
                    figure_case_df = case_df.loc[output_method][key_figure]
                    if (case == 'wind_speed_4' or case == 'wind_speed_8'):
                        figure_case_df = figure_case_df.loc[:,
                                                            ['Log. interp.']]
                    if case in ['wind_speed_1', 'wind_speed_2', 'wind_speed_3',
                                'wind_speed_5', 'wind_speed_6',
                                'wind_speed_7']:
                        # Order columns
                        figure_case_df = figure_case_df[[
                            '{} {}'.format(list(figure_case_df)[0].split(
                                ' ')[0], height) for
                            height in ['100', '80', '10']]]
                    # Create data frame for plot containing data from different
                    # approaches for one year and weather data set
                    plot_df = pd.concat([plot_df, figure_case_df], axis=1)
                fig, ax = plt.subplots()
                plot_df.plot(kind='bar', ax=ax, legend=False, zorder=3,
                             cmap='Blues_r',
                             edgecolor=['black'] * len(plot_df),
                             linewidth=0.5)
                ax.grid(zorder=0)
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                plt.ylabel(key_figure.replace('coeff.', 'Coefficient'))
                if key_figure == 'RMSE [m/s]':
                    plt.ylim(ymin=0.0, ymax=2.5)
                plt.xticks(rotation='horizontal')
                plt.tight_layout()
                if 'wind_speed_5' in cases:
                    filename_add_on = '_less_data_points'
                else:
                    filename_add_on = ''
                # Save as png and as pdf
                filename_start = os.path.join(
                    os.path.dirname(__file__),
                    '../../../User-Shares/Masterarbeit/Latex/inc/images/' +
                    'key_figures', cases[0],
                    'Barplot_wind_speed_methods_{}_{}_{}_{}{}'.format(
                        key_figure.replace(' ', '_').replace(
                            '/', '_').replace('.', '').replace(
                                '%', 'percentage'), year, weather_data_name,
                        output_method, filename_add_on))
                fig.savefig(filename_start + '.pdf', bbox_inches="tight")
                fig.savefig(filename_start, bbox_inches="tight")
                plt.close()
                # Combine data frames for double plots
                weather_df = pd.concat([weather_df, plot_df], axis=1)
            weather_plot_df = pd.DataFrame()
            column_names = list(set(list(weather_df)))
            column_names.sort()
            for column_name in column_names:
                # Take mean from years
                weather_plot_df[column_name] = weather_df[column_name].mean(
                    axis=1)
            if 'wind_speed_1' in cases or 'wind_speed_5' in cases:
                # Bring column into desired order
                cols = ['Log 100', 'Log 80', 'Log 10', 'H 100', 'H 80', 'H 10',
                        'H2 100', 'H2 80', 'H2 10', 'Log. interp.']
                weather_plot_df = weather_plot_df[cols]
            # Plot into subplot
            weather_plot_df.plot(kind='bar', ax=weather_ax, legend=False,
                                 zorder=3, cmap='Blues_r',
                                 edgecolor=['black'] * len(plot_df),
                                 linewidth=0.5)
            weather_ax.annotate(weather_data_name, xy=(0.99, 0.99),
                                xycoords='axes fraction', ha='right', va='top',
                                zorder=3)
            weather_ax.grid(zorder=0)
            # Rotate xticks
            if len(weather_plot_df.index) <= 4:
                weather_ax.set_xticklabels(weather_ax.get_xticklabels(),
                                           rotation=0, fontsize=8)
            else:
                weather_ax.set_xticklabels(weather_ax.get_xticklabels(),
                                           rotation=0, fontsize=6)
            # Csv dump for calculations
            weather_plot_df.to_csv(os.path.join(
                os.path.dirname(__file__),
                '../../../User-Shares/Masterarbeit/Latex/Tables/' +
                'differences/csvs', 'mean_years_{}_{}_{}_{}_{}.csv'.format(
                        key_figure.replace(' ', '_').replace('/', '_').replace(
                            '.', '').replace('%', 'percentage'),
                        weather_data_name, output_method, case,
                        filename_add_on)))
            if ((('wind_speed_1' in cases or 'wind_speed_5' in cases) and
                    'weather_wind_speed_1' not in cases) or
                    'wake_losses_3' in cases or 'smoothing_2' in cases):
                if 'wind_speed_1' in cases or 'wind_speed_5' in cases:
                    weather_plot_df.index = ['{} ({} m)'.format(
                        item, height) for item, height in zip(
                        weather_plot_df.index, [105, 60, 105])]
                single_fig, ax = plt.subplots()
                weather_plot_df.plot(kind='bar', ax=ax, legend=True, zorder=3,
                                     cmap='Blues_r',
                                     edgecolor=['black'] * len(plot_df),
                                     linewidth=0.5)
                if 'wind_speed_1' in cases or 'wind_speed_5' in cases:
                    # redefine colors
                    if 'wind_speed_1' in cases:
                        multiplicator = 3
                    else:
                        multiplicator = 2
                    colors = (['black'] * multiplicator)
                    colors.extend(['grey'] * multiplicator)
                    colors.extend(['white'] * multiplicator)
                    colors.extend(['darkblue'] * multiplicator)
                    colors.extend(['blue'] * multiplicator)
                    colors.extend(['lightblue'] * multiplicator)
                    colors.extend(['green'] * multiplicator)
                    colors.extend(['yellowgreen'] * multiplicator)
                    colors.extend(['lightgreen'] * multiplicator)
                    colors.extend(['khaki'] * multiplicator)
                    bars = ax.patches
                    for bar, color in zip(bars, colors):
                        bar.set_color(color)
                        bar.set_edgecolor('black')
                ax.grid(zorder=0)
                plt.xticks(rotation='horizontal')
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                plt.ylabel(key_figure.replace('coeff.', 'Coefficient'))
                if key_figure == 'RMSE [m/s]':
                    plt.ylim(ymin=0.0, ymax=2.5)
                plt.tight_layout()
                filename_start = os.path.join(
                    os.path.dirname(__file__),
                    '../../../User-Shares/Masterarbeit/Latex/inc/images/' +
                    'key_figures', cases[0], 'yearly_mean',
                    'Barplot_wind_speed_methods_{}_{}_{}_{}{}'.format(
                        key_figure.replace(' ', '_').replace('/', '_').replace(
                            '.', '').replace('%', 'percentage'), 'yearly_mean',
                        weather_data_name, output_method, filename_add_on))
                single_fig.savefig(filename_start + '.pdf',
                                   bbox_inches="tight")
                single_fig.savefig(filename_start, bbox_inches="tight")
                plt.close()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    weather_fig.text(0.04, 0.5, key_figure.replace('coeff.', 'Coefficient'),
                     va='center', rotation='vertical')
    # Save as png and as pdf
    if ('wind_speed_5' not in cases):
        filename_start = os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/inc/images/key_figures',
            cases[0], 'yearly_mean',
            'Barplot_wind_speed_methods_{}_{}_{}_{}{}'.format(
                key_figure.replace(' ', '_').replace('/', '_').replace(
                    '.', '').replace('%', 'percentage'), 'yearly_mean',
                'both_weather',
                output_method, filename_add_on))
        weather_fig.savefig(filename_start + '.pdf', bbox_inches="tight")
        weather_fig.savefig(filename_start, bbox_inches="tight")
    plt.close()


def bar_plot_key_figures_all_in_one(cases, output_method='hourly'):
    """ average over years"""
    key_figures = ['RMSE [m/s]', 'RMSE [%]', 'Pearson coefficient',
                   'mean bias [m/s]']
    if 'wind_speed' in cases[0]:
        key_figures = [figure.replace('MW', 'm/s') for figure in key_figures]
    else:
        key_figures = [figure.replace('m/s', 'MW') for figure in key_figures]
    weather_data_names = ['MERRA', 'open_FRED']
    for weather_data_name in weather_data_names:
        if (('wind_speed_1' in cases or 'wind_speed_5' in cases or
             'wake_losses_1' in cases or
             'wake_losses_3' in cases) and weather_data_name == 'MERRA'):
            pass
        else:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)
            for key_figure, ax in zip(key_figures, fig.axes):
                figure_df = pd.DataFrame()
                for year in [2015, 2016]:
                    plot_df = pd.DataFrame()
                    for case in cases:
                        # Read data
                        filename_csv = os.path.join(
                            os.path.dirname(__file__),
                            '../../../User-Shares/Masterarbeit/Latex/' +
                            'csv_for_plots',
                            'key_figures_approaches_{0}_{1}_{2}.csv'.format(
                                case, year, weather_data_name))
                        case_df = pd.read_csv(filename_csv, index_col=[1, 0],
                                              header=[0, 1])
                        # Choose data with output method and key figure
                        figure_case_df = case_df.loc[output_method][key_figure]
                        if (case == 'wind_speed_4' or case == 'wind_speed_8'):
                            figure_case_df = figure_case_df.loc[
                                :, ['Log. interp.']]
                        if case in ['wind_speed_1', 'wind_speed_2',
                                    'wind_speed_3', 'wind_speed_5',
                                    'wind_speed_6', 'wind_speed_7']:
                            # Order columns
                            figure_case_df = figure_case_df[[
                                '{} {}'.format(
                                    list(figure_case_df)[0].split(' ')[0],
                                    height) for height in ['100', '80', '10']]]
                        # Create data frame from all cases
                        plot_df = pd.concat([plot_df, figure_case_df], axis=1)
                    # Combine data frames from both years
                    figure_df = pd.concat([figure_df, plot_df], axis=1)
                figure_plot_df = pd.DataFrame()
                column_names = list(set(list(figure_df)))
                column_names.sort()
                for column_name in column_names:
                    # Take mean from years
                    figure_plot_df[column_name] = figure_df[
                        column_name].mean(axis=1)
                if 'wind_speed_1' in cases or 'wind_speed_5' in cases:
                    # Bring column into desired order
                    cols = ['Log 100', 'Log 80', 'Log 10', 'H 100', 'H 80',
                            'H 10', 'H2 100', 'H2 80', 'H2 10', 'Log. interp.']
                    figure_plot_df = figure_plot_df[cols]
                    figure_plot_df.index = ['{} ({} m)'.format(
                        item, height) for item, height in zip(
                        figure_plot_df.index, [105, 60, 105])]
                # Plot into subplot
                figure_plot_df.plot(kind='bar', ax=ax, legend=False, zorder=3,
                                    cmap='Blues_r',
                                    edgecolor=['black'] * len(plot_df),
                                    linewidth=0.5, width=0.75)
                if 'wind_speed_1' in cases or 'wind_speed_5' in cases:
                    colors = (['black'] * 3)
                    colors.extend(['grey'] * 3)
                    colors.extend(['white'] * 3)
                    colors.extend(['darkblue'] * 3)
                    colors.extend(['blue'] * 3)
                    colors.extend(['lightblue'] * 3)
                    colors.extend(['green'] * 3)
                    colors.extend(['yellowgreen'] * 3)
                    colors.extend(['lightgreen'] * 3)
                    colors.extend(['khaki'] * 3)
                    bars = ax.patches
                    for bar, color in zip(bars, colors):
                        bar.set_color(color)
                        bar.set_edgecolor('black')
                ax.grid(zorder=0)
                ax.set_ylabel(key_figure)
                # Rotate xticks
                if len(figure_plot_df.index) <= 4:
                    ax.set_xticklabels(ax.get_xticklabels(), rotation=0,
                                       fontsize=8)
                else:
                    ax.set_xticklabels(ax.get_xticklabels(), rotation=0,
                                       fontsize=6)
                plt.figlegend(loc='upper center', ncol=5, prop={'size': 8},
                              bbox_to_anchor=(0, 0.07, 1, 1),
                              bbox_transform=plt.gcf().transFigure)
            plt.tight_layout()
            filename_start = os.path.join(
                    os.path.dirname(__file__),
                    '../../../User-Shares/Masterarbeit/Latex/inc/images/' +
                    'key_figures/subplots',
                    'Sub_Barplots_yearly_mean_{}_{}_{}'.format(
                        weather_data_name, output_method, case))
            fig.savefig(filename_start + '.pdf', bbox_inches="tight")
            plt.close()


def run_bar_plot_key_figures():
    weather_data_names = [
        'MERRA',
        'open_FRED'
    ]
    cases_list = [
        ['wind_speed_1', 'wind_speed_2', 'wind_speed_3', 'wind_speed_4'],  # from 4 only log.interp
        ['wind_speed_5', 'wind_speed_6', 'wind_speed_7', 'wind_speed_8'],  # first row like weather_wind_speed_3
        # ['weather_wind_speed_1'],
        # ['smoothing_2'],
        # ['single_turbine_1'],
        # ['wake_losses_3'],
        # ['wind_farm_4'],
        # ['wind_farm_gw'],
        # ['wind_farm_2'],
        # ['weather_wind_farm'],
        # ['wind_farm_final']
    ]
    not_for_monthly_list = [
        'wind_farm_3',
        'wind_farm_4',
        'power_output_1',
                            'single_turbine_1']
    years = [
        2015,
        2016
    ]
    key_figures = [
        'RMSE [MW]',
        'RMSE [%]',
        'Pearson coefficient',
        'mean bias [MW]'
    ]
    output_methods = [
        'hourly',
        'monthly'
    ]
    for output_method in output_methods:
        for key_figure in key_figures:
            for cases in cases_list:
                if (output_method == 'monthly' and
                        cases[0] in not_for_monthly_list):
                    pass
                else:
                    if 'wind_speed' in cases[0]:
                        key_figure = key_figure.replace('MW', 'm/s')
                    else:
                        key_figure = key_figure.replace('m/s', 'MW')
                    bar_plot_key_figures(
                        years, output_method, key_figure,
                        cases, weather_data_names)

    for cases in cases_list:
            bar_plot_key_figures_all_in_one(cases=cases,
                                            output_method='hourly')


def run_all_plots():
    run_bar_plot_key_figures()
    run_bar_plots_from_files()

if __name__ == "__main__":
    run_bar_plot_key_figures()
    run_bar_plots_from_files()
