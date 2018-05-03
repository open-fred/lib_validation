# Imports from lib_validation
import tools

# Other imports
import numpy as np
import pandas as pd
import os
import pickle
import copy


class ValidationObject(object):
    r"""

    Parameters
    ----------
    name : String
        Name of ValidationObject (name of wind farm or region).
    data : pd.DataFrame
        # TODO: add here and adapt attributes
    output_method : String
        Specifies the form of the time series (`simulation_series` and
        `validation_series`) for the validation.
        For example: 'hourly_energy_output'. Default: None
    weather_data_name : String
        Indicates the origin of the weather data of the simulated feedin time
        series. This parameter will be set as an attribute of ValidationObject
        and is used for giving filenames etc.
    validation_name : String
        Indicates the origin of the validation feedin time series.
        This parameter will be set as an attribute of ValidationObject and is
        used for giving filenames etc.
    approach : String
        ...
    min_periods_pearson : Integer
        ...

    Attributes
    ----------
    name : String
        Name of ValidationObject (name of wind farm or region).
    output_method : String
        Specifies the form of the time series (`simulation_series` and
        `validation_series`) for the validation.
        For example: 'hourly_energy_output'. Default: None
    weather_data_name : String
        Indicates the origin of the weather data of the simulated feedin time
        series. This parameter will be set as an attribute of ValidationObject
        and is used for giving filenames etc.
    validation_name : String
        Indicates the origin of the validation feedin time series.
        This parameter will be set as an attribute of ValidationObject and is
        used for giving filenames etc.
    validation_series : pandas.Series
            Validation feedin output time series.
    simulation_series : pandas.Series
            Simulated feedin output time series.
    bias : pd.Series
        Bias of `simulation_series` from `validation_series`.
    mean_bias : Float
        Mean bias of `simulation_series` from `validation_series`.
    rmse : Float
        Root mean square error of `simulation_series` concerning
        `validation_series`.
    rmse_monthly : List
        Root mean square error for each month.
    rmse_normalized : Float
        With the average annual power output normalized RMSE.
    standard_deviation : Float
        Standard deviation of the bias time series (`bias`).
    pearson_s_r : Float
         Pearson's correlation coeffiecient (Pearson's R) of
         `simulation_series` and `validation_series`.
    std_dev_val : Float
        Standard deviation of the validation time series (`validation_series`).
    std_dev_sim : Float
        Standard deviation of the simulation time series (`simulation_series`).

    """
    def __init__(self, name, data, output_method=None,
                 weather_data_name=None, validation_name=None, approach=None,
                 min_periods_pearson=None):
        self.name = name
        self.data = data
        self.output_method = output_method
        self.weather_data_name = weather_data_name
        self.validation_name = validation_name
        self.approach = approach
        self.min_periods_pearson = min_periods_pearson

        self.validation_series = self.get_series('measured')
        self.simulation_series = self.get_series('calculated')
        self.bias = self.get_bias()
        self.mean_bias = self.bias.mean()
        self.rmse = self.get_rmse()
        self.rmse_monthly = None
        self.rmse_normalized = self.get_rmse(normalized=True)
        self.standard_deviation = self.get_standard_deviation(self.bias)
        self.pearson_s_r = self.get_pearson_s_r()
        self.std_dev_val = self.get_standard_deviation(self.validation_series)
        self.std_dev_sim = self.get_standard_deviation(self.simulation_series)

    def get_series(self, type):
        column = [col for col in list(self.data) if type in col][0]
        return self.data.dropna()[column]

    def get_standard_deviation(self, data_series):
        r"""
        Calculate standard deviation of a data series.

        Parameters
        ----------
        data_series : list or pandas.Series
            Input data series (data points) of which the standard deviation
            will be calculated.

        Return
        ------
        float
            Standard deviation of the input data series.

        """
        average = data_series.mean()
        variance = ((data_series - average)**2).sum() / len(data_series)
        return np.sqrt(variance)

    def get_rmse(self, time_scale=None, normalized=False):
        r"""
        Calculate root mean square error of simulation from validation series.

        Parameters
        ----------
        time_scale : String
            The time scale the RMSE will be calculated for. Options: 'annual',
            'monthly'. Add other options if needed.
        normalized : Boolean
            If True the RMSE is normalized with the average annual power
            output.

        Returns
        -------
        rmse : float or list
            Root mean square error in the time scale specified in `time_scale`.

        """
        if (time_scale is None or time_scale == 'annual'):
            rmse = np.sqrt(((self.simulation_series -
                             self.validation_series)**2).sum() /
                           len(self.simulation_series))
        if time_scale == 'monthly':
            rmse = []
            for month in range(12):
                sim_series = self.simulation_series['{0}-{1}'.format(
                    self.simulation_series.index[-1].year, month + 1)]
                val_series = self.validation_series['{0}-{1}'.format(
                    self.simulation_series.index[-1].year, month + 1)]
                monthly_rmse = np.sqrt(((sim_series - val_series)**2).sum() /
                                       len(self.simulation_series))
                rmse.append(monthly_rmse)
        if normalized:
            rmse = (rmse /
                    self.validation_series.resample('A').mean().values * 100)
        return rmse

    def get_bias(self):
        r"""
        Compare two series concerning their deviation (bias).

        Returns
        -------
        pd.Series
            Deviation of simulated series from validation series.

        """
        return self.simulation_series - self.validation_series

    def get_monthly_mean_biases(self):
        r"""
        Calculate mean biases for each month of the year.

        Returns
        -------
        mean_biases : List
            Contains the mean biases (floats) for each month of the year.

        """
        mean_biases = []
        for month in range(12):
            mean_bias = self.bias['{0}-{1}'.format(
                self.bias.index[10].year, month + 1)].mean()
            mean_biases.append(mean_bias)
        return mean_biases

    def get_pearson_s_r(self):
        r"""
        Calculates the Pearson's correlation coefficient of two series.

        Returns
        -------
        float
            Pearson's correlation coeffiecient (Pearson's R)
            of the input series.

        """
        correlation = self.data.corr(
            method='pearson', min_periods=self.min_periods_pearson).iloc[1, 0]
        return correlation


