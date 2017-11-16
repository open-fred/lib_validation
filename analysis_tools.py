import numpy as np
import pandas as pd

def standard_deviation(data_series):
    r"""

    Calculate standard deviation of a data series.

    Parameters
    ----------
    data_series : list or pandas.Series
        Input data series of which the standard deviation will be calculated.

    Return
    ------
    float
        Standard deviation of the input data series.

    """
    average = sum(data_series) / len(data_series)
    variance = sum((data_series[i] - average)**2
                   for i in range(len(data_series))) / len(data_series)
    return np.sqrt(variance)


def compare_series_std_deviation(series_validation, series_simulated):
    r"""
    Compare two series concerning their deviation and standard deviation.
    
    Parameters
    ----------
    series_validation : pandas.Series
        Validation power output time series.
    series_simulated : pandas.Series
        Simulated power output time series.
    
    Returns
    -------
    deviation : pd.Series
        Deviation of simulated series from validation series.
    std_deviation : float
        Standard deviation of simulated series from validation series.

    """
    deviation = pd.Series(data=(series_validation.values -
                                series_simulated.values),
                          index=series_simulated.index)
    std_deviation = standard_deviation(deviation)
    return deviation, std_deviation
    

def compare_series_std_deviation_multiple(series_validation_list,
                                          series_simulated_list, column_names):
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
        deviation, std_deviation = compare_series_std_deviation(
            series_validation_list[farm_number],
            series_simulated_list[farm_number])
        deviation_df_part = pd.DataFrame(
            data=deviation, index=series_validation_list[farm_number].index,
            columns=[column_names[farm_number]])
        deviation_df = pd.concat([deviation_df, deviation_df_part], axis=1)
        standard_deviations.append(std_deviation)
    return deviation_df, standard_deviations