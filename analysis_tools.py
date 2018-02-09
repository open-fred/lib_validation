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
    object_name : String
        Name of ValidationObject (name of wind farm or region).
    validation_series : pandas.Series
            Validation feedin output time series.
    simulation_series : pandas.Series
            Simulated feedin output time series.
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

    Attributes
    ----------
    object_name : String
        Name of ValidationObject (name of wind farm or region).
    validation_series : pandas.Series
            Validation feedin output time series.
    simulation_series : pandas.Series
            Simulated feedin output time series.
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
    bias : pd.Series
        Bias of `simulation_series` from `validation_series`.
    mean_bias : Float
        Mean bias of `simulation_series` from `validation_series`.
    pearson_s_r : Float
         Pearson's correlation coeffiecient (Pearson's R) of
         `simulation_series` and `validation_series`.
    rmse : Float
        Root mean square error of `simulation_series` concerning
        `validation_series`.
    rmse_monthly : List
        Root mean square error for each month.
    standard_deviation : Float
        Standard deviation of the bias time series (`bias`).

    """
    def __init__(self, object_name, validation_series, simulation_series,
                 output_method=None, weather_data_name=None,
                 validation_name=None):
        self.object_name = object_name
        self.validation_series = validation_series
        self.simulation_series = simulation_series
        self.output_method = output_method
        self.weather_data_name = weather_data_name
        self.validation_name = validation_name

        self.bias = self.get_bias()
        self.mean_bias = self.bias.mean()
        self.rmse = self.get_rmse()
        #        self.rmse_monthly = self.get_rmse('monthly')
        self.rmse_monthly = None
        self.standard_deviation = self.get_standard_deviation(self.bias)
        if output_method is not 'annual_energy_output':
            self.pearson_s_r = self.get_pearson_s_r()
    # TODO: add some kind of percentage bias/rmse
    # TODO: add annual energy output deviation [%] as attribute (for latex output)

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

    def get_rmse(self, time_scale=None):
        r"""
        Calculate root mean square error of simulation from validation series.

        Parameters
        ----------
        time_scale : String
            The time scale the RMSE will be calculated for. Options: 'annual',
            'monthly'. Add other options if needed.

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
        return rmse

    def get_bias(self):
        r"""
        Compare two series concerning their deviation (bias).

        Returns
        -------
        pd.Series
            Deviation of simulated series from validation series.

        """
        return pd.Series(data=(self.simulation_series.values -
                               self.validation_series.values),
                         index=self.simulation_series.index)

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
        return (((self.validation_series - self.validation_series.mean()) *
                 (self.simulation_series -
                  self.simulation_series.mean())).sum() /
                np.sqrt(((self.validation_series -
                          self.validation_series.mean())**2).sum() *
                        ((self.simulation_series -
                          self.simulation_series.mean())**2).sum()))


def evaluate_feedin_time_series(
        validation_farm_list, simulation_farm_list, output_method,
        validation_name, weather_data_name, time_period=None, time_zone=None,
        temporal_output_resolution=None):
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
    time_zone : String
        Time zone information of the location of the feed-in time series of
        `validation_farm_list` and `simulation_farm_list`. Not necessary
        if the feed-in time series carry this information. Set to 'UTC' if
        time period selection is wanted in UTC time zone. Default: None.
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
    # TODO check power output graphs for time periods (feedin comparison) - why interpolation?
    validation_object_set = []
    for validation_farm, simulation_farm in zip(validation_farm_list,
                                                simulation_farm_list):
        # Select certain time steps from series if time_period is not None
        if time_period is not None:
            # Convert time series to local time zone and back after selection
            validation_series, converted_v = tools.convert_time_zone_of_index(
                validation_farm.power_output, output_time_zone='local',
                local_time_zone=time_zone)
            simulation_series, converted_s = tools.convert_time_zone_of_index(
                simulation_farm.power_output, output_time_zone='local',
                local_time_zone=time_zone)
            # Selecet time steps
            validation_series = tools.select_certain_time_steps(
                validation_series, time_period)
            simulation_series = tools.select_certain_time_steps(
                simulation_series, time_period)
            # Convert back to UTC (if there was conversion)
            if converted_v:
                validation_series.index = validation_series.index.tz_convert(
                    'UTC')
            if converted_s:
                simulation_series.index = simulation_series.index.tz_convert(
                    'UTC')
        else:
            validation_series = validation_farm.power_output
            simulation_series = simulation_farm.power_output
        if 'energy' in output_method:
            # Get validation energy output series in certain temp. resolution
            validation_series = tools.energy_output_series(
                validation_series, temporal_output_resolution, time_zone)
            # Get simulated energy output series in certain temp. resolution
            simulation_series = tools.energy_output_series(
                simulation_series, temporal_output_resolution, time_zone)
        # Initialize validation objects and append to list
        validation_object_set.append(ValidationObject(
            validation_farm.object_name, validation_series,
            simulation_series, output_method, weather_data_name,
            validation_name))
    return validation_object_set


def correlation(val_obj, sample_resolution=None):
    """


    """
    data = pd.DataFrame([val_obj.validation_series,
                         val_obj.simulation_series]).transpose()
    b = data.resample(sample_resolution).agg({'corr': lambda x: x[data.columns[0]].corr(
        x[data.columns[1]])})
    corr = b['corr'].drop(b['corr'].columns[1], axis=1)
    corr.columns = ['{0} {1}'.format(val_obj.object_name,
                    val_obj.weather_data_name)]
    return corr

if __name__ == "__main__":
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
