
from matplotlib import pyplot as plt
import pandas as pd
import os



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
    plot_df.plot(kind='bar', ax=ax, legend=False)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.ylabel(ylabel)
    # plt.xlabel('Wind farms')
    # plt.xticks(rotation='vertical')
    # plt.title('{} of wind speed calculation with different methods in {}'.format(
    #     key_figure, year))
    plt.tight_layout()
    fig.savefig(output_filename, bbox_inches="tight")
    plt.close()

def run_bar_plots_from_files():
    filenames = ['mean_std_dev_smoothing_2.csv']
    index_header_cols = [([1, 0], 1)]
    ylabels = ['Mean standard deviation in MW']
    output_methods = ['hourly', 'monthly', 'half-hourly']
    for output_method in output_methods:
        for filename, index_header_col, ylabel in zip(filenames, index_header_cols, ylabels):
            input_filename = os.path.join(
                os.path.dirname(__file__), '../../../User-Shares/Masterarbeit/Latex/csv_for_plots', filename)
            output_filename = os.path.join(
                os.path.dirname(__file__),
                '../../../User-Shares/Masterarbeit/Latex/inc/images/bar_plots_others',
                'bar_plot_{}_{}.png'.format(filename.split('.')[0], output_method))
            bar_plot_from_file(
                input_filename, output_filename=output_filename,
                index_cols=index_header_col[0],
                header_cols=index_header_col[1], index=output_method, ylabel=ylabel)
            bar_plot_from_file(
                input_filename, output_filename=output_filename.replace('.png', '.pdf'),
                index_cols=index_header_col[0],
                header_cols=index_header_col[1], index=output_method,
                ylabel=ylabel)

