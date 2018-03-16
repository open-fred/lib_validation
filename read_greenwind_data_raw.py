import pandas as pd
import os
import sys
import pickle


#ToDo: localize
def setup_windfarm_dataframe(year, windfarm):
    r"""
    Reads greenwind wind turbine data from original files for given year and
    windfarm and sets up a dataframe. The dataframe is stored to a csv file.

    Parameters
    ----------
    year : int
       Year to set up the dataframe for.
    windfarm : String
        Windfarm to set up the dataframe for. Possible choices are 'WF1', 'WF2'
         and 'WF3'.

    """

    file_directory = 'data/Daten_Twele/{}_10-Minuten-Daten/{}/'.format(
        windfarm, year)

    # get names of all files in directory and list of windturbines
    file_list = []
    wind_turbine_list = []
    for file in os.listdir(os.path.join(sys.path[0], file_directory)):
        if file.startswith('{}_{}'.format(windfarm, year)):
            file_list.append(file)
            wind_turbine_list.append(file.split(' ')[0].split('_')[-1])

    # get data for each wind_turbine
    windfarm_alias = {'WF1': 'wf_6', 'WF2': 'wf_7', 'WF3': 'wf_8'}
    counter = 0
    windfarm_df = pd.DataFrame()
    for wt in list(set(wind_turbine_list)):
        print('windturbine' + str(wt))
        if 'WTG' in wt:
            wt_number = int(wt[3:])
        else:
            wt_number = int(wt)
            wt = 'WTG_' + wt
        wt_df = pd.DataFrame()
        for file in file_list:
            if wt in file:
                wt_data = pd.read_csv(file_directory + file,
                                      sep=';', header=[0], decimal=',')
                # set datetime index
                wt_data['timeindex'] = pd.to_datetime(
                    (wt_data['Datum(Remote)'] +
                     wt_data['Uhrzeit(Remote)']).apply(str),
                    format='%d.%m.%Y%H:%M:%S')
                wt_data.set_index('timeindex', inplace=True)
                # delete unnecessary columns
                keep_cols = ['Windgeschwindigkeit', 'Leistung',
                             'Gondelposition', 'Fehlernummer']
                wt_data = wt_data[keep_cols]
                # rename other columns
                wt_data.columns = [
                    '{}_{}_wind_speed'.format(windfarm_alias[windfarm],
                                              wt_number),
                    '{}_{}_power_output'.format(windfarm_alias[windfarm],
                                                wt_number),
                    '{}_{}_wind_dir'.format(windfarm_alias[windfarm],
                                            wt_number),
                    '{}_{}_error_number'.format(windfarm_alias[windfarm],
                                                wt_number)]
                wt_df = wt_df.append(wt_data)
        if counter != 0:
            windfarm_df = windfarm_df.join(wt_df, how='outer')
        else:
            windfarm_df = wt_df
        counter += 1

    # sort index
    windfarm_df.sort_index(inplace=True)
    # drop index with wrong year
    drop_index = windfarm_df.loc[wt_df.index.year != year]
    windfarm_df.drop(drop_index.index, inplace=True)

    # calculate total power output
    column_name = '{}_power_output'.format(windfarm_alias[windfarm])
    power_output_columns = [i for i in list(windfarm_df.columns)
                            if 'power_output' in i]
    windfarm_df[column_name] = windfarm_df[power_output_columns].sum(axis=1)

    file_directory = 'data/Daten_Twele/processed_data/'
    windfarm_df.to_csv(file_directory + '{}_{}.csv'.format(windfarm, year))


def read_windfarm_dataframe(year, windfarm):
    r"""
    Reads greenwind windfarm dataframe created with function
    `setup_windfarm_dataframe` from csv file.

    Parameters
    ----------
    year : int
       Year to set up the dataframe for.
    windfarm : String
        Windfarm to set up the dataframe for. Possible choices are 'WF1', 'WF2'
        and 'WF3'.

    Returns
    --------
    pandas.DataFrame
        The columns of the DataFrame contain measured wind_speed, power_output,
        _wind_dir and error_number for each turbine in the wind farm.

    """

    file_directory = 'data/Daten_Twele/processed_data/'
    windfarm_df = pd.read_csv(
        file_directory + '{}_{}.csv'.format(windfarm, year),
        header=[0], index_col=[0], parse_dates=True)
    return windfarm_df


if __name__ == '__main__':
    windfarms = [
        'WF1',
        'WF2',
        'WF3'
        ]
    years = [
        2015,
        2016
        ]
    for year in years:
        for windfarm in windfarms:
            setup_windfarm_dataframe(year, windfarm)
