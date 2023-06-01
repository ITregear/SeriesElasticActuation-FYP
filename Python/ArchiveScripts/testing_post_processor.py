# Author: ivantregear
# Date Created: 07/12/2022
# Description:

# When I wrote this code only got I and knew how it worked.
# Now only god knows it.


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import scipy.signal as sg
import scipy.stats as st


def bode(time, input_arr, output_arr):
    input_fft = np.fft.fft(np.array(input_arr))
    output_fft = np.fft.fft(np.array(output_arr))

    time = np.array(time)

    t = time[-1]
    n = len(time)

    freq = np.arange(0, n / (2 * t), 1 / t)

    tf = output_fft / input_fft

    mag = 20 * np.log10(np.absolute(tf))[:len(freq)]
    phase = np.degrees(np.angle(tf))[:len(freq)]

    mag = sg.savgol_filter(mag, 99, 1)
    phase = sg.savgol_filter(phase, 99, 1)

    mag_peak = mag.max()
    mag_3db = mag_peak - 3
    idx_3db = np.where(mag <= mag_3db)[0][0]
    bandwidth = freq[idx_3db]

    return freq, mag, phase, bandwidth


def step_characteristics(time_arr, input_arr, output_arr):
    time_arr = np.array(time_arr)
    input_arr = np.array(input_arr)
    output_arr = np.array(output_arr)

    # GENERAL DEFINITIONS
    initial_input = input_arr[0]  # Initial value of input array, always zero
    step_input = input_arr[-1]  # Final value of input array, step amplitude
    step_index = np.where(input_arr == step_input)[0][0]  # Index at which step is requested (always at t=3s)
    step_time = time_arr[step_index]  # Time at which step is requested (always 3)

    t1_index = np.where(time_arr >= 1 / 3 * step_time)[0][0]  # Index at which t=1s
    t2_index = np.where(time_arr >= 2 / 3 * step_time)[0][0]  # Index at which t=2s
    t3_index = np.where(time_arr >= 4 / 3 * step_time)[0][0]  # Index at which t=4s
    t4_index = np.where(time_arr >= 5 / 3 * step_time)[0][0]  # Index at which t=5s

    initial_output = np.mean(output_arr[t1_index:t2_index])
    final_output = np.mean(output_arr[t3_index:t4_index])

    # RISE TIME
    output_0_1 = 0.1 * final_output  # 10% of final value
    output_0_9 = 0.9 * final_output  # 90% of final value

    t_rise_0_1 = time_arr[np.where(output_arr >= output_0_1)[0][0]]  # Time at which output is 10% of final value
    t_rise_0_9 = time_arr[np.where(output_arr >= output_0_9)[0][0]]  # Time at which output is 90% of final value

    rise_time = t_rise_0_9 - t_rise_0_1

    # PERCENTAGE_OVERSHOOT
    output_max = np.max(output_arr)
    percentage_overshoot = (output_max - final_output) / final_output * 100

    # STEADY STATE ERROR
    error_ss = (step_input - final_output) / step_input * 100

    return rise_time, percentage_overshoot, error_ss


