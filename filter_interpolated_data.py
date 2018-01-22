import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# filter interpolated data

# Input:
# path to data
file_path = 'data/2016-01-01+00P1M_.csv'
# window_size specifies how many consecutive time steps have to have the same
# gradient in order to count as interpolated data
window_size = 10
# tolerance specifies the allowed deviation from an inclination of zero summed
# over the whole window
tolerance = 0.0011

# read data
arge_data = pd.read_csv(file_path, sep=';', thousands='.', decimal=',')

arge_data_feedin = arge_data.iloc[:, 6]
data_corrected = arge_data_feedin.copy()
# calculate the sum of the gradient of the feed-in data over |window_size| time
# steps, if it is about zero over the whole time window the data is assumed to
# be interpolated
data_gradient_sum = arge_data_feedin.diff().diff().rolling(
    window=window_size, min_periods=window_size).sum()
for i, v in data_gradient_sum.iteritems():
    # if the sum of the gradient is within the set tolerance and
    if abs(v) <= tolerance:
        if not (arge_data_feedin[i-window_size+1:i+1] < 0).all():
            data_corrected[i-window_size+1:i+1] = np.nan

# plot to check the corrected data
arge_data_feedin.plot()
data_corrected.plot()
plt.show()
