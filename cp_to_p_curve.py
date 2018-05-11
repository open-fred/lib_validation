# Imports from lib_validation
from wind_farm_specifications import initialize_turbines

# Other imports
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import os


def get_curves_for_plot(turbine):
    # Load power and power coefficient curve
    power_curve = pd.DataFrame(turbine.power_curve)
    power_curve.rename(columns={col: col.replace('wind_speed',
                                                 'wind speed [m/s]') for
                                col in list(power_curve)}, inplace=True)
    power_curve.set_index('wind speed [m/s]', inplace=True)
    power_curve.columns = ['original power curve']
    power_curve = power_curve / (1 * 10 ** 6)
    power_coefficient_curve = pd.DataFrame(turbine.power_coefficient_curve)
    # Convert power coefficient curve to power curve with standard air density
    power_coefficient_curve['calculated power curve'] = (
        power_coefficient_curve['power coefficient'] * (1 / 8) * 1.225 *
        turbine.rotor_diameter ** 2 * np.pi *
        power_coefficient_curve['wind_speed'] ** 3)
    power_coefficient_curve.drop('power coefficient', axis=1, inplace=True)
    power_coefficient_curve.rename(columns={
        col: col.replace('wind_speed', 'wind speed [m/s]') for
        col in list(power_coefficient_curve)}, inplace=True)
    power_coefficient_curve.set_index('wind speed [m/s]', inplace=True)
    power_coefficient_curve = power_coefficient_curve / (1 * 10 ** 6)
    return power_curve, power_coefficient_curve


def cp_to_p_curve_single_plots():
    turbines = initialize_turbines([
        'enerconE70', 'vestasV90', 'vestasV80', 'ge_1500',
        'enerconE82_2000'])
        # These implies also most often installe turbines from dena study

    for turbine in turbines:
        power_curve, power_coefficient_curve = get_curves_for_plot(turbine)
        # Plot
        fig, ax = plt.subplots()
        power_curve.plot(ax=ax, legend=True)
        power_coefficient_curve.plot(ax=ax, legend=True)
        plt.title(turbine.object_name)
        plt.ylabel('Power in MW')
        fig.savefig(os.path.join(os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/inc/images/cp_to_p_curves',
            'cp_to_p_{0}.pdf'.format(turbine.object_name).replace(' ', '_')))
        plt.close()


def cp_to_p_curve_subplots():
    turbines = initialize_turbines([
        # 'enerconE70',
        'vestasV90',
        'vestasV80',
        'ge_1500',
        'enerconE82_2000'
    ])

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2,  sharex='col')
    axes = [ax1, ax2, ax3, ax4]
    for turbine, ax in zip(turbines, axes):
        power_curve, power_coefficient_curve = get_curves_for_plot(turbine)
        # Plot to axis
        power_curve.plot(ax=ax, legend=False)
        power_coefficient_curve.plot(ax=ax, legend=False)
        ax.annotate(turbine.object_name,
                    xy=(1, 0), xycoords='axes fraction',
                    xytext=(-1, -1), textcoords='offset points',
                    ha='right', va='bottom', fontsize=8)
        # ax.title(turbine.object_name)
    fig.text(0.05, 0.5, "Power in MW", ha="center",
             va="center", rotation=90)
    plt.legend(loc='upper right', bbox_to_anchor=(0.9, 2.45), ncol=2)
    fig.savefig(os.path.join(os.path.dirname(__file__),
            '../../../User-Shares/Masterarbeit/Latex/inc/images/cp_to_p_curves',
            'cp_to_p_subplots.pdf'))
    plt.close()

if __name__ == "__main__":
    cp_to_p_curve_single_plots()
    cp_to_p_curve_subplots()
