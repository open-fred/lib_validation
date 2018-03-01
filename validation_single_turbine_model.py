# Imports from Windpowerlib
from windpowerlib import wind_farm as wf

# Imports from lib_validation
import visualization_tools
import tools
import latex_tables
import modelchain_usage
from merra_weather_data import get_merra_data
from open_fred_weather_data import get_open_fred_data
from argenetz_data import get_argenetz_data
from enertrag_data import get_enertrag_data, get_enertrag_curtailment_data
from analysis_tools import ValidationObject
from greenwind_data import get_greenwind_data

# Other imports
from matplotlib import pyplot as plt
import os
import pandas as pd
import numpy as np
import pickle


# -------------------------- Check wind directions -------------------------- #
def wind_directions_to_csv(frequency=None, corr_min=0.8):
    if frequency is None:
        resample = False
    else:
        resample = True
    # Get Enertrag data
    enertrag_data = get_enertrag_data(
        pickle_load=True, filename=os.path.join(
            os.path.dirname(__file__), 'dumps/validation_data/',
            'enertrag_data_check_wind_dir.p'),
        resample=resample, frequency=frequency, plot=False, x_limit=None)
    # Select wind directions
    wind_directions_df = enertrag_data[[
        column_name for column_name in list(enertrag_data) if
            '_'.join(column_name.split('_')[3:]) == 'wind_dir']]
    if resample:
        wind_directions_df = wind_directions_df.resample(frequency).mean()
    wind_directions_df.to_csv(
        'Evaluation/enertrag_wind_direction/wind_direction_enertrag_resample_{0}.csv'.format(frequency))
    correlation = wind_directions_df.corr()
    amount_df = pd.DataFrame(correlation[correlation >= 0.8].count() - 1,
                             columns=['corr >='.format(corr_min)]).transpose()
    pd.concat([correlation, amount_df], axis=0).to_csv(
        'Evaluation/enertrag_wind_direction/correlation_wind_direction_enertrag_resample_{0}_corrmin_{1}.csv'.format(frequency, corr_min))

if __name__ == "__main__":
    frequency = '30T'
    corr_min = 0.95
    wind_directions_to_csv(frequency, corr_min)
