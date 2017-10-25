from windpowerlib.modelchain import ModelChain
import pandas as pd
import os
import pickle
from windpowerlib import wind_turbine


year = 2015
filename = 'weather_data_GER_2015.csv'


def get_weather_data(pickle_load=None, filename='pickle_dump.p',
                     weather_data=None, year=None):
    """
    Helper function to load pickled weather data or retrieve data and dump it.

    Parameters
    ----------
    pickle_load : Boolean
        True if data has already been dumped before.
    filename : String
        Name (including path) of file to load data from or if
        MERRA data is retrieved using function 'create_merra_multi_weather'
        to get data from. Default: 'pickle_dump.p'.
    weather_data : String
        String specifying if coastdat or MERRA data is retrieved in case
        `pickle_load` is False. Default: None. # TODO: add open_FRED
    year : int
        Specifies which year the weather data is retrieved for. Default: None.

    Returns
    -------


    """
    if pickle_load:
        data = pickle.load(open(filename, 'rb'))
    else:
        if weather_data == 'open_FRED':
            # # TODO: add open_FRED weather data
            filename = 'weather_df_open_FRED_{0}.p'.format(year)
        elif weather_data == 'merra':
            data = create_merra_df(os.path.join(os.path.dirname(__file__),
                                                'dumps/weather',
                                                'weather_data_GER_{0}.csv'.format(year))) # TODO check this
            filename = 'weather_df_merra_{0}.p'.format(year)
        pickle.dump(data, open(filename, 'wb'))
    return data


def create_merra_df(filename, coordinates):
    """
    Parameters:
    -----------
    coordinates : list
        ...
    """
    merra_df = pd.read_csv(filename, sep=',', decimal='.', index_col=0)
    merra_df = merra_df.loc[(merra_df['lat'] == coordinates[0]) &
                            (merra_df['lon'] == coordinates[1])]
    merra_df = merra_df.drop(['v1', 'v2', 'h2', 'cumulated hours',
                              'SWTDN', 'SWGDN'], axis=1)
    return merra_df


def power_output_sum(wind_turbines, number_of_turbines, weather):
    """
    Calculate power output of several wind turbines by summation.

    Simplest way to calculate the power output of a wind farm or other
    gathering of wind turbines.

    Parameters:
    -----------
    wind_turbines : list
        Contains wind turbine objects.
    number_of_turbines : list
        Contains number of turbines in wind farm for each wind turbine object.
    weather : object
        ... TODO

    """




# Bredstedt (54.578219, 8.978092)
br_coor = [55, 8.75]
# Get weather
pickle_path = os.path.join(os.path.dirname(__file__),
                               'dumps/weather', 'weather_df_merra_2015.p')
## Initialise WindTurbine objects
#e70 = wind_turbine.WindTurbine(**enerconE70)
#e66 = wind_turbine.WindTurbine(**enerconE66)
#
#wind_turbines = e70
#number_of_turbines = 16

#mc = ModelChain(wind_turbines).run_model(weather)
#power_output = mc.power_output * number_of_turbines
