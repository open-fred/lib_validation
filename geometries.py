
import os
import geopandas as gpd
import pandas as pd


def load_polygon(region='uckermark'):
    path = '/home/sabine/Daten_flexibel_01/Wetterdaten/ERA5/'
    if region == 'uckermark':
        filename = os.path.join(path, 'uckermark.geojson')
    elif (region == 'germany' or region == 'brandenburg'):
        filename = os.path.join(path, 'germany', 'germany_nuts_1.geojson')
    regions = gpd.read_file(filename)
    if region == 'uckermark':
        regions.rename(columns={'NUTS': 'nuts'}, inplace=True)
    if region == 'brandenburg':
        regions = regions[regions['nuts'] == 'DE40F']
        regions.index = [0]
    return regions[['geometry', 'nuts']]