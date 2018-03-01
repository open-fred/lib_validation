import os
import pandas as pd
import pickle


def get_energy_map_data(plz, place=None, peak_power=None,
                        pickle_load=False, pickle_path=None):
    if not pickle_load:
        df_energymap = pd.read_csv(
            os.path.join(os.path.join(os.path.dirname(__file__),
                                      'data/Energymap'),
                         'eeg_anlagenregister_2015.08.utf8.csv'),
            skiprows=[0, 1, 2, 4], sep=';', decimal=',', thousands='.')
        df_energymap['PLZ'] == plz
        pickle.dump(df_energymap, open(os.path.join(pickle_path,
                                                    'energy_map'), 'wb'))
    if pickle_load:
            df_energymap = pickle.load(open(pickle_path, 'rb'))
    df_energymap = df_energymap.loc[df_energymap['Ort'] == place]
    df_energymap = df_energymap.loc[df_energymap['Anlagentyp'] == 'Windkraft']
    df_energymap = df_energymap.loc[
        df_energymap['Nennleistung(kWp_el)'] == peak_power]
    return df_energymap

if __name__ == "__main__":
    energy_map = True  # Print energy map data (parameter settings below)
    if energy_map:
        # Evaluate WEA data from Energymap
        pickle_load = False
        pickle_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                   'dumps/validation_data'))
        plz = 25821
        place = 'Struckum'
        peak_power = 2300
        df_energymap = get_energy_map_data(plz, place, peak_power,
                                           pickle_load, pickle_path)
        print(df_energymap)
