import numpy as np
import pandas as pd
import tools


class ValidationObject(object):
    r"""

    Parameters
    ----------
    object_name : String
        Name of ValidationObject (name of wind farm or region).
    validation_series : pandas.Series
            Validation feedin output time series.
    simulation_series : pandas.Series
            Simulated feedin output time series.
    weather_data_name : String
        Indicates the origin of the weather data of the simulated feedin time
        series. This parameter will be set as an attribute of ValidationObject
        and is used for giving filenames etc.
    validation_name : String
        Indicates the origin of the validation feedin time series.
        This parameter will be set as an attribute of ValidationObject and is
        used for giving filenames etc.

    Attributes
    ----------
    object_name : String
        Name of ValidationObject (name of wind farm or region).
    validation_series : pandas.Series
            Validation feedin output time series.
    simulation_series : pandas.Series
            Simulated feedin output time series.
    weather_data_name : String
        Indicates the origin of the weather data of the simulated feedin time
        series. This parameter will be set as an attribute of ValidationObject
        and is used for giving filenames etc.
    validation_name : String
        Indicates the origin of the validation feedin time series.
        This parameter will be set as an attribute of ValidationObject and is
        used for giving filenames etc.
    bias : pd.Series
        Deviation of a simulated feedin time series from a validation time
        series.
    mean_bias : Float
        Mean deviation of a simulated feedin time series from a validation time
        series.
    pearson_s_r : Float
         Pearson's correlation coeffiecient (Pearson's R) of two time series.
    rmse : Float
        Root mean square error ...... # TODO: implement rmse
    standard_deviation : Float
        Standard deviation of the bias (deviation) time series.
    output_method : String
        Specification of form of time series to be validated. For example:
        'hourly_energy_output'.
    """
    def __init__(self, object_name, validation_series, simulation_series,
                 weather_data_name=None, validation_name=None):
        self.object_name = object_name
        self.validation_series = validation_series
        self.simulation_series = simulation_series
        self.weather_data_name = weather_data_name
        self.validation_name = validation_name

        self.bias = self.get_bias(validation_series, simulation_series)
        self.mean_bias = self.bias.mean()
        self.pearson_s_r = self.get_pearson_s_r(validation_series,
                                                simulation_series)
        self.rmse = None
        self.standard_deviation = self.get_standard_deviation(self.bias)
        self.standard_deviation_from_zero = (
            self.get_standard_deviation_from_zero(self.bias))
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

        """
        average = data_series.mean()
        variance = ((data_series - average)**2).sum() / len(data_series)
        return np.sqrt(variance)

    def get_standard_deviation_from_zero(self, data_series):
        r"""
        Calculate standard deviation of a data series from the value zero.

        This makes sense for the purpose of validating a time series as
        positive values might compensate negative values.

        Parameters
        ----------
        data_series : list or pandas.Series
            Input data series (data points) of which the standard deviation
            will be calculated.

        Return
        ------
        float
            Standard deviation from zero of the input data series.

        """
        variance = ((data_series - 0)**2).sum() / len(data_series)
        return np.sqrt(variance)

    def get_bias(self, validation_series, simulation_series):
        r"""
        Compare two series concerning their deviation (bias).

        Parameters
        ----------
        validation_series : pandas.Series
            Validation feedin output time series.
        simulation_series : pandas.Series
            Simulated feedin output time series.

        Returns
        -------
        pd.Series
            Deviation of simulated series from validation series.

        """
        return pd.Series(data=(simulation_series.values -
                               validation_series.values),
                         index=simulation_series.index)

    def get_monthly_mean_biases(self):
        r"""


        """
        mean_biases = []
        for month in range(12):
            mean_bias = self.bias['{0}-{1}'.format(
                self.bias.index[10].year, month + 1)].mean()
            mean_biases.append(mean_bias)
        return mean_biases

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
                                output_method, validation_name,
                                weather_data_name, time_period=None,
                                temporal_output_resolution=None): #  time_period
    # TODO: possibility of selecting time periods (only mornings, evenings...)
    # + other scales? months?
    r"""
    Evaluate feedin time series concerning validation feedin time series.

    The simulated time series of each farm in `simulation_farm_list` is being
    compared to the corresponding validation time series of the farm in
    `validation_farm_list`. For later usage for each of these pairs a
    :class:`~.analysis_tools.ValidationObject` object is created. Finally, a
    :class:`~.analysis_tools.ValidationObject` object of the sum of the feedin
    time series is created.

    Parameters
    ----------
    validation_farm_list : List of objects
        List of :class:`~.wind_farm.WindFarm` objects representing wind farms
        for validation.
    simulation_farm_list : List of objects
        List of :class:`~.wind_farm.WindFarm` objects representing simulated
        wind farms. Must be in the same order as `validation_farm_list`.
    temp_resolution_val : Float or Integer
        Temporal resolution of valdation time series in minutes.
    temp_resolution_sim : Float or Integer
        Temporal resolution of simulation time series in minutes.
    output_method : String
        Specification of form of time series to be validated. For example:
        'hourly_energy_output'. This parameter will be set as an attribute of
        ValidationObject and is used for giving filenames etc.
    validation_name : String
        Indicates the origin of the validation feedin time series.
        This parameter will be set as an attribute of ValidationObject and is
        used for giving filenames etc.
    weather_data_name : String
        Indicates the origin of the weather data of the simulated feedin time
        series. This parameter will be set as an attribute of ValidationObject
        and is used for giving filenames etc.
    time_period : Tuple (Int, Int)
        Hourly time period to be selected from time series (h, h).
        Default: None.
    temporal_output_resolution : String
        Specification of temporal ouput resolution in the form of 'H', 'M',
        etc. for energy output series. Not needed for power_output_series.
        For more information see function energy_output_series() in the
        ``tools`` module. Default: None.

    Returns
    -------
    validation_object_set : List of objects
        A set of :class:`~.analysis_tools.ValidationObject` objects.

    """
    # TODO check power output graphs (feedin comparison) - why interpolation?
    validation_object_set = []
    for farm_number in range(len(validation_farm_list)):
        # Select certain time steps from series
        if time_period is not None:
            validation_series = tools.select_certain_time_steps(
                    validation_farm_list[farm_number].power_output,
                    time_period)
            simulation_series = tools.select_certain_time_steps(
                    simulation_farm_list[farm_number].power_output,
                    time_period)
        else:
            validation_series = validation_farm_list[farm_number].power_output
            simulation_series = simulation_farm_list[farm_number].power_output
        if 'energy' in output_method:
            # Get validation energy output series in certain temp. resolution
            validation_series = tools.energy_output_series(
                validation_series, temp_resolution_val,
                temporal_output_resolution)
            # Get simulated energy output series in certain temp. resolution
            simulation_series = tools.energy_output_series(
                simulation_series, temp_resolution_sim,
                temporal_output_resolution)
        # Initialize validation objects and append to list
        validation_object = ValidationObject(
            validation_farm_list[farm_number].wind_farm_name,
            validation_series, simulation_series, weather_data_name,
            validation_name)
        validation_object.output_method = output_method
        validation_object_set.append(validation_object)
    # Initialize validation object for sum of wind farms
    validation_object = ValidationObject(
        'all {0} farms'.format(validation_name),
        sum([val_obj.validation_series for val_obj in validation_object_set]),
        sum([val_obj.simulation_series for val_obj in validation_object_set]),
        weather_data_name, validation_name)
    validation_object.output_method = output_method
    validation_object_set.append(validation_object)
    return validation_object_set
