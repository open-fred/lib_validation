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

cases = ['wind_speed_1', 'wind_speed_2',
         # 'wind_speed_3',
         'wind_speed_4']  # from 4 only log.interp
years = [2015, 2016]
key_figures = [
    'RMSE [m/s]',
   # 'RMSE [%]',
   # 'Pearson coeff.',
   #  'mean bias [m/s]'
]

for year in years:
    for key_figure in key_figures:
        plot_df = pd.DataFrame()
        for case in cases:
            filename_csv = os.path.join(
                os.path.dirname(__file__), 'csv_for_plots',
                'key_figures_approaches_{0}_{1}_open_FRED.tex'.format(
                    case, year))
            case_df = pd.read_csv(filename_csv, index_col=[1, 0],
                                  header=[0, 1])
            figure_case_df = case_df.loc['hourly'][key_figure]
            if case == 'wind_speed_4':
                figure_case_df = figure_case_df.loc[:, ['log. interp.']]
            plot_df = pd.concat([plot_df, figure_case_df], axis=1)
        fig, ax = plt.subplots()
        plot_df.plot(kind='bar', ax=ax, legend=False)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.ylabel(key_figure)
        # plt.xlabel('Wind farms')
        plt.xticks(rotation='vertical')
        # plt.title('{} of wind speed calculation with different methods in {}'.format(
        #     key_figure, year))
        plt.tight_layout()
        fig.savefig(os.path.join(
            os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/inc/images/wind_speeds',
            'Barplot_wind_speed_methods_{}_{}.pdf'.format(
                key_figure.replace(' ', '_').replace('/', '_').replace(
                    '.', ''), year)), bbox_inches = "tight")
        plt.close()


# if __name__ == "__main__":
