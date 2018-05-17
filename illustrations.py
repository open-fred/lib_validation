# Imports from lib validation
import plots_single_functionalities
# Other imports
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import os

# Read csv
df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'helper_files',
                              'renewables_energy_2016_ger.csv'),
                 decimal='.', sep=',', index_col=0)
# Get cmap
cmap = plots_single_functionalities.get_cmap()
fig, ax = plt.subplots()
df.plot(legend=True, ax=ax, cmap=cmap)
plt.xlabel('Years')
plt.ylabel('Gross electricity generation in GWh')
# plt.show()
fig.savefig(os.path.join(os.path.dirname(__file__),
                         '../../../User-Shares/Masterarbeit/Latex/inc/images/',
'renewable_energy_2016_ger.pdf'))