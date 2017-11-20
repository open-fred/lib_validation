import numpy as np
import pandas as pd


class ValidationObject(object):
    r"""


    """
    def __init__(self, weather_name, validation_name, wind_farm_name,
                 series_validation, series_simulation):
        self.weather_name = weather_name
        self.validation_name = validation_name
        self.wind_farm_name = wind_farm_name
        self.series_validation = series_validation
        self.series_simulation = series_simulation
        
        self.bias = self.get_bias(series_validation, series_simulation)
        self.mean_bias = self.bias.mean()
        self.pearson_s_r = self.get_pearson_s_r(series_validation,
                                                series_simulation)
        self.rmse = None
        self.standard_deviation = self.get_standard_deviation(self.bias)

    def get_standard_deviation(data_series):
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
        average = sum(data_series) / len(data_series)
        variance = sum((data_series[i] - average)**2
                       for i in range(len(data_series))) / len(data_series)
        return np.sqrt(variance)
    
    
    def get_bias(series_validation, series_simulation):
        r"""
        Compare two series concerning their deviation (bias).
        
        Parameters
        ----------
        series_validation : pandas.Series
            Validation power output time series.
        series_simulated : pandas.Series
            Simulated power output time series.
        
        Returns
        -------
        pd.Series
            Deviation of simulated series from validation series.
    
        """
        return pd.Series(data=(series_simulation.values -
                               series_validation.values),
                         index=series_simulation.index)
    
    
    def get_pearson_s_r(series_validation, series_simulation):
        r"""
        Calculates the Pearson's correlation coeffiecient of two series.
    
        Parameters
        ----------
        series_validation : pandas.Series
            Validation power output time series.
        series_simulated : pandas.Series
            Simulated power output time series.
    
        Returns
        -------
        float
            Pearson's correlation coeffiecient (Pearson's R)
            of the input series.
    
        """
        return (((series_validation - series_validation.mean()) *
                 (series_simulation - series_simulation.mean())).sum() /
                np.sqrt(((series_validation -
                          series_validation.mean())**2).sum() *
                        ((series_simulation -
                          series_simulation.mean())**2).sum()))


def compare_series_std_deviation_multiple(series_validation_list,
                                          series_simulation_list, column_names):
    r"""
    Compare multiple series concerning their deviation and standard deviation.

    Multiple series are being compared to their validation series by using the
    function compare_series_std_deviation(). 

    Parameters
    ----------
    series_validation_list : List of pd.Series
        List of validation series.
    series_simulated_list : List of pd.Series
        List of simulated series that should be validated. Must be in the same
        order as `series_validation`.
    column_names : List of Strings
        Desired column names in the same order as `series_validation` and
        `series_simulated`.

    Returns
    -------
    deviation_df : pd.DataFrame
        The columns contain deviations of simulated series from validation
        series.
    standard_deviations : List
        Contains standard deviations (floats) of simulated series concerning
        their validation series.

    """
    deviation_df = pd.DataFrame()
    standard_deviations = []
    for farm_number in range(len(series_validation_list)):
        deviation = get_bias(
            series_validation_list[farm_number],
            series_simulation_list[farm_number])
        deviation_df_part = pd.DataFrame(
            data=deviation, index=series_validation_list[farm_number].index,
            columns=[column_names[farm_number]])
        deviation_df = pd.concat([deviation_df, deviation_df_part], axis=1)
        standard_deviations.append(standard_deviation(deviation))
    return deviation_df, standard_deviations
