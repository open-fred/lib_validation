import numpy as np
import pandas as pd


class ValidationObject(object):
    r"""


    """
    def __init__(self, wind_farm_name, series_validation, series_simulation):
        self.wind_farm_name = wind_farm_name
        self.series_validation = series_validation
        self.series_simulation = series_simulation
        
        self.bias = self.get_bias(series_validation, series_simulation)
        self.mean_bias = self.bias.mean()
        self.pearson_s_r = self.get_pearson_s_r(series_validation,
                                                series_simulation)
        self.rmse = None
        self.standard_deviation = self.get_standard_deviation(self.bias)
        
        self.weather_data_name = None
        self.validation_name = None
        self.output_method = None

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
        average : float
            Arithmetric average of `data_series`.
        """
        average = data_series.mean()
        variance = ((data_series - average)**2).sum() / len(data_series)
        return np.sqrt(variance) 
    
    def get_bias(self, series_validation, series_simulation):
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
    
    
    def get_pearson_s_r(self, series_validation, series_simulation):
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


def evaluate_feedin_time_series(validation_farm_list, simulation_farm_list,
                                temp_resolution_val, temp_resolution_sim,
                                temporal_output_resolution, output_method): #  time_period, temporal_output_resolution
    # TODO: first only hourly energy output -  then add other scales (months, days?) 
    #       + power output
    #       + possibility of selecting time periods (only mornings, evenings...)
    r"""
    Evaluate feedin time series concerning a validation feedin time series.

    Multiple series are being compared to their validation series by using the
    validation methods specified in the parameters. 

    Parameters
    ----------
    validation_farm_list : List of objects
        List of :class:`~.wind_farm.WindFarm` objects representing wind farms
        for validation.
    simulation_farm_list : List of objects
        List of :class:`~.wind_farm.WindFarm` objects representing simulated
        wind farms. Must be in the same order as `validation_farm_list`.
    temp_resolution_val :
    
    temp_resolution_sim :
    
    temporal_output_resolution : 
    
    output_method : 
        
 

    Returns
    -------
    validation_object_set : List of objects
        ...

    """
    validation_object_set = []
    for farm_number in range(len(validation_farm_list)):
        # Get Series for validation in certain time scale
        series_validation = tools.energy_output_series(
            validation_farm_list[farm_number].power_output,
            temp_resolution_val, temporal_output_resolution)
        # Get simulated Series in certain time scale
        series_simulation = tools.energy_output_series(
            simulation_farm_list[farm_number].power_output,
            temp_resolution_sim, temporal_output_resolution)
        # Initialize validation objects and append to list
        validation_object = ValidationObject(
            validation_farm_list[farm_number].wind_farm_name,
            series_validation, series_simulation)
        validation_object.output_method = output_method
        validation_object_set.append(validation_object)
    return validation_object_set
