import pandas as pd
import analysis_tools


class TestPearson:
    def test_pearson_s_r(self):
        # Identical series
        series_1 = pd.Series([1., 2., 3.])
        series_2 = pd.Series([1., 2., 3.])
        r_exp = 1.0
        assert r_exp == analysis_tools.pearson_s_r(series_1, series_2)
        
        # Correlation < 1.0
        series_2 = pd.Series([3., 1.8, 4.])
        r_exp = 0.45392064950160177
        assert r_exp == analysis_tools.pearson_s_r(series_1, series_2)
