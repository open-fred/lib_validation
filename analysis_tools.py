# imports
import numpy as np


class ValidationObject(object):
    r"""

    Parameters
    ----------
    name : string
        Name of ValidationObject (name of wind farm or region).
    data : pd.DataFrame
        Containing validation and simulated series. Column name of validation
        series contains 'measured' and column name of simulated series
        contains 'calculated'.
    output_method : string
        Specifies the temporal resolution of `data` which is later used for the
        generation of latex tables. For example: 'half_hourly'. Default: None
    weather_data_name : string
        Indicates the origin of the weather data of the simulated feed-in time
        series. This parameter is used for giving file names etc.
         Default: None.
    approach : string
        Name of approach the simulated time series are calculated with. This
        parameter is used for giving file names etc.  Default: None.
    min_periods_pearson : Integer
        Minimum amount of periods for correlation. Default: None.

    Attributes
    ----------
    name : string
        Name of ValidationObject (name of wind farm or region).
    data : pd.DataFrame
        Containing validation and simulated series. Column name of validation
        series contains 'measured' and column name of simulated series
        contains 'calculated'.
    output_method : string
        Specifies the temporal resolution of `data` which is later used for the
        generation of latex tables. For example: 'half_hourly'. Default: None
    weather_data_name : string
        Indicates the origin of the weather data of the simulated feed-in time
        series. This parameter is used for giving file names etc.
         Default: None.
    approach : string
        Name of approach the simulated time series are calculated with. This
        parameter is used for giving file names etc.  Default: None.
    min_periods_pearson : Integer
        Minimum amount of periods for correlation. Default: None.
    validation_series : pandas.Series
        Validation feed-in time series.
    simulation_series : pandas.Series
        Simulated feed-in time series.
    bias : pd.Series
        Bias of `simulation_series` from `validation_series`.
    mean_bias : float
        Mean bias of `simulation_series` from `validation_series`.
    rmse : float
        Root mean squared error of `simulation_series` concerning
        `validation_series`.
    rmse_normalized : float
        With the average annual power output normalized RMSE.
    standard_deviation : float
        Standard deviation of `bias`.
    pearson_s_r : float
         Pearson's correlation coefficient (Pearson's r) of
         `simulation_series` concerning `validation_series`.
    std_dev_val : float
        Standard deviation of `validation_series`.
    std_dev_sim : float
        Standard deviation of `simulation_series`.

    """
    def __init__(self, name, data, output_method=None, weather_data_name=None,
                 approach=None, min_periods_pearson=None):
        self.name = name
        self.data = data
        self.output_method = output_method
        self.weather_data_name = weather_data_name
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
        r"""
        Returns a data series depending on `type` from `data`.

        Parameters
        ----------
        type : string
            Options: 'measured' and 'calculated'.

        Returns
        -------
        Data series of type `type`.

        """
        column = [col for col in list(self.data) if type in col][0]
        return self.data.dropna()[column]

    def get_standard_deviation(self, data_series):
        r"""
        Calculates the standard deviation of a data series.

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

    def get_rmse(self, normalized=False):
        r"""
        Calculates the RMSE of simulation from validation series.

        Parameters
        ----------
        normalized : Boolean
            If True the RMSE is normalized with the average annual power
            output.

        Returns
        -------
        rmse : float or list
            Root mean squared error.

        """
        rmse = np.sqrt(((self.simulation_series -
                         self.validation_series)**2).sum() /
                       len(self.simulation_series))
        if normalized:
            rmse = (rmse /
                    self.validation_series.resample('A').mean().values * 100)
        return rmse

    def get_bias(self):
        r"""
        Compares two series concerning their deviation (bias).

        Returns
        -------
        pd.Series
            Deviation of simulated series from validation series.

        """
        return self.simulation_series - self.validation_series

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