def data_viewer():
    test_type = "sr"
    data_processing = "single"
    data_id = 55  # Change to desired TEST ID
    plot_type = "both"

    test_path = "../TestData"

    if test_type == "bw":
        test_path += "\\OriginalMotorBandwidth"
    if test_type == "sr":
        if data_processing == "torque_constant":
            test_path += "\\OriginalMotorStepResponse"
        elif data_processing == "single":
            test_path += "\\OriginalMotorStepResponseAdjusted"

    if data_processing == "single":
        for file in os.listdir(test_path):
            if int(file.split("-")[3]) == data_id:
                filename = file

        amplitude = float(filename.split("-")[1])
        max_freq = int(filename.split("-")[4])

        df = pd.read_csv(test_path + "\\" + filename)

        if test_type == "bw":
            if plot_type == "time_domain" or plot_type == "both":
                fig1 = plt.figure(figsize=(12, 6))
                plt.suptitle("Torque Control Frequency Response at {}Nm Amplitude".format(amplitude))
                plt.title("Test ID: {}".format(data_id), fontsize=8)
                plt.xlabel("Time [s]")
                plt.ylabel("Torque [Nm]")
                plt.grid()
                plt.plot(df['time'], df['torque_in'], label="Input")
                plt.plot(df['time'], df['torque_out'], label="Output")
                plt.legend()
                fig1.show()
            if plot_type == "frequency_domain" or plot_type == "both":
                freq, mag, phase, bandwidth = bode(df['time'], df['torque_in'], df['torque_out'])

                fig2, ax = plt.subplots(nrows=2, ncols=1, figsize=(12, 6))
                plt.suptitle(
                    "Torque Control Frequency Response at {}Nm Amplitude, up to {}Hz".format(amplitude, max_freq))
                ax[0].set_title("Test ID: {}".format(data_id), fontsize=8)
                ax[0].set_xlabel("Frequency [Hz]")
                ax[0].set_ylabel("Magnitude [dB]")
                ax[1].set_xlabel("Frequency [Hz]")
                ax[1].set_ylabel("Phase [deg]")
                ax[0].set_xscale('log')
                ax[1].set_xscale('log')
                ax[0].grid()
                ax[1].grid()
                ax[0].plot(freq, mag, c='r')
                ax[1].plot(freq, phase, c='r')
                ax[0].set_xlim([0.1, max_freq])
                ax[1].set_xlim([0.1, max_freq])
                plt.tight_layout()
                fig2.show()
        if test_type == "sr":

            t_demanded = round(np.array(df['torque_in'])[-1], 2)

            t_rise, overshoot, e_ss = step_characteristics(df['time'], df['torque_in'], df['torque_out'])

            fig1, ax = plt.subplots(figsize=(12, 6))
            plt.suptitle("Torque Control Step Response at {}Nm ({}A) Amplitude".format(t_demanded, amplitude))
            plt.title("Test ID: {}".format(data_id), fontsize=8)
            plt.xlabel("Time [s]")
            plt.ylabel("Torque [Nm]")
            plt.grid()
            plt.plot(df['time'], df['torque_in'], label="Input")
            plt.plot(df['time'], df['torque_out'], label="Output")
            plt.text(0.015, 0.8, "Rise Time: {}s\nOvershoot: {}%\nSteady State Error: {}%".format(round(t_rise, 4),
                                                                                                  round(overshoot, 3),
                                                                                                  round(e_ss, 2)),
                     transform=ax.transAxes, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='grey',
                                                                            boxstyle='round,pad=0.5', alpha=0.8,
                                                                            linewidth=0.5))
            plt.legend()
            fig1.show()
        plt.show()

    elif data_processing == "torque_constant":

        write_adjusted_files = False  # True will overwrite all files in OriginalMotorStepResponseAdjusted

        torque_dictionary = {'in_0': [],
                             'in_1': [],
                             'out_0': [],
                             'out_1': []}

        for file in os.listdir(test_path):
            df = pd.read_csv(test_path + "\\" + file)
            length = len(df['torque_out'])
            initial_output = np.mean(np.array(df['torque_out'])[int(1 / 6 * length):int(2 / 6 * length)])
            final_output = np.mean(np.array(df['torque_out'])[int(4 / 6 * length):int(5 / 6 * length)])
            initial_input = np.array(df['torque_in'])[0]
            final_input = np.array(df['torque_in'])[-1]

            torque_dictionary['in_0'] += [initial_input]
            torque_dictionary['in_1'] += [final_input]
            torque_dictionary['out_0'] += [initial_output]
            torque_dictionary['out_1'] += [final_output]

        input_torque_amplitudes = np.array(torque_dictionary['in_1'])
        output_torque_amplitudes = np.array(torque_dictionary['out_1']) - np.array(torque_dictionary['out_0'])

        a, b, r_value, _, _ = st.linregress(input_torque_amplitudes, output_torque_amplitudes)

        torque_constant = a  # Nm/A
        min_current = -b / a  # A
        min_torque = torque_constant * min_current

        print(torque_constant, min_current, min_torque)

        if write_adjusted_files:
            for i, file in enumerate(os.listdir(test_path)):
                df = pd.read_csv(test_path + "\\" + file)
                df['torque_out'] = (np.array(df['torque_out']) - torque_dictionary['out_0'][i])
                df['torque_in'] = np.array(df['torque_in']) * torque_constant

                df.to_csv("TestData/OriginalMotorStepResponseAdjusted" + "/" + file)

        plt.suptitle("Output Torque vs Input Current")
        plt.title("Torque Constant across {}-{}Nm is {}Nm/A with R={}".format(round(input_torque_amplitudes.min(), 2),
                                                                              round(input_torque_amplitudes.max()),
                                                                              round(torque_constant, 3),
                                                                              round(r_value, 4)), fontsize=10)
        plt.xlabel("Input Current [A]")
        plt.ylabel("Output Torque [Nm]")
        plt.grid()
        plt.scatter(input_torque_amplitudes, output_torque_amplitudes, marker='x', color='r')
        plt.plot(input_torque_amplitudes, a*input_torque_amplitudes + b, linestyle='--', color='black')
        plt.xlim([0, None])
        plt.ylim([0, None])
        plt.show()


