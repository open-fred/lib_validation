import pandas as pd
import analysis_tools


class TestValidationObject:
    def test_functions(self):
        series_1 = pd.Series([1., 2., 3.])
        series_2 = pd.Series([1., 2., 3.])
        series_3 = pd.Series([3., 4., 5.])
        series_4 = pd.Series([2., 4., 6.])
        series_5 = pd.Series([2., 4., 5.])
        # Identical series
        val_obj_1 = analysis_tools.ValidationObject('Test', series_1, series_2)
        r_exp = 1.0
        mean_bias_exp = 0
        std_dev_exp = 0
        rmse_exp = 0
        assert r_exp == val_obj_1.pearson_s_r
        assert mean_bias_exp == val_obj_1.mean_bias
        assert std_dev_exp == val_obj_1.standard_deviation
        assert rmse_exp == val_obj_1.rmse

        # Simulated series fully correlate but with bias
        val_obj_2 = analysis_tools.ValidationObject('Test', series_1, series_3)
        r_exp = 1.0
        mean_bias_exp = 2.0
        std_dev_exp = 0
        rmse_exp = 2.0
        assert r_exp == val_obj_2.pearson_s_r
        assert mean_bias_exp == val_obj_2.mean_bias
        assert std_dev_exp == val_obj_2.standard_deviation
        assert rmse_exp == val_obj_2.rmse

        # Simulated series = 2 * validation series
        val_obj_3 = analysis_tools.ValidationObject('Test', series_1, series_4)
        r_exp = 1.0
        mean_bias_exp = 2.0
        std_dev_exp = 0.81649658092772603
        rmse_exp = 2.1602468994692869
        assert r_exp == val_obj_3.pearson_s_r
        assert mean_bias_exp == val_obj_3.mean_bias
        assert std_dev_exp == val_obj_3.standard_deviation
        assert rmse_exp == val_obj_3.rmse
     
#        # Not linear
#        val_obj_4 = analysis_tools.ValidationObject('Test', series_1, series_5)
#        r_exp = 1.0
#        mean_bias_exp = 2.0
#        std_dev_exp = 0.81649658092772603
#        print(val_obj_4.get_standard_deviation_from_zero(val_obj_4.bias))
#        assert r_exp == val_obj_4.pearson_s_r
#        assert mean_bias_exp == val_obj_4.mean_bias
#        assert std_dev_exp == val_obj_4.standard_deviation

#        # Correlation < 1.0
#        series_2 = pd.Series([3., 1.8, 4.])
#        r_exp = 0.45392064950160177
#        assert r_exp == analysis_tools.pearson_s_r(series_1, series_2)
