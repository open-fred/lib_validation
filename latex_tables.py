import pandas as pd
import os


def create_column_format(number_of_columns, position='c', index_columns='l'):
        r"""
        Creates column format for pd.DataFrame.to_latex() function.

        Parameters
        ----------
        number_of_columns : Integer
            Number of columns of the table to be created without index column.
        position : String
            Position of text in columns. For example: 'c', 'l', 'r'.

        """
        column_format = index_columns
        for i in range(number_of_columns):
            column_format = column_format.__add__(position)
        return column_format


def write_latex_output(latex_output, weather_data_list, approach_list,
                       restriction_list, val_obj_dict, annual_energy_dicts,
                       wind_farm_names, key_figures_print, output_methods,
                       path_latex_tables, filename_add_on, year, case):
    if 'annual_energy_approaches' in latex_output:
        for weather_data_name in weather_data_list:
            latex_df = pd.DataFrame()
            for outerKey, innerDict in annual_energy_dicts[
                    weather_data_name].items():
                df_part = pd.DataFrame(
                    {(innerKey, innerstKey): [values] for
                     innerKey, innerstDict in innerDict.items() if (
                         innerKey != 'measured_annual_energy' and
                         innerKey not in restriction_list) for
                     innerstKey, values in innerstDict.items()},
                    index=[outerKey.replace('wf_', 'WF ')]).round(2)
                df_part['measured', '[MWh]'] = round(
                    annual_energy_dicts[weather_data_name][outerKey][
                        'measured_annual_energy'], 2)
                latex_df = pd.concat([latex_df, df_part], axis=0)
            latex_df.sort_index(axis=1, ascending=False, inplace=True)
            latex_df.sort_index(axis=0, inplace=True)
            # Column order
            order = ['measured']
            order.extend([approach for approach in approach_list if
                          approach not in restriction_list])
            latex_df = latex_df[order]
            filename_table = os.path.join(
                path_latex_tables,
                'annual_energy_approach_{0}_{1}_{2}{3}.tex'.format(
                    case, year, weather_data_name, filename_add_on))
            latex_df.to_latex(buf=filename_table,
                              column_format=create_column_format(
                                  len(
                                      latex_df.columns), 'c'),
                              multicolumn_format='c')

    if 'annual_energy_weather' in latex_output:
        for approach in approach_list:
            if approach not in restriction_list:
                latex_df = pd.DataFrame()
                for weather_data_name in weather_data_list:
                    df_part_weather = pd.DataFrame()
                    for outerKey, innerDict in annual_energy_dicts[
                            weather_data_name].items():
                        df_part = pd.DataFrame(
                            {(weather_data_name, innerstKey): [values] for
                             innerKey, innerstDict in innerDict.items() if
                             (innerKey == approach and innerKey not in
                              restriction_list) for
                             innerstKey, values in innerstDict.items()},
                            index=[outerKey.replace('wf_', 'WF ')]).round(2)
                        if weather_data_name == weather_data_list[0]:
                            df_part['measured', '[MWh]'] = round(
                                annual_energy_dicts[weather_data_name][
                                    outerKey]['measured_annual_energy'], 2)
                        df_part_weather = pd.concat([df_part_weather, df_part],
                                                    axis=0)
                    latex_df = pd.concat([latex_df, df_part_weather], axis=1)
                # Sort columns and index
                latex_df.sort_index(axis=1, ascending=True, inplace=True)
                latex_df.sort_index(axis=0, inplace=True)
                # Column order
                order = ['measured']
                order.extend(weather_data_list)
                latex_df = latex_df[order]
                filename_table = os.path.join(
                    path_latex_tables,
                    'annual_energy_weather_{0}_{1}_{2}{3}.tex'.format(
                        case, year, approach, filename_add_on))
                latex_df.to_latex(
                    buf=filename_table, column_format=create_column_format(
                        len(latex_df.columns), 'c'), multicolumn_format='c')

    if 'annual_energy_weather_approaches' in latex_output:
        latex_df = pd.DataFrame()
        for weather_data_name in weather_data_list:
            df_part_weather = pd.DataFrame()
            for outerKey, innerDict in annual_energy_dicts[
                    weather_data_name].items():
                df_part = pd.DataFrame(
                    {(innerKey, weather_data_name): [values] for
                     innerKey, innerstDict in innerDict.items() if (
                         innerKey != 'measured_annual_energy' and
                         innerKey not in restriction_list) for
                     innerstKey, values in innerstDict.items() if
                     innerstKey == 'deviation [%]'},
                    index=[outerKey.replace('wf_', 'WF ')]).round(2)
                df_part_weather = pd.concat([df_part_weather, df_part], axis=0)
            latex_df = pd.concat([latex_df, df_part_weather], axis=1)
        # Sort columns and index
        latex_df.sort_index(axis=1, ascending=True, inplace=True)
        latex_df.sort_index(axis=0, inplace=True)
        # Column order
        latex_df = latex_df[[approach for approach in approach_list if
                             approach not in restriction_list]]
        filename_table = os.path.join(
            path_latex_tables,
            'annual_energy_weather_approaches_{0}_{1}{2}.tex'.format(
                case, year, filename_add_on))
        latex_df.to_latex(
            buf=filename_table, column_format=create_column_format(
                len(latex_df.columns), 'c'), multicolumn_format='c')

    if 'key_figures_approaches' in latex_output:
        if 'wind_speed' in case:
            unit = '[m/s]'
        else:
            unit= '[MW]'
        for weather_data_name in weather_data_list:
            latex_df = pd.DataFrame()
            for outerKey, innerDict in val_obj_dict[
                    weather_data_name].items():
                for wf_name in wind_farm_names:
                    if wf_name not in restriction_list:
                        df_wf_part = pd.DataFrame()
                        if 'rmse' in key_figures_print:
                            df_part = pd.DataFrame(
                                {('RMSE {}'.format(unit), innerKey.replace(
                                    'ity_correction', '. corr.').replace(
                                    '_wf', '').replace(
                                    'efficiency', 'eff.').replace(
                                    '_%', '').replace(
                                    'constant', 'const.').replace(
                                    '_', ' ').replace('hellman', 'H').replace(
                                    '-curve', '')):
                                 val_obj.rmse for
                                 innerKey, innerstList in innerDict.items() if
                                 innerKey not in restriction_list for
                                 val_obj in innerstList if
                                 val_obj.object_name == wf_name},
                                index=[[wf_name.replace('wf_', 'WF ').replace(
                                    'single_', '')],
                                       [outerKey.replace('_', '-')]])
                            df_wf_part = pd.concat([df_wf_part, df_part],
                                                   axis=1)
                        if 'rmse_normalized' in key_figures_print:
                            df_part = pd.DataFrame(
                                {('RMSE [%]', innerKey.replace(
                                    'ity_correction', '. corr.').replace(
                                    '_wf', '').replace(
                                    'efficiency', 'eff.').replace(
                                    '_%', '').replace(
                                    'constant', 'const.').replace(
                                    '_', ' ').replace('hellman', 'H').replace(
                                    '-curve', '')):
                                 val_obj.rmse_normalized for
                                 innerKey, innerstList in
                                 innerDict.items() for
                                 val_obj in innerstList if
                                 val_obj.object_name == wf_name},
                                index=[[wf_name.replace('wf_', 'WF ').replace(
                                    'single_', '')],
                                       [outerKey.replace('_', '-')]])
                            df_wf_part = pd.concat([df_wf_part, df_part],
                                                   axis=1)
                        if 'pearson' in key_figures_print:
                            df_part = pd.DataFrame(
                                {('Pearson coeff.', innerKey.replace(
                                    'ity_correction', '. corr.').replace(
                                    '_wf', '').replace(
                                    'efficiency', 'eff.').replace(
                                    '_%', '').replace(
                                    'constant', 'const.').replace(
                                    '_', ' ').replace('hellman', 'H').replace(
                                    '-curve', '')):
                                 val_obj.pearson_s_r for
                                 innerKey, innerstList in innerDict.items() for
                                 val_obj in innerstList if
                                 val_obj.object_name == wf_name},
                                index=[[wf_name.replace('wf_', 'WF ').replace(
                                    'single_', '')],
                                       [outerKey.replace('_', '-')]])
                            df_wf_part = pd.concat([df_wf_part, df_part],
                                                   axis=1)
                        if 'mean_bias' in key_figures_print:
                            df_part = pd.DataFrame(
                                {('mean bias {}'.format(unit),
                                  innerKey.replace(
                                      'ity_correction', '. corr.').replace(
                                      '_wf', '').replace(
                                      'efficiency', 'eff.').replace(
                                      '_%', '').replace(
                                      'constant', 'const.').replace(
                                      '_', ' ').replace('hellman', 'H').replace( # TODO: replacement function - and then dependend on case even possible
                                      '-curve', '')):
                                 val_obj.mean_bias for
                                 innerKey, innerstList in innerDict.items() for
                                 val_obj in innerstList if
                                 val_obj.object_name == wf_name},
                                index=[[wf_name.replace('wf_', 'WF ').replace(
                                    'single_', '')],
                                       [outerKey.replace('_', '-')]])
                            df_wf_part = pd.concat([df_wf_part, df_part],
                                                   axis=1)
                        if 'standard_deviation' in key_figures_print:
                            df_part = pd.DataFrame(
                                {('std deviation {}'.format(unit),
                                  innerKey.replace(
                                      'ity_correction', '. corr.').replace(
                                      '_wf', '').replace(
                                      'efficiency', 'eff.').replace(
                                      '_%', '').replace(
                                      'constant', 'const.').replace(
                                      '_', ' ').replace(
                                      'hellman', 'H').replace('-curve', '')):
                                 val_obj.standard_deviation for
                                 innerKey, innerstList in innerDict.items() for
                                 val_obj in innerstList if
                                 val_obj.object_name == wf_name},
                                index=[[wf_name.replace('wf_', 'WF ').replace(
                                    'single_', '')],
                                       [outerKey.replace('_', '-')]])
                            df_wf_part = pd.concat([df_wf_part, df_part],
                                                   axis=1)
                        latex_df = pd.concat([latex_df, df_wf_part]).round(2)
            # Sort index
            latex_df.sort_index(axis=0, inplace=True)
            filename_table = os.path.join(
                path_latex_tables,
                'key_figures_approaches_{0}_{1}_{2}{3}.tex'.format(
                    case, year, weather_data_name, filename_add_on))
            column_format = create_column_format(
                number_of_columns=(
                    len(val_obj_dict[weather_data_name][
                        output_methods[1]]) * len(key_figures_print)),
                index_columns='ll')
            latex_df.to_latex(buf=filename_table, column_format=column_format,
                              multicolumn_format='c')

    if 'key_figures_weather' in latex_output:
        if 'wind_speed' in case:
            unit = '[m/s]'
        else:
            unit= '[MW]'
        for approach in approach_list:
            if approach not in restriction_list:
                latex_df = pd.DataFrame()
                for weather_data_name in weather_data_list:
                    df_part_weather = pd.DataFrame()
                    for outerKey, innerDict in val_obj_dict[
                            weather_data_name].items():
                        if outerKey != 'half_hourly':
                            for wf_name in wind_farm_names:
                                if wf_name not in restriction_list:
                                    df_wf_part = pd.DataFrame()
                                    if 'rmse' in key_figures_print:
                                        df_part = pd.DataFrame(
                                            {('RMSE {}'.format(unit),
                                              weather_data_name):
                                             val_obj.rmse for
                                             innerKey, innerstList in
                                             innerDict.items() for
                                             val_obj in innerstList if
                                             val_obj.object_name == wf_name},
                                            index=[[
                                                wf_name.replace(
                                                    'wf_', 'WF ').replace(
                                                    'single_', '')],
                                                [outerKey.replace('_', '-')]])
                                        df_wf_part = pd.concat(
                                            [df_wf_part, df_part], axis=1)
                                    if 'rmse_normalized' in key_figures_print:
                                        df_part = pd.DataFrame(
                                            {('RMSE [%]',
                                              weather_data_name):
                                             val_obj.rmse_normalized for
                                             innerKey, innerstList in
                                             innerDict.items() for
                                             val_obj in innerstList if
                                             val_obj.object_name == wf_name},
                                            index=[[
                                                wf_name.replace(
                                                    'wf_', 'WF ').replace(
                                                    'single_', '')],
                                                [outerKey.replace('_', '-')]])
                                        df_wf_part = pd.concat(
                                            [df_wf_part, df_part], axis=1)
                                    if 'pearson' in key_figures_print:
                                        df_part = pd.DataFrame(
                                            {('Pearson coeff.',
                                              weather_data_name):
                                             val_obj.pearson_s_r for
                                             innerKey, innerstList in
                                             innerDict.items() for
                                             val_obj in innerstList if
                                             val_obj.object_name == wf_name},
                                            index=[[
                                                wf_name.replace(
                                                    'wf_', 'WF ').replace(
                                                    'single_', '')],
                                                [outerKey.replace('_', '-')]])
                                        df_wf_part = pd.concat(
                                            [df_wf_part, df_part], axis=1)
                                    if 'mean_bias' in key_figures_print:
                                        df_part = pd.DataFrame(
                                            {('mean bias {}'.format(unit),
                                              weather_data_name):
                                             val_obj.mean_bias for
                                             innerKey, innerstList in
                                             innerDict.items() for
                                             val_obj in innerstList if
                                             val_obj.object_name == wf_name},
                                            index=[[
                                                wf_name.replace(
                                                    'wf_', 'WF ').replace(
                                                    'single_', '')],
                                                [outerKey.replace('_', '-')]])
                                        df_wf_part = pd.concat(
                                            [df_wf_part, df_part], axis=1)
                                    if ('standard_deviation' in
                                            key_figures_print):
                                        df_part = pd.DataFrame(
                                            {('std deviation {}'.format(unit),
                                              weather_data_name):
                                             val_obj.standard_deviation for
                                             innerKey, innerstList in
                                             innerDict.items() for
                                             val_obj in innerstList if
                                             val_obj.object_name == wf_name},
                                            index=[[
                                                wf_name.replace(
                                                    'wf_', 'WF ').replace(
                                                        'single_', '')],
                                                [outerKey.replace('_', '-')]])
                                        df_wf_part = pd.concat(
                                            [df_wf_part, df_part], axis=1)
                                    df_part_weather = pd.concat(
                                        [df_part_weather, df_wf_part])
                    latex_df = pd.concat([latex_df, df_part_weather],
                                         axis=1).round(2)
            # Sort columns and index
            latex_df.sort_index(axis=1, inplace=True)
            latex_df.sort_index(axis=0, inplace=True)
            filename_table = os.path.join(
                path_latex_tables,
                'Key_figures_weather_{0}_{1}_{2}{3}.tex'.format(
                    case, year, approach, filename_add_on))
            column_format = create_column_format(
                number_of_columns=(
                    len(val_obj_dict[weather_data_name][
                        output_methods[1]]) * len(key_figures_print)),
                index_columns='ll')
            latex_df.to_latex(buf=filename_table, column_format=column_format,
                              multicolumn_format='c')