def results_viewer():

    plot_results = True
    save_results = False

    test_path = "../TestData"

    bandwidth_test_path = test_path + "\\OriginalMotorBandwidth"

    bandwidth_data = {'torque': [],
                      'bandwidth': []}

    for file in os.listdir(bandwidth_test_path):
        df = pd.read_csv(bandwidth_test_path + "/" + file)
        _, _, _, bandwidth = bode(df['time'], df['torque_in'], df['torque_out'])
        amplitude = round(max(df['torque_in']) / 1.393, 2)

        bandwidth_data['torque'] += [amplitude]
        bandwidth_data['bandwidth'] += [bandwidth]

    step_test_path = test_path + "\\OriginalMotorStepResponseAdjusted"

    step_data = {'torque': [],
                 'rise_time': [],
                 'overshoot': [],
                 'error': []}

    for file in os.listdir(step_test_path):
        df = pd.read_csv(step_test_path + "/" + file)
        rise_time, overshoot, error = step_characteristics(df['time'], df['torque_in'], df['torque_out'])
        amplitude = round(max(df['torque_in']), 2)

        step_data['torque'] += [amplitude]
        step_data['rise_time'] += [rise_time]
        step_data['overshoot'] += [overshoot]
        step_data['error'] += [error]

    if save_results:
        results_path = "../TestResults"

        df_bandwidth = pd.DataFrame.from_dict(bandwidth_data)
        df_step = pd.DataFrame.from_dict(step_data)

        df_bandwidth.to_csv(results_path + "/" + "BandwidthResults.csv")
        df_step.to_csv(results_path + "/" + "StepResponseResults.csv")

    if plot_results:
        fig, ax = plt.subplots(nrows=2, ncols=2)

        # Bandwidth vs Torque Amplitude
        ax[0, 0].scatter(bandwidth_data['torque'], bandwidth_data['bandwidth'], marker='x', color='red')
        ax[0, 0].set_ylabel("Bandwidth [Hz]")
        ax[0, 0].set_title("Bandwidth vs Torque Amplitude")

        # Rise Time vs Torque Step
        ax[0, 1].scatter(step_data['torque'], step_data['rise_time'], marker='x', color='red')
        ax[0, 1].set_ylabel("Rise Time [s]")
        ax[0, 1].set_title("Rise Time vs Torque Amplitude")

        # Overshoot vs Torque Step
        ax[1, 0].scatter(step_data['torque'], step_data['overshoot'], marker='x', color='red')
        ax[1, 0].set_ylabel("Percentage Overshoot [%]")
        ax[1, 0].set_title("Percentage Overshoot vs Torque Amplitude")

        # Error vs Torque Step
        ax[1, 1].scatter(step_data['torque'], step_data['error'], marker='x', color='red')
        ax[1, 1].set_ylabel("Steady State Error [%]")
        ax[1, 1].set_title("Steady State Error vs Torque Amplitude")

        for axis in ax.flatten():
            axis.grid()
            axis.set_xlim([0, None])
            axis.set_ylim([0, None])
            axis.set_xlabel("Torque Amplitude [Nm]")

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":

    viewData = False
    viewResults = True

    if viewData:
        data_viewer()
    if viewResults:
        results_viewer()
