from greenwind_data import get_first_row_turbine_time_series, get_greenwind_data
from wind_farm_specifications import get_wind_farm_data

# Other imports
import os

# Parameters
wind_farm_pickle_folder = os.path.join(os.path.dirname(__file__),
                                       'dumps/wind_farm_data')
validation_pickle_folder = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'dumps/validation_data'))

def get_wind_efficiency_curves(years):
    for year in years:
        # Get wind farm data
        wind_farm_data_gw = get_wind_farm_data(
            'farm_specification_greenwind_{0}.p'.format(year),
            wind_farm_pickle_folder, pickle_load=True)
        # Get Greenwind data
        greenwind_data = get_greenwind_data(
            year, pickle_load=True, resample=False,
            filename=os.path.join(validation_pickle_folder,
                                  'greenwind_data_{0}.p'.format(year)))
        # Select aggregated power output of wind farm (rename)
        greenwind_data = greenwind_data[[
            '{0}_power_output'.format(data['object_name']) for
            data in wind_farm_data_gw]]
        pickle_filename = os.path.join(
            os.path.dirname(__file__), 'dumps/validation_data',
            'greenwind_data_first_row_{0}.p'.format(year))
        gw_first_row = get_first_row_turbine_time_series(
            year=year, pickle_load=True,
            pickle_filename=pickle_filename, resample=False)
        for wf in ['BE', 'BS', 'BNW']:
            cols_first_row = [col for col in gw_first_row.columns if wf in col]
            first_row_data = gw_first_row[cols_first_row]
            cols_wf = [col for col in greenwind_data.columns if wf in col]
            wf_power_output = greenwind_data[cols_wf]
            wind_efficiency_curve = create_wind_efficiency_curve(
                first_row_data=first_row_data,
                wind_farm_power_output=wf_power_output)

def create_wind_efficiency_curve(first_row_data, wind_farm_power_output):
    pass


if __name__ == "__main__":
    years = [
        2015,
        2016
    ]
    get_wind_efficiency_curves(years=years)