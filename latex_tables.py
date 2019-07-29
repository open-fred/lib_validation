import pandas as pd
import os


def create_column_format(number_of_columns, position='c', index_columns='l'):
        r"""
        Creates column format for pd.DataFrame.to_latex() function.

        Parameters
        ----------
        number_of_columns : integer
            Number of columns of the table to be created exclusive index
            column.
        position : string
            Position of text in columns. For example: 'c', 'l', 'r'.
            Default: 'c'.
        index_columns : string

        """
        column_format = index_columns
        for i in range(number_of_columns):
            column_format = column_format.__add__(position)
        return column_format


def replacement_of_characters(string, replacement_list):
    r"""
    Applies the replace() function on a string.

    Parameters
    ----------
    string : string
        Replace() function is applied on `string`.
    replacement_list : list
        Contains tuples (string, string) with replacment characters.

    """
    for replacement in replacement_list:
        string = string.replace(replacement[0], replacement[1])
    return string