def correlation(val_obj, sample_resolution=None):
    """


    """
    data = pd.DataFrame([val_obj.validation_series,
                         val_obj.simulation_series]).transpose()
    b = data.resample(sample_resolution).agg({'corr': lambda x: x[data.columns[0]].corr(
        x[data.columns[1]])})
    corr = b['corr'].drop(b['corr'].columns[1], axis=1)
    corr.columns = ['{0} {1}'.format(val_obj.name,
                    val_obj.weather_data_name)]
    return corr

if __name__ == "__main__":
    # TODO delete
    # Load validation objects - choose power output or hourly/monthly energy output
#    path = os.path.join(os.path.dirname(__file__), 'dumps/validation_objects',
#                        'validation_sets_2015_open_FRED_ArgeNetz_simple_power_output.p')
#    path_2 = os.path.join(os.path.dirname(__file__), 'dumps/validation_objects',
#                        'validation_sets_2015_MERRA_ArgeNetz_simple_power_output.p')
    path = os.path.join(os.path.dirname(__file__), 'dumps/validation_objects',
                        'validation_sets_2015_open_FRED_ArgeNetz_simple_hourly_energy_output.p')
    path_2 = os.path.join(os.path.dirname(__file__), 'dumps/validation_objects',
                        'validation_sets_2015_MERRA_ArgeNetz_simple_hourly_energy_output.p')
    val_objs = pickle.load(open(path,'rb'))
    val_objs_2 = pickle.load(open(path_2,'rb'))
    for obj in val_objs_2:
        val_obj = val_objs.append(obj)
    # Choose resolution of resampling
    sample_resolution = 'M'
    # ##################### Correlation dataframe ###############################
    df = pd.DataFrame()
    for val_obj in val_objs:
        output = correlation(val_obj, sample_resolution)
        df = pd.concat([df, output], axis=1)
    df.to_csv('correlations.csv')

    ###################### Tageszeiten  #####################
    time_periods = [(4, 8), (8, 16), (16, 22), (22, 4)]
    for time_period in time_periods:
        val_objs_copy = copy.deepcopy(val_objs)
        for val_obj in val_objs_copy:
            # Set all time series to UTC (will be different in the future, now
            # it's an easy way)
            val_obj.simulation_series.index = val_obj.simulation_series.index.tz_convert(
                    'UTC')
            val_obj.validation_series.index =  val_obj.validation_series.index.tz_convert(
                    'UTC')
            # Selecet time steps
            val_obj.simulation_series = tools.select_certain_time_steps(
                val_obj.simulation_series, time_period)
            val_obj.validation_series = tools.select_certain_time_steps(
                val_obj.validation_series, time_period)
        # Get correlation
        df = pd.DataFrame()
        for val_obj in val_objs:
            output = correlation(val_obj, sample_resolution)
            df = pd.concat([df, output], axis=1)
        df.to_csv('correlations_{0}_{1}.csv'.format(time_period[0],
                                                    time_period[1]))
        ############### Tageszeiten yearly correlation ########################
        # Get correlation
        df = pd.DataFrame()
        for val_obj in val_objs:
            output = correlation(val_obj, 'Y')
            df = pd.concat([df, output], axis=1)
        df.to_csv('correlations_yearly_{0}_{1}.csv'.format(time_period[0],
                                                           time_period[1]))
