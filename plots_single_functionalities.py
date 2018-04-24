
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
                'bar_plot_{}_{}'.format(filename.split('.')[0], output_method))
            bar_plot_from_file(
                input_filename, output_filename=output_filename,
                index_cols=index_header_col[0],
                header_cols=index_header_col[1], index=output_method, ylabel=ylabel)

def bar_plot_key_figures(year, output_method, key_figure, cases,
                         weather_data_name):
    plot_df = pd.DataFrame()
    for case in cases:
        filename_csv = os.path.join(
            os.path.dirname(__file__), '../../../User-Shares/Masterarbeit/Latex/csv_for_plots',
            'key_figures_approaches_{0}_{1}_{2}.csv'.format(
                case, year, weather_data_name))
        case_df = pd.read_csv(filename_csv, index_col=[1, 0],
                              header=[0, 1])
        figure_case_df = case_df.loc[output_method][key_figure]
        if (case == 'wind_speed_4' or case == 'wind_speed_8'):
            figure_case_df = figure_case_df.loc[:, ['Log. interp.']]
        if (case == 'wind_speed_1' and
                case is not 'wind_speed_2' and
                case is not 'wind_speed_3'):
            # Order columns
            figure_case_df = figure_case_df[[
                '{} {}'.format(list(figure_case_df)[0].split(' ')[0],
                               height) for height in ['100', '80', '10']]]
        plot_df = pd.concat([plot_df, figure_case_df], axis=1)
    fig, ax = plt.subplots()
    plot_df.plot(kind='bar', ax=ax, legend=False)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.ylabel(key_figure.replace('coeff.', 'Coefficient'))
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
    if 'wind_speed' in cases[0]:
        folder = 'wind_speeds'
    elif 'smoothing_2' in cases:
        folder = 'smoothing_2'
    elif 'single_turbine' in cases[0]:
        folder = 'single_turbine'
    elif 'wake_losses_1' in cases[0]:
        folder = 'wake_losses_1'
    elif 'wake_losses_3' in cases[0]:
        folder = 'wake_losses_3'
    elif 'wind_farm_1' in cases[0]:
        folder = 'wind_farm_1'
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


def run_bar_plot_key_figures():
    weather_data_names = [
        'MERRA',
        'open_FRED'
    ]
    cases_list = [
        ['wind_speed_1', 'wind_speed_2', 'wind_speed_3', 'wind_speed_4'],  # from 4 only log.interp
        ['wind_speed_5', 'wind_speed_6', 'wind_speed_7', 'wind_speed_8'],  # first row like weather_wind_speed_3
        # ['weather_wind_speed_1'],  # For best function for MERRA
        ['smoothing_2'],
        ['single_turbine_1'],
        ['wake_losses_1'],
        ['wake_losses_3'],
        ['wind_farm_1']
    ]
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
    for year in years:
        for weather_data_name in weather_data_names:
            for output_method in output_methods:
                for key_figure in key_figures:
                    for cases in cases_list:
                        if 'wind_speed' in cases[0]:
                            key_figure = key_figure.replace('MW', 'm/s')
                        else:
                            key_figure = key_figure.replace('m/s', 'MW')
                        if (('wind_speed_1' in cases or
                                    'wind_speed_5' in cases or
                                    'wake_losses_1' in cases or
                                    'wake_losses_3' in cases) and
                                weather_data_name == 'MERRA'):
                            pass
                        else:
                            bar_plot_key_figures(
                                year, output_method, key_figure,
                                cases, weather_data_name)

def run_all_plots():
    run_bar_plot_key_figures()
    run_bar_plots_from_files()

if __name__ == "__main__":
    run_bar_plot_key_figures()
    run_bar_plots_from_files()
