from input import restructure_data


def check_column_names(filename):
    column_names_check = list(restructure_data('2016-02-01+00P1M_.csv',
                                               drop_na=True))
    with open(filename) as file:
        for line in file:
            name = line.strip()
            df = restructure_data(name, drop_na=True)
            column_names = list(df)
            if column_names != column_names_check:
                print(str(name) + ' columns:')
#                print(column_names)

#check_column_names('filenames_2015.txt')
#check_column_names('filenames_2016_2017.txt')