def bar_plot_key_figures(years, output_method, key_figure, cases,
                         weather_data_names):
    # Initialize double plot (both weather data sets)
    weather_fig, axes = plt.subplots(1, 2, sharey='row')
    for weather_data_name, weather_ax in zip(weather_data_names, axes):
        if (('wind_speed_1' in cases or
                     'wind_speed_5' in cases or
                     'wake_losses_1' in cases or
                     'wake_losses_3' in cases) and
                    weather_data_name == 'MERRA'):
            pass
        else:
            weather_df = pd.DataFrame()
            for year in years:
                plot_df = pd.DataFrame()
                for case in cases:
                    # Read data
                    filename_csv = os.path.join(
                        os.path.dirname(__file__), '../../../User-Shares/Masterarbeit/Latex/csv_for_plots',
                        'key_figures_approaches_{0}_{1}_{2}.csv'.format(
                            case, year, weather_data_name))
                    case_df = pd.read_csv(filename_csv, index_col=[1, 0],
                                          header=[0, 1])
                    # Choose data with output method and key figure
                    figure_case_df = case_df.loc[output_method][key_figure]
                    if (case == 'wind_speed_4' or case == 'wind_speed_8'):
                        figure_case_df = figure_case_df.loc[:, ['Log. interp.']]
                    if case in ['wind_speed_1', 'wind_speed_2', 'wind_speed_3',
                                'wind_speed_5', 'wind_speed_6',
                                'wind_speed_7']:
                        # Order columns
                        figure_case_df = figure_case_df[[
                            '{} {}'.format(list(figure_case_df)[0].split(' ')[0],
                                           height) for height in ['100', '80', '10']]]
                    # Create data frame for plot containing data from different
                    # approaches for one year and weather data set
                    plot_df = pd.concat([plot_df, figure_case_df], axis=1)
                fig, ax = plt.subplots()
                plot_df.plot(kind='bar', ax=ax, legend=False)
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                plt.ylabel(key_figure.replace('coeff.', 'Coefficient'))
                if key_figure == 'RMSE [m/s]':
                    plt.ylim(ymin=0.0, ymax=2.5)
                # plt.xlabel('Wind farms')
                plt.xticks(rotation='horizontal')
                plt.grid()
                # plt.title('{} of wind speed calculation with different methods in {}'.format(
                #     key_figure, year))
                plt.tight_layout()
                if 'wind_speed_5' in cases:
                    filename_add_on = '_less_data_points'
                else:
                    filename_add_on = ''
                if 'wind_speed_1' in cases:
                    folder = 'wind_speed_1'
                elif 'wind_speed_5' in cases:
                    folder = 'wind_speed_5'
                elif 'smoothing_2' in cases:
                    folder = 'smoothing_2'
                elif 'single_turbine_1' in cases:
                    folder = 'single_turbine_1'
                elif 'wake_losses_1' in cases:
                    folder = 'wake_losses_1'
                elif 'wake_losses_3' in cases:
                    folder = 'wake_losses_3'
                elif 'wind_farm_gw' in cases:
                    folder = 'wind_farm_gw'
                elif 'wind_farm_2' in cases:
                    folder = 'wind_farm_2'
                elif 'wind_farm_3' in cases:
                    folder = 'wind_farm_3'
                elif 'wind_farm_4' in cases:
                    folder = 'wind_farm_4'
                elif 'weather_wind_speed_1' in cases:
                    folder = 'weather_wind_speed_1'
                elif 'weather_wind_farm' in cases:
                    folder = 'weather_wind_farm'
                else:
                    folder = ''
                # Save as png and as pdf
                filename_start = os.path.join(
                    os.path.dirname(__file__),
                    '../../../User-Shares/Masterarbeit/Latex/inc/images/key_figures',
                    folder, 'Barplot_wind_speed_methods_{}_{}_{}_{}{}'.format(
                        key_figure.replace(' ', '_').replace('/', '_').replace(
                            '.', '').replace('%', 'percentage'), year, weather_data_name,
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
                weather_plot_df[column_name] = weather_df[column_name].mean(axis=1)
            if 'wind_speed_1' in cases or 'wind_speed_5' in cases:
                # Bring column into desired order
                cols = ['Log 100', 'Log 80', 'Log 10', 'H 100', 'H 80', 'H 10',
                        'H2 100', 'H2 80', 'H2 10', 'Log. interp.']
                weather_plot_df = weather_plot_df[cols]
            # Plot into subplot
            weather_plot_df.plot(kind='bar', ax=weather_ax, legend=False)
            weather_ax.annotate(weather_data_name, xy=(0.99, 0.99),
                         xycoords='axes fraction', ha='right', va='top')
            # Csv dump for calculations
            weather_plot_df.to_csv(os.path.join(
                os.path.dirname(__file__),
                '../../../User-Shares/Masterarbeit/Latex/Tables/differences/csvs',
                'mean_years_{}_{}_{}_{}_{}.csv'.format(
                        key_figure.replace(' ', '_').replace('/', '_').replace(
                            '.', '').replace('%', 'percentage'), weather_data_name,
                        output_method, case, filename_add_on)))
            if ((('wind_speed_1' in cases or 'wind_speed_5' in cases)and
                    'weather_wind_speed_1' not in cases) or
                            'wake_losses_3' in cases):
                if 'wind_speed_1' in cases:
                    weather_plot_df.index = ['{} ({} m)'.format(
                        item, height) for item, height in zip(
                        weather_plot_df.index, [105, 60, 105])]
                single_fig, ax = plt.subplots()
                weather_plot_df.plot(kind='bar', ax=ax, legend=True)
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                plt.ylabel(key_figure.replace('coeff.', 'Coefficient'))
                plt.xticks(rotation='horizontal')
                plt.grid()
                if key_figure == 'RMSE [m/s]':
                    plt.ylim(ymin=0.0, ymax=2.5)
                plt.tight_layout()
                filename_start = os.path.join(
                    os.path.dirname(__file__),
                    '../../../User-Shares/Masterarbeit/Latex/inc/images/key_figures',
                    folder, 'yearly_mean', 'Barplot_wind_speed_methods_{}_{}_{}_{}{}'.format(
                        key_figure.replace(' ', '_').replace('/', '_').replace(
                            '.', '').replace('%', 'percentage'), 'yearly_mean',
                        weather_data_name, output_method, filename_add_on))
                single_fig.savefig(filename_start + '.pdf',
                                    bbox_inches="tight")
                single_fig.savefig(filename_start, bbox_inches="tight")
                plt.close()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.xticks(rotation='horizontal')
    plt.grid()
    weather_fig.text(0.04, 0.5, key_figure.replace('coeff.', 'Coefficient'),
                     va='center', rotation='vertical')
    # plt.tight_layout()
    # plt.title('{} of wind speed calculation with different methods in {}'.format(
    #     key_figure, year))
    # Save as png and as pdf
    if ('wind_speed_5' not in cases):
        filename_start = os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/inc/images/key_figures',
            folder, 'yearly_mean', 'Barplot_wind_speed_methods_{}_{}_{}_{}{}'.format(
                key_figure.replace(' ', '_').replace('/', '_').replace(
                    '.', '').replace('%', 'percentage'), 'yearly_mean',
                'both_weather',
                output_method, filename_add_on))
        weather_fig.savefig(filename_start + '.pdf', bbox_inches="tight")
        weather_fig.savefig(filename_start, bbox_inches="tight")
    plt.close()

def run_bar_plot_key_figures():
    weather_data_names = [
        'MERRA',
        'open_FRED'
    ]
    cases_list = [
        ['wind_speed_1', 'wind_speed_2', 'wind_speed_3', 'wind_speed_4'],  # from 4 only log.interp
        ['wind_speed_5', 'wind_speed_6', 'wind_speed_7', 'wind_speed_8'],  # first row like weather_wind_speed_3
        ['weather_wind_speed_1'],
        ['smoothing_2'],
        ['single_turbine_1'],
        ['wake_losses_3'],
        ['wind_farm_4'],
        ['wind_farm_gw'],
        ['wind_farm_2'],
        ['weather_wind_farm']
    ]
    not_for_monthly_list = [
        'wind_farm_3',
        # 'wind_farm_4',
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

def run_all_plots():
    run_bar_plot_key_figures()
    run_bar_plots_from_files()

if __name__ == "__main__":
    run_bar_plot_key_figures()
    run_bar_plots_from_files()
