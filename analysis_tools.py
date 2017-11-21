import numpy as np
import pandas as pd


class ValidationObject(object):
    r"""
    
    Parameters
    ----------    
    object_name : String
        Name of ValidationObject (name of wind farm or region).
    


    """
    def __init__(self, object_name, validation_series, simulation_series):
        self.object_name = object_name
        self.validation_series = validation_series
        self.simulation_series = simulation_series
        
        self.bias = self.get_bias(validation_series, simulation_series)
        self.mean_bias = self.bias.mean()
        self.pearson_s_r = self.get_pearson_s_r(validation_series,
                                                simulation_series)
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
    
    def get_bias(self, validation_series, simulation_series):
        r"""
        Compare two series concerning their deviation (bias).
        
        Parameters
        ----------
        validation_series : pandas.Series
            Validation power output time series.
        series_simulated : pandas.Series
            Simulated power output time series.
        
        Returns
        -------
        pd.Series
            Deviation of simulated series from validation series.
    
        """
        return pd.Series(data=(simulation_series.values -
                               validation_series.values),
                         index=simulation_series.index)
    
    def get_pearson_s_r(self, validation_series, simulation_series):
        r"""
        Calculates the Pearson's correlation coeffiecient of two series.
    
        Parameters
        ----------
        validation_series : pandas.Series
            Validation power output time series.
        series_simulated : pandas.Series
            Simulated power output time series.
    
        Returns
        -------
        float
            Pearson's correlation coeffiecient (Pearson's R)
            of the input series.
    
        """
        return (((validation_series - validation_series.mean()) *
                 (simulation_series - simulation_series.mean())).sum() /
                np.sqrt(((validation_series -
                          validation_series.mean())**2).sum() *
                        ((simulation_series -
                          simulation_series.mean())**2).sum()))


def evaluate_feedin_time_series(validation_farm_list, simulation_farm_list,
                                temp_resolution_val, temp_resolution_sim,
                                temporal_output_resolution, output_method,
                                validation_name, weather_data_name): #  time_period, temporal_output_resolution
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
        
    validation_data : 
    
    weather_data : 

    Returns
    -------
    validation_object_set : List of objects
        ...

    """
    validation_object_set = []
    for farm_number in range(len(validation_farm_list)):
        # Get Series for validation in certain time scale
        validation_series = tools.energy_output_series(
            validation_farm_list[farm_number].power_output,
            temp_resolution_val, temporal_output_resolution)
        # Get simulated Series in certain time scale
        simulation_series = tools.energy_output_series(
            simulation_farm_list[farm_number].power_output,
            temp_resolution_sim, temporal_output_resolution)
        # Initialize validation objects and append to list
        validation_object = ValidationObject(
            validation_farm_list[farm_number].wind_farm_name,
            validation_series, simulation_series)
        validation_object.output_method = output_method
        validation_object.weather_data_name = weather_data_name
        validation_object.validation_name = validation_name
        validation_object_set.append(validation_object)
    # Initialize validation object for sum of wind farms
    validation_object = ValidationObject(
        'all {0} farms'.format(validation_name),
        sum([val_obj.validation_series for val_obj in validation_object_set]),
        sum([val_obj.simulation_series for val_obj in validation_object_set]))
    # TODO: these attributes should be paramters for less lines!!
    validation_object.output_method = output_method
    validation_object.weather_data_name = weather_data_name
    validation_object.validation_name = validation_name
    validation_object_set.append(validation_object)
    return validation_object_set
