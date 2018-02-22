

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


def get_columns(column_names, multiplikator):
    r"""
    Produces columns for pd.DataFrame needed for latex output.

    Parameters
    ----------
    column_names : List
        Contains column names (String).
    multiplikator : Integer
        Frequency of column names.

    Returns
    -------
    columns : List
        Column names for pd.DataFrame needed for latex output.

    """
    columns = []
    for column_name in column_names:
        columns.extend([column_name for i in range(multiplikator)])
    return columns


def get_data(validation_sets, data_names, object_position, length):
    r"""
    Retruns list containing data for pd.DataFrame needed for latex output.

    Paramters
    ---------
    validation_sets : List
        Contains lists of :class:`~.analysis_tools.ValidationObject` objects.
    data_names : List
        Contains specification of data (Strings) to be displayed.
    object_position : Integer
        Position of object in lists in `validation_sets`.
    length : Integer
        Lenth of TODO: add # might be changed

    Returns
    -------
    data : List
        Data for pd.DataFrame needed for latex output.

    """
    data = []
    if 'RMSE' in data_names:
        data.extend([round(validation_sets[j][object_position].rmse, 2)
                     for j in range(length)])
    if 'Pr' in data_names:
        data.extend([round(validation_sets[j][object_position].pearson_s_r, 2)
                     for j in range(length)])
    if 'mean bias' in data_names:
        data.extend([round(validation_sets[j][object_position].mean_bias, 2)
                     for j in range(length)])
    if 'std. dev.' in data_names:
        data.extend([round(
            validation_sets[j][object_position].standard_deviation, 2)
            for j in range(length)])
    return data
