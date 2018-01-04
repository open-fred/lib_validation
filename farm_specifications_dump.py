import pickle
import os



if __name__ == "__main__":
    save_folder = os.path.join(os.path.dirname(__file__), 'helper_files')
    filenames = ['farm_specification_argenetz']
    for filename in filenames:
        file = os.path.join(save_folder, filename)
