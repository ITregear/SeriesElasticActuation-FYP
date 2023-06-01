# Author: ivantregear
# Date Created: 28/02/2023
# Description: 

# When I wrote this code only God I and knew how it worked.
# Now only god knows it.

import matplotlib.pyplot as plt
import matplotlib
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os
import pandas as pd
import numpy as np
import scipy.stats as st
import scipy.signal as sig
import sys


class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)


def draw_figure_w_toolbar(canvas, fig, canvas_toolbar):
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    if canvas_toolbar.children:
        for child in canvas_toolbar.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(fig, master=canvas)
    figure_canvas_agg.draw()
    toolbar = Toolbar(figure_canvas_agg, canvas_toolbar)
    toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)


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

    mag = sig.savgol_filter(mag, 99, 1)
    phase = sig.savgol_filter(phase, 99, 1)

    mag_dc = mag[0]
    mag_3db = mag_dc - 3 * 1.5
    idx_3db = np.where(mag >= mag_3db)[0]

    phase_min_freq = freq[np.argmin(phase)]
    phase1 = phase[freq <= phase_min_freq]
    phase2 = phase[freq >= phase_min_freq]

    phase_dc = np.max(phase1)

    freq_upperbound_idx = np.where(phase2 >= phase_dc)[0][0] + len(phase1)
    freq_upperbound = freq[freq_upperbound_idx]

    bandwidth = freq[idx_3db[idx_3db <= freq_upperbound_idx][-1]]

    return freq, mag, phase, bandwidth


def first_order_system_identification(time, xt, yt):
    n = len(time)

    y_ss = np.mean(yt[int(4 / 6 * n): int(5 / 6 * n)])
    x_ss = xt[-1]

    k = y_ss / x_ss  # Steady state gain (A_0)

    y_ss_63 = 0.63 * y_ss  # t=tau
    y_ss_86 = 0.86 * y_ss  # t=2*tau
    y_ss_95 = 0.95 * y_ss  # t=3*tau

    t_63 = time[np.where(yt >= y_ss_63)[0][0]] - 3
    t_86 = time[np.where(yt >= y_ss_86)[0][0]] - 3
    t_95 = time[np.where(yt >= y_ss_95)[0][0]] - 3

    tau = (t_63 + t_86 / 2 + t_95 / 3) / 3

    return k, tau


def find_nearest_idx(array, value):
    array = np.array(array)
    idx = (np.abs(array - value)).argmin()
    return idx


def group(x, y):
    x_group, y_group = [], []

    last_x = None
    y_temp = None

    for i in range(len(x)):
        if x[i] != last_x:
            x_group += [x[i]]
            y_temp = []
            y_temp += [y[i]]
        else:
            y_temp += [y[i]]
        if x[i] != last_x or i == len(x):
            y_group += [y_temp]

        last_x = x[i]

    return np.array(x_group), np.array(y_group)


def raw_stiffness_plot(fig, path, filename):

    fig.set_size_inches(18, 6, forward=True)
    torque_amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])
    spring_id = int(filename.split("-")[4])
    df = pd.read_csv(path + "\\" + filename)

    m, c, r_value, _, _ = st.linregress(np.array(df['displacement']), np.array(df['torque_out']))

    limits = np.array([np.min(df['displacement']), np.max(df['displacement'])])
    torque_bf = m * limits + c

    ax0 = fig.add_subplot(1, 2, 1)
    ax1 = fig.add_subplot(1, 2, 2)
    fig.suptitle("Torque, Displacement vs Time at {}Nm Amplitude\nTest ID: {}, Spring ID: {}".
                 format(torque_amplitude, data_id, spring_id))

    ax0.set_title("Measurements vs Time")
    ax0.set_xlabel("Time [s]")
    ax0.set_ylabel("Torque [Nm] / Displacement [deg]")
    ax0.grid()
    ax0.plot(df['time'], df['torque_in'], label="Demanded Torque")
    ax0.plot(df['time'], df['torque_out'], label="Measured Torque")
    ax0.plot(df['time'], df['displacement'], label="Displacement")
    ax0.legend()
    ax1.set_title("Torque vs Displacement")
    ax1.set_xlabel("Displacement [deg]")
    ax1.set_ylabel("Torque [Nm]")
    ax1.grid()
    ax1.plot(df['displacement'], df['torque_out'])
    ax1.plot(limits, torque_bf, linestyle='--', c='r')


def raw_bandwidth_plot_time(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])

    df = pd.read_csv(path + "\\" + filename)
    ax = fig.add_subplot(1, 1, 1)

    fig.suptitle("Torque Control Frequency Response at {}Nm Amplitude".format(amplitude))
    ax.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Torque [Nm]")
    ax.grid()
    ax.plot(df['time'], df['torque_in'], label="Input")
    ax.plot(df['time'], df['torque_out'], label="Output")
    ax.legend()


def raw_bandwidth_plot_frequency(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])
    max_freq = int(filename.split("-")[4])

    df = pd.read_csv(path + "\\" + filename)

    ax0 = fig.add_subplot(2, 1, 1)
    ax1 = fig.add_subplot(2, 1, 2)

    freq, mag, phase, bandwidth = bode(df['time'], df['torque_in'], df['torque_out'])

    bandwidth_idx = find_nearest_idx(freq, bandwidth)

    fig.suptitle("Torque Control Frequency Response at {}Nm Amplitude, up to {}Hz".format(amplitude, max_freq))
    ax0.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax0.set_xlabel("Frequency [Hz]")
    ax0.set_ylabel("Magnitude [dB]")
    ax1.set_xlabel("Frequency [Hz]")
    ax1.set_ylabel("Phase [deg]")
    ax0.set_xscale('log')
    ax1.set_xscale('log')
    ax0.grid()
    ax1.grid()
    ax0.plot(freq, mag, c='r')
    ax1.plot(freq, phase, c='r')
    ax0.set_xlim([0.1, max_freq])
    ax1.set_xlim([0.1, max_freq])
    fig.tight_layout()

    [ymin, ymax] = ax0.get_ylim()
    ax0.plot([bandwidth, bandwidth], [ymin, mag[bandwidth_idx]], c='black', linestyle='--')
    ax0.text(1.1 * bandwidth, 0.8 * ymin, "Bandwidth: {}Hz".format(round(bandwidth, 3)))


def raw_step_response_plot(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])

    df = pd.read_csv(path + "\\" + filename)

    ax = fig.add_subplot(1, 1, 1)

    t_demanded = round(np.array(df['torque_in'])[-1], 2)

    t_rise, overshoot, e_ss = step_characteristics(df['time'], df['torque_in'], df['torque_out'])

    fig.suptitle("Torque Control Step Response at {}Nm ({}A) Amplitude".format(t_demanded, amplitude))
    ax.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Torque [Nm]")
    ax.grid()
    ax.plot(df['time'], df['torque_in'], label="Input")
    ax.plot(df['time'], df['torque_out'], label="Output")
    ax.text(0.015, 0.8, "Rise Time: {}s\nOvershoot: {}%\nSteady State Error: {}%".format(round(t_rise, 4),
                                                                                         round(overshoot, 3),
                                                                                         round(e_ss, 2)),
            transform=ax.transAxes, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='grey',
                                                                   boxstyle='round,pad=0.5', alpha=0.8,
                                                                   linewidth=0.5))
    ax.legend()


def raw_step_response_adjusted_plot(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])

    df = pd.read_csv(path + "\\" + filename)

    ax = fig.add_subplot(1, 1, 1)

    t_demanded = round(np.array(df['torque_in'])[-1], 2)

    t_rise, overshoot, e_ss = step_characteristics(df['time'], df['torque_in'], df['torque_out'])

    fig.suptitle("Torque Control Step Response at {}Nm ({}A) Amplitude".format(t_demanded, amplitude))
    ax.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Torque [Nm]")
    ax.grid()
    ax.plot(df['time'], df['torque_in'], label="Input")
    ax.plot(df['time'], df['torque_out'], label="Output")
    ax.text(0.015, 0.8, "Rise Time: {}s\nOvershoot: {}%\nSteady State Error: {}%".format(round(t_rise, 4),
                                                                                         round(overshoot, 3),
                                                                                         round(e_ss, 2)),
            transform=ax.transAxes, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='grey',
                                                                   boxstyle='round,pad=0.5', alpha=0.8,
                                                                   linewidth=0.5))
    ax.legend()


def raw_sea_bandwidth_plot_time(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])

    df = pd.read_csv(path + "\\" + filename)
    ax = fig.add_subplot(1, 1, 1)

    fig.suptitle("SEA Torque Control Frequency Response at {}Nm Amplitude".format(amplitude))
    ax.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Torque [Nm]")
    ax.grid()
    ax.plot(df['time'], df['torque_in'], label="Input")
    ax.plot(df['time'], df['torque_ati'], label="Output")
    ax.plot(df['time'], df['torque_sea'], label="SEA Torque [unused]", alpha=0.5)
    ax.legend()


def raw_sea_bandwidth_plot_frequency(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])
    max_freq = int(filename.split("-")[4])

    df = pd.read_csv(path + "\\" + filename)

    ax0 = fig.add_subplot(2, 1, 1)
    ax1 = fig.add_subplot(2, 1, 2)

    freq, mag, phase, bandwidth = bode(df['time'], df['torque_in'], df['torque_ati'])

    bandwidth_idx = find_nearest_idx(freq, bandwidth)

    fig.suptitle("SEA Torque Control Frequency Response at {}Nm Amplitude, up to {}Hz".format(amplitude, max_freq))
    ax0.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax0.set_xlabel("Frequency [Hz]")
    ax0.set_ylabel("Magnitude [dB]")
    ax1.set_xlabel("Frequency [Hz]")
    ax1.set_ylabel("Phase [deg]")
    ax0.set_xscale('log')
    ax1.set_xscale('log')
    ax0.grid()
    ax1.grid()
    ax0.plot(freq, mag, c='r')
    ax1.plot(freq, phase, c='r')
    ax0.set_xlim([0.1, max_freq])
    ax1.set_xlim([0.1, max_freq])
    fig.tight_layout()

    [ymin, ymax] = ax0.get_ylim()
    ax0.plot([bandwidth, bandwidth], [ymin, mag[bandwidth_idx]], c='black', linestyle='--')
    ax0.text(1.1 * bandwidth, 0.8 * ymin, "Bandwidth: {}Hz".format(round(bandwidth, 3)))


def raw_sea_step_response_plot(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])

    df = pd.read_csv(path + "\\" + filename)

    ax = fig.add_subplot(1, 1, 1)

    t_demanded = round(np.array(df['torque_in'])[-1], 2)

    t_rise, overshoot, e_ss = step_characteristics(df['time'], df['torque_in'], df['torque_ati'])
    t_rise_sea, overshoot_sea, e_ss_sea = step_characteristics(df['time'], df['torque_in'], df['torque_sea'])

    fig.suptitle("SEA Torque Control Step Response at {}Nm ({}A) Amplitude".format(t_demanded, amplitude))
    ax.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Torque [Nm]")
    ax.grid()
    ax.plot(df['time'], df['torque_sea'], label="SEA Output", c='green', alpha=0.5)
    ax.plot(df['time'], df['torque_in'], label="Input")
    ax.plot(df['time'], df['torque_ati'], label="ATI Output")

    ax.text(0.015, 0.8,
            "ATI Response:\nRise Time: {}s\nOvershoot: {}%\nSteady State Error: {}%".format(round(t_rise, 4),
                                                                                            round(overshoot, 3),
                                                                                            round(e_ss, 2)),
            transform=ax.transAxes, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='grey',
                                                                   boxstyle='round,pad=0.5', alpha=0.8,
                                                                   linewidth=0.5))
    ax.text(0.015, 0.4,
            "SEA Response:\nRise Time: {}s\nOvershoot: {}%\nSteady State Error: {}%".format(round(t_rise_sea, 4),
                                                                                            round(overshoot_sea, 3),
                                                                                            round(e_ss_sea, 2)),
            transform=ax.transAxes, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='grey',
                                                                   boxstyle='round,pad=0.5', alpha=0.8,
                                                                   linewidth=0.5))
    ax.legend()


def raw_kalman_step_response_plot(fig, path, filename):
    data_id = int(filename.split("-")[3])
    covariance = float(filename.split("-")[1])
    noise = float(filename.split("-")[4])

    df = pd.read_csv(path + "\\" + filename)

    ax = fig.add_subplot(1, 1, 1)

    t_rise, overshoot, e_ss = step_characteristics(df['time'], df['torque_in'], df['torque_ati'])
    t_rise_sea, overshoot_sea, e_ss_sea = step_characteristics(df['time'], df['torque_in'], df['torque_sea_filtered'])

    fig.suptitle("Kalman Filtering @ 1Nm, Covariance: {}, Measurement Noise: {}".format(covariance, noise))
    ax.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Torque [Nm]")
    ax.grid()
    ax.plot(df['time'], df['torque_sea'], label="SEA Output", c='green', alpha=0.5)
    ax.plot(df['time'], df['torque_in'], label="Input")
    ax.plot(df['time'], df['torque_ati'], label="ATI Output")
    ax.plot(df['time'], df['torque_sea_filtered'], c='green', label="Filtered Torque", linestyle='--')

    ax.text(0.015, 0.6,
            "ATI Response:\nRise Time: {}s\nOvershoot: {}%\nSteady State Error: {}%".format(round(t_rise, 4),
                                                                                            round(overshoot, 3),
                                                                                            round(e_ss, 2)),
            transform=ax.transAxes, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='grey',
                                                                   boxstyle='round,pad=0.5', alpha=0.8,
                                                                   linewidth=0.5))
    ax.text(0.015, 0.4,
            "SEA Response:\nRise Time: {}s\nOvershoot: {}%\nSteady State Error: {}%".format(round(t_rise_sea, 4),
                                                                                            round(overshoot_sea, 3),
                                                                                            round(e_ss_sea, 2)),
            transform=ax.transAxes, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='grey',
                                                                   boxstyle='round,pad=0.5', alpha=0.8,
                                                                   linewidth=0.5))
    ax.legend()


def raw_sea_step_response_closed_loop_plot(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    gains = filename.split("-")[4]
    data_id = int(filename.split("-")[3])

    df = pd.read_csv(path + "\\" + filename)

    ax = fig.add_subplot(1, 1, 1)

    t_demanded = round(np.array(df['torque_in'])[-1], 2)

    t_rise, overshoot, e_ss = step_characteristics(df['time'], df['torque_in'], df['torque_ati'])
    t_rise_sea, overshoot_sea, e_ss_sea = step_characteristics(df['time'], df['torque_in'], df['torque_sea'])

    fig.suptitle("SEA Closed Loop Torque Step Response at {}Nm ({}A) Amplitude, PID Gains={}".format(t_demanded,
                                                                                                     amplitude,
                                                                                                     gains))
    ax.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Torque [Nm]")
    ax.grid()
    ax.plot(df['time'], df['torque_sea'], label="SEA Output", c='green', alpha=0.5)
    ax.plot(df['time'], df['torque_in'], label="Input")
    ax.plot(df['time'], df['torque_ati'], label="ATI Output")

    ax.text(0.015, 0.8,
            "ATI Response:\nRise Time: {}s\nOvershoot: {}%\nSteady State Error: {}%".format(round(t_rise, 4),
                                                                                            round(overshoot, 3),
                                                                                            round(e_ss, 2)),
            transform=ax.transAxes, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='grey',
                                                                   boxstyle='round,pad=0.5', alpha=0.8,
                                                                   linewidth=0.5))
    ax.text(0.015, 0.4,
            "SEA Response:\nRise Time: {}s\nOvershoot: {}%\nSteady State Error: {}%".format(round(t_rise_sea, 4),
                                                                                            round(overshoot_sea, 3),
                                                                                            round(e_ss_sea, 2)),
            transform=ax.transAxes, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='grey',
                                                                   boxstyle='round,pad=0.5', alpha=0.8,
                                                                   linewidth=0.5))
    ax.legend()


def raw_sea_bandwidth_closed_loop_plot_time(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])
    gains = filename.split("-")[4]

    df = pd.read_csv(path + "\\" + filename)
    ax = fig.add_subplot(1, 1, 1)

    fig.suptitle("SEA Torque Control Frequency Response at {}Nm Amplitude, PID Gains={}".format(amplitude,
                                                                                                gains))
    ax.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Torque [Nm]")
    ax.grid()
    ax.plot(df['time'], df['torque_in'], label="Input")
    ax.plot(df['time'], df['torque_ati'], label="Output")
    ax.plot(df['time'], df['torque_sea'], label="SEA Torque [unused]", alpha=0.5)
    ax.legend()


def raw_sea_bandwidth_closed_loop_plot_frequency(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])
    max_freq = 100  # Now permanently 100, PID tunings now encoded in this space
    gains = filename.split("-")[4]

    df = pd.read_csv(path + "\\" + filename)

    ax0 = fig.add_subplot(2, 1, 1)
    ax1 = fig.add_subplot(2, 1, 2)

    freq, mag, phase, bandwidth = bode(df['time'], df['torque_in'], df['torque_ati'])

    bandwidth_idx = find_nearest_idx(freq, bandwidth)

    fig.suptitle("SEA Closed Loop Torque Frequency Response at {}Nm Amplitude, PID Gains={}".format(amplitude,
                                                                                                    gains))
    ax0.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax0.set_xlabel("Frequency [Hz]")
    ax0.set_ylabel("Magnitude [dB]")
    ax1.set_xlabel("Frequency [Hz]")
    ax1.set_ylabel("Phase [deg]")
    ax0.set_xscale('log')
    ax1.set_xscale('log')
    ax0.grid()
    ax1.grid()
    ax0.plot(freq, mag, c='r')
    ax1.plot(freq, phase, c='r')
    ax0.set_xlim([0.1, max_freq])
    ax1.set_xlim([0.1, max_freq])
    fig.tight_layout()

    [ymin, ymax] = ax0.get_ylim()
    ax0.plot([bandwidth, bandwidth], [ymin, mag[bandwidth_idx]], c='black', linestyle='--')
    ax0.text(1.1 * bandwidth, 0.8 * ymin, "Bandwidth: {}Hz".format(round(bandwidth, 3)))


def raw_ati_bandwidth_closed_loop_plot_time(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])
    gains = filename.split("-")[4]

    df = pd.read_csv(path + "\\" + filename)
    ax = fig.add_subplot(1, 1, 1)

    fig.suptitle("ATI Torque Control Frequency Response at {}Nm Amplitude, PID Gains={}".format(amplitude,
                                                                                                gains))
    ax.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Torque [Nm]")
    ax.grid()
    ax.plot(df['time'], df['torque_in'], label="Input")
    ax.plot(df['time'], df['torque_ati'], label="Output")
    ax.plot(df['time'], df['torque_sea'], label="SEA Torque [unused]", alpha=0.5)
    ax.legend()


def raw_ati_bandwidth_closed_loop_plot_frequency(fig, path, filename):
    amplitude = float(filename.split("-")[1])
    data_id = int(filename.split("-")[3])
    max_freq = 100  # Now permanently 100, PID tunings now encoded in this space
    gains = filename.split("-")[4]

    df = pd.read_csv(path + "\\" + filename)

    ax0 = fig.add_subplot(2, 1, 1)
    ax1 = fig.add_subplot(2, 1, 2)

    freq, mag, phase, bandwidth = bode(df['time'], df['torque_in'], df['torque_ati'])

    bandwidth_idx = find_nearest_idx(freq, bandwidth)

    fig.suptitle("ATI Closed Loop Torque Frequency Response at {}Nm Amplitude, PID Gains={}".format(amplitude,
                                                                                                    gains))
    ax0.set_title("Test ID: {}".format(data_id), fontsize=8)
    ax0.set_xlabel("Frequency [Hz]")
    ax0.set_ylabel("Magnitude [dB]")
    ax1.set_xlabel("Frequency [Hz]")
    ax1.set_ylabel("Phase [deg]")
    ax0.set_xscale('log')
    ax1.set_xscale('log')
    ax0.grid()
    ax1.grid()
    ax0.plot(freq, mag, c='r')
    ax1.plot(freq, phase, c='r')
    ax0.set_xlim([0.1, max_freq])
    ax1.set_xlim([0.1, max_freq])
    fig.tight_layout()

    [ymin, ymax] = ax0.get_ylim()
    ax0.plot([bandwidth, bandwidth], [ymin, mag[bandwidth_idx]], c='black', linestyle='--')
    ax0.text(1.1 * bandwidth, 0.8 * ymin, "Bandwidth: {}Hz".format(round(bandwidth, 3)))


def process_stiffness(path):
    print("Processing Stiffness Results")

    results_dict = {'spring_id': [],
                    'torque_amplitude': [],
                    'stiffness': []}

    for file in os.listdir(path):
        torque_amplitude = file.split("-")[1]
        test_number = file.split("-")[2]
        test_id = file.split("-")[3]
        spring_id = file.split("-")[4]

        df = pd.read_csv(path + "\\" + file)

        m, c, r_value, _, _ = st.linregress(np.array(df['displacement']), np.array(df['torque_out']))

        stiffness = m * 180 / np.pi  # Converting to Nm/rad

        results_dict['spring_id'] += [spring_id]
        results_dict['torque_amplitude'] += [torque_amplitude]
        results_dict['stiffness'] += [stiffness]

        results_df = pd.DataFrame.from_dict(results_dict)
        results_df.to_csv("TestResults" + "\\" + "StiffnessResults" + ".csv")

    print("Successfully written results to StiffnessResults.csv")


def process_system_identification(path):
    time_constant_dict = {'torque': [],
                          'time_constant': []}

    for file in os.listdir(path):
        df = pd.read_csv(path + "/" + file)
        x_t = np.array(df['torque_in'])
        y_t = np.array(df['torque_out'])
        t = np.array(df['time'])

        step_amplitude = round(x_t[-1], 2)

        gain, tau = first_order_system_identification(t, x_t, y_t)

        time_constant_dict['torque'] += [step_amplitude]
        time_constant_dict['time_constant'] += [tau]

    tau_average = np.mean([i for i in time_constant_dict['time_constant'] if i <= 0.07])

    results_path = "TestResults"
    results_file = "TimeConstantResults.csv"
    df_tau = pd.DataFrame.from_dict(time_constant_dict)

    df_tau.to_csv(results_path + "/" + results_file)

    print("Average Time Constant is: {}".format(round(tau_average, 3)))
    print("Successfully Written to ", results_file)


def process_torque_constant(path):
    torque_dictionary = {'in_0': [],
                         'in_1': [],
                         'out_0': [],
                         'out_1': []}

    print("Adjusted Step Response Data")

    for file in os.listdir(path):
        df = pd.read_csv(path + "\\" + file)
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

    torque_constant_dictionary = {'in': input_torque_amplitudes,
                                  'out': output_torque_amplitudes}

    torque_constant_df = pd.DataFrame.from_dict(torque_constant_dictionary)
    torque_constant_df.to_csv("TestResults/" + path.split("\\")[1] + "TorqueConstant.csv")

    a, b, r_value, _, _ = st.linregress(input_torque_amplitudes, output_torque_amplitudes)

    torque_constant = a  # Nm/A
    min_current = -b / a  # A
    min_torque = torque_constant * min_current

    print("Kt: ", round(torque_constant, 4))
    print("Min Torque", min_torque)

    new_directory = path + "Adjusted"

    for i, file in enumerate(os.listdir(path)):
        df = pd.read_csv(path + "\\" + file)
        df['torque_out'] = (np.array(df['torque_out']) - torque_dictionary['out_0'][i])
        df['torque_in'] = np.array(df['torque_in']) * torque_constant

        df.to_csv(new_directory + "/" + file)


def process_bandwidth(path):
    results_filename = path.split("\\")[-1] + ".csv"
    print(results_filename)

    bandwidth_data = {'torque': [],
                      'bandwidth': []}

    for file in os.listdir(path):
        df = pd.read_csv(path + "/" + file)
        try:
            _, _, _, bandwidth = bode(df['time'], df['torque_in'], df['torque_out'])
        except:
            _, _, _, bandwidth = bode(df['time'], df['torque_in'], df['torque_ati'])  # should be ati
        amplitude = round(max(df['torque_in']), 2)
        print(round(bandwidth, 2), "@", amplitude, "Nm")
        bandwidth_data['torque'] += [amplitude]
        bandwidth_data['bandwidth'] += [bandwidth]

    results_path = "TestResults"

    df_bandwidth = pd.DataFrame.from_dict(bandwidth_data)
    df_bandwidth.to_csv(results_path + "/" + results_filename)


def process_step_response(path):
    print("Processing Step Response")
    step_data = {'torque': [],
                 'rise_time': [],
                 'overshoot': [],
                 'error': []}

    for file in os.listdir(path):
        df = pd.read_csv(path + "/" + file)
        rise_time, overshoot, error = step_characteristics(df['time'], df['torque_in'], df['torque_out'])
        amplitude = round(max(df['torque_in']), 2)

        step_data['torque'] += [amplitude]
        step_data['rise_time'] += [rise_time]
        step_data['overshoot'] += [overshoot]
        step_data['error'] += [error]

    results_path = "TestResults"

    df_step = pd.DataFrame.from_dict(step_data)
    df_step.to_csv(results_path + "/" + "StepResponseResults.csv")

    print("Successfully Written to ", results_path + "/" + "StepResponseResults.csv")


def process_bandwidth_statistics(path):
    test_folder = "TestResults"

    paths = ["OriginalMotorBandwidth.csv", "SEAMotorBandwidth.csv", "SEABandwidthClosedLoop.csv",
             "ATIBandwidthClosedLoop.csv"]

    statistics_dict = {"system": ["Motor", "OpenLoopSEA", "ClosedLoopSEA", "ClosedLoopATI"],
                       "mean": [],
                       "min": [],
                       "max": [],
                       "t_max": []}

    for p in paths:
        df = pd.read_csv(test_folder + "/" + p, comment="#")
        statistics_dict["mean"] += [df['bandwidth'].mean()]
        statistics_dict["min"] += [df['bandwidth'].min()]
        statistics_dict["max"] += [df['bandwidth'].max()]
        statistics_dict["t_max"] += [df.loc[df['bandwidth'].idxmax(), 'torque']]

    df_stats = pd.DataFrame.from_dict(statistics_dict)

    print(df_stats)


def processed_stiffness_plot(fig, path):
    df = pd.read_csv(path)
    springs = {"spring1": [],
               "spring2": [],
               "spring3": [],
               "spring4": [],
               "spring5": [],
               "torque1": [],
               "torque2": [],
               "torque3": [],
               "torque4": [],
               "torque5": [],
               "spring_id": ["Waterjet 3mm", "Lasercut 7mm", "Lasercut 3mm", "Lasercut 2mm", "Constrained 7mm"]}

    for index, row in df.iterrows():
        i = int(row['spring_id'])
        springs["spring{}".format(i)] += [row['stiffness']]
        springs["torque{}".format(i)] += [row['torque_amplitude']]

    print("Average Stiffness:")

    ax = fig.add_subplot(1, 1, 1)

    colours = ['blue', 'orange', 'green', 'grey']

    for i in range(1, 5):  # Change to 6 to see constrained 7mm spring

        xg, yg = group(springs['torque{}'.format(i)], springs['spring{}'.format(i)])
        min_ser = [min(j) for j in yg]
        max_ser = [max(j) for j in yg]

        ax.fill_between(xg, min_ser, max_ser, alpha=0.2, color=colours[i-1])

        ax.scatter(springs['torque{}'.format(i)], springs['spring{}'.format(i)], label=springs['spring_id'][i - 1],
                   marker='x', color=colours[i-1])
        k_arr = np.array(springs['spring{}'.format(i)])
        print(springs['spring_id'][i - 1], ": ", np.average(k_arr), " & ",
              k_arr[(k_arr > k_arr[0] * 0.9) & (k_arr < k_arr[0] * 1.1)].mean())
    ax.set_title("Spring Stiffness against Maximum applied Torque")
    ax.set_xlabel("Applied Torque Amplitude [Nm]")
    ax.set_ylabel("Stiffness [Nm/rad]")
    ax.legend()
    ax.grid()


def processed_bandwidth_plot(fig, path):
    df = pd.read_csv(path, index_col=0, comment='#')

    ax = fig.add_subplot(1, 1, 1)

    n = np.array(df['torque'].value_counts())

    b_err = np.array(df.groupby(['torque']).std())[:, 0] / np.sqrt(n)
    b_mean = df.groupby(['torque']).mean()

    print(b_err)

    ax.errorbar(np.unique(df['torque']), np.array(b_mean['bandwidth']), yerr=b_err, capsize=10,
                c='red', markerfacecolor='red', markeredgecolor='red', marker='x', ecolor='black')
    ax.set_ylabel("Bandwidth [Hz]")
    ax.set_title("Bandwidth vs Torque Amplitude")
    ax.grid()
    ax.set_xlim([0, None])
    ax.set_ylim([0, None])
    ax.set_xlabel("Torque Amplitude [Nm]")


def processed_step_response_plot(fig, path):
    df = pd.read_csv(path)

    ax0 = fig.add_subplot(3, 1, 1)
    ax1 = fig.add_subplot(3, 1, 2)
    ax2 = fig.add_subplot(3, 1, 3)

    ax0.scatter(df['torque'], df['rise_time'], marker='x', color='red')
    ax0.set_ylabel("Rise Time [s]")
    ax0.set_title("Rise Time vs Torque Amplitude")
    ax1.scatter(df['torque'], df['overshoot'], marker='x', color='red')
    ax1.set_ylabel("Percentage Overshoot [%]")
    ax1.set_title("Percentage Overshoot vs Torque Amplitude")
    ax2.scatter(df['torque'], df['error'], marker='x', color='red')
    ax2.set_ylabel("Steady State Error [%]")
    ax2.set_title("Steady State Error vs Torque Amplitude")

    ax0.grid()
    ax0.set_xlim([0, None])
    ax0.set_ylim([0, None])
    ax0.set_xlabel("Torque Amplitude [Nm]")
    ax1.grid()
    ax1.set_xlim([0, None])
    ax1.set_ylim([0, None])
    ax1.set_xlabel("Torque Amplitude [Nm]")
    ax2.grid()
    ax2.set_xlim([0, None])
    ax2.set_ylim([0, None])
    ax2.set_xlabel("Torque Amplitude [Nm]")

    plt.tight_layout()


def processed_time_constant_plot(fig, path):
    df = pd.read_csv(path)

    ax = fig.add_subplot(1, 1, 1)

    tau_average = np.mean([i for i in df['time_constant'] if i <= 0.07])

    ax.set_title("Time Constants vs Demanded Torque\nAverage Time Constant: {}".format(np.round(tau_average, 5)))
    ax.set_xlabel("Torque Step [Nm]")
    ax.set_ylabel("Time Constant [-]")
    ax.grid()
    ax.plot([0, max(df['torque'])], [tau_average, tau_average], color='black', linestyle='--')
    ax.scatter(df['torque'], df['time_constant'], marker='x', color='red')
    ax.set_xlim([0, max(df['torque'])])
    ax.set_ylim([0, None])
    '''ax.text(0.015, 0.8, "Average Time Constant: {}".format(round(tau_average, 5)),
            transform=ax.transAx`es, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='grey',
                                                                   boxstyle='round,pad=0.5', alpha=0.8,
                                                                   linewidth=0.5))'''


def aggregate_bandwidth_results(fig, path):

    ax = fig.add_subplot(1, 1, 1)

    df = pd.read_csv(path + "/OriginalMotorBandwidth.csv", comment='#')
    xg, yg = group(df['torque'], df['bandwidth'])
    min_ser = [min(i) for i in yg]
    max_ser = [max(i) for i in yg]

    ax.fill_between(xg, min_ser, max_ser, alpha=0.2, color='blue')
    ax.scatter(df['torque'], df['bandwidth'], marker='x', label="Original Motor", c='blue')

    df = pd.read_csv(path + "/SEAMotorBandwidth.csv", comment='#')
    xg, yg = group(df['torque'], df['bandwidth'])
    min_ser = [min(i) for i in yg]
    max_ser = [max(i) for i in yg]

    ax.fill_between(xg, min_ser, max_ser, alpha=0.2, color='orange')
    ax.scatter(df['torque'], df['bandwidth'], marker='x', label="Passive SEA Module", c='orange')

    df = pd.read_csv(path + "/SEABandwidthClosedLoop.csv", comment='#')
    xg, yg = group(df['torque'], df['bandwidth'])
    min_ser = [min(i) for i in yg]
    max_ser = [max(i) for i in yg]

    ax.fill_between(xg, min_ser, max_ser, alpha=0.2, color='green')
    ax.scatter(df['torque'], df['bandwidth'], marker='x', label="SEA Module with SEA Feedback", c='green')

    df = pd.read_csv(path + "/ATIBandwidthClosedLoop.csv", comment='#')
    xg, yg = group(df['torque'], df['bandwidth'])
    min_ser = [min(i) for i in yg]
    max_ser = [max(i) for i in yg]

    ax.fill_between(xg, min_ser, max_ser, alpha=0.2, color='grey')
    ax.scatter(df['torque'], df['bandwidth'], marker='x', label="SEA Module with ATI Feedback", c='grey')

    ax.set_ylabel("Bandwidth [Hz]")
    ax.set_title("Bandwidth vs Torque Amplitude")
    ax.grid()
    ax.legend()
    ax.set_xlim([0, None])
    ax.set_ylim([0, None])
    ax.set_xlabel("Torque Amplitude [Nm]")


def torque_constant_results(fig, path):
    df = pd.read_csv(path)
    ax = fig.add_subplot(1, 1, 1)

    ax.scatter(df['in'], df['out'], marker='x', c='red')
    ax.plot([0, np.max(df['in'])], [0, np.max(df['out'])], linestyle="--", c='black')

    a, b, r_value, _, _ = st.linregress(df['in'], df['out'])

    torque_constant = a  # Nm/A
    min_current = -b / a  # A
    min_torque = torque_constant * min_current

    ax.set_title("Output Torque vs Input Current\nAverage Torque Constant is {} with R={}".format(np.round(torque_constant, 3), np.round(r_value, 4)))
    ax.set_xlabel("Input Current [A]")
    ax.set_ylabel("Output Torque [Nm]")
    ax.set_ylim([0, None])
    ax.set_xlim([0, None])
    ax.grid()


def main():
    matplotlib.use("TkAgg")
    sg.theme('GrayGrayGray')
    fig = matplotlib.figure.Figure(figsize=(14, 6))

    operation_list = ["Plot Raw Data",
                      "Post Process Data",
                      "Plot Processed Results"]

    # Add additional processor lists if other Raw Datas can have multiple processors operating on them
    processor_list_0 = ["Process Bandwidth",
                        "Process Bandwidth Statistics"]
    processor_list_1 = ["Process Torque Constant"]
    processor_list_2 = ["Process System Identification",
                        "Process Step Response"]
    processor_list_3 = ["Process Stiffness"]

    data_selection_0 = ["OriginalMotorBandwidth",
                        "OriginalMotorStepResponse",
                        "OriginalMotorStepResponseAdjusted",
                        "StiffnessTesting",
                        "SEAMotorBandwidth",
                        "SEAStepResponse",
                        "KalmanFiltering",
                        "SEAStepResponseClosedLoop",
                        "SEABandwidthClosedLoop",
                        "ATIBandwidthClosedLoop"]

    data_selection_1 = ["OriginalMotorBandwidth",
                        "SEAMotorBandwidth",
                        "SEABandwidthClosedLoop",
                        "StepResponseResults",
                        "StiffnessResults",
                        "TimeConstantResults",
                        "AggregateBandwidthResults",
                        "OriginalMotorStepResponseTorqueConstant"]

    domain_list = ["TimeDomain",
                   "FrequencyDomain"]

    valid_data_ids = np.linspace(1, 200, 200, dtype='int')

    data_selection = data_selection_0  # Will change based on operation_list selection

    raw_plots = {"raw_stiffness_plot": raw_stiffness_plot,
                 "raw_bandwidth_plot_time": raw_bandwidth_plot_time,
                 "raw_bandwidth_plot_frequency": raw_bandwidth_plot_frequency,
                 "raw_step_response_plot": raw_step_response_plot,
                 "raw_step_response_adjusted_plot": raw_step_response_adjusted_plot,
                 "raw_sea_bandwidth_plot_time": raw_sea_bandwidth_plot_time,
                 "raw_sea_bandwidth_plot_frequency": raw_sea_bandwidth_plot_frequency,
                 "raw_sea_step_response_plot": raw_sea_step_response_plot,
                 "raw_kalman_step_response_plot": raw_kalman_step_response_plot,
                 "raw_sea_step_response_closed_loop_plot": raw_sea_step_response_closed_loop_plot,
                 "raw_sea_bandwidth_closed_loop_plot_time": raw_sea_bandwidth_closed_loop_plot_time,
                 "raw_sea_bandwidth_closed_loop_plot_frequency": raw_sea_bandwidth_closed_loop_plot_frequency,
                 "raw_ati_bandwidth_closed_loop_plot_frequency": raw_ati_bandwidth_closed_loop_plot_frequency,
                 "raw_ati_bandwidth_closed_loop_plot_time": raw_ati_bandwidth_closed_loop_plot_time}

    post_processors = {"process_bandwidth_results": process_bandwidth,
                       "process_torque_constant": process_torque_constant,
                       "process_system_identification": process_system_identification,
                       "process_step_response": process_step_response,
                       "process_stiffness": process_stiffness,
                       "process_bandwidth_statistics": process_bandwidth_statistics}

    processed_plots = {"processed_stiffness_plot": processed_stiffness_plot,
                       "processed_bandwidth_plot": processed_bandwidth_plot,
                       "processed_step_response": processed_step_response_plot,
                       "processed_time_constant": processed_time_constant_plot,
                       "aggregate_bandwidth_results": aggregate_bandwidth_results,
                       "torque_constant_results": torque_constant_results}

    left_col = [[sg.Combo(operation_list, size=(30, 5), default_value=operation_list[0], key="OP_LIST")],
                [sg.Combo(data_selection, size=(30, 5), default_value=data_selection[0], key="DATA_LIST")],
                [sg.Combo(processor_list_0, size=(30, 5), default_value=processor_list_0[0], key="PRO_LIST",
                          visible=False)],
                [sg.Text("Data ID"),
                 sg.Spin(valid_data_ids, initial_value=valid_data_ids[0], key="DATA_ID", size=(5, 5),
                         enable_events=True, readonly=False),
                 sg.Combo(domain_list, size=(15, 5), default_value=domain_list[0], key="DOMAIN", visible=False)],
                [sg.Button("Process"), sg.Button("Plot"), sg.Button("Clear Output")],
                # [sg.Output(size=(30, 20), key="OUTPUT")]
                ]

    right_col = [[sg.Canvas(size=(600 * 2, 500), key='FIG_CV')],
                 [sg.Push(), sg.Canvas(key='CONTROLS_CV'), sg.Push()]
                 ]

    layout = [[sg.Column(left_col, element_justification='c'),
               sg.Column(right_col, element_justification='r')]]

    window = sg.Window("Results GUI", layout, finalize=True)

    while True:
        try:
            event, values = window.read(timeout=20)  # Constantly reads for events such as button presses

            # RAW DATA PLOTTING
            if values["OP_LIST"] == "Plot Raw Data":
                data_selection = data_selection_0
                window.find_element('DATA_LIST').update(values=data_selection, value=values['DATA_LIST'])
                window.find_element('PRO_LIST').update(visible=False)
                path = "TestData" + "\\" + values["DATA_LIST"]

                if values["DATA_LIST"] == "OriginalMotorBandwidth" or values["DATA_LIST"] == "SEAMotorBandwidth" or \
                        values["DATA_LIST"] == "SEABandwidthClosedLoop" \
                        or values["DATA_LIST"] == "ATIBandwidthClosedLoop":
                    window.find_element('DOMAIN').update(visible=True)
                else:
                    window.find_element('DOMAIN').update(visible=False)

                if event == 'Plot' or event == "DATA_ID":
                    for file in os.listdir(path):
                        if int(file.split("-")[3]) == values['DATA_ID']:
                            filename = file
                    fig.clear()
                    fig.set_size_inches(14, 6, forward=True)

                    if values["DATA_LIST"] == "StiffnessTesting":
                        raw_plots["raw_stiffness_plot"](fig, path, filename)

                    if values["DATA_LIST"] == "OriginalMotorBandwidth":
                        if values["DOMAIN"] == "TimeDomain":
                            raw_plots["raw_bandwidth_plot_time"](fig, path, filename)
                        elif values["DOMAIN"] == "FrequencyDomain":
                            raw_plots["raw_bandwidth_plot_frequency"](fig, path, filename)

                    if values["DATA_LIST"] == "SEAMotorBandwidth":
                        if values["DOMAIN"] == "TimeDomain":
                            raw_plots["raw_sea_bandwidth_plot_time"](fig, path, filename)
                        elif values["DOMAIN"] == "FrequencyDomain":
                            raw_plots["raw_sea_bandwidth_plot_frequency"](fig, path, filename)

                    if values["DATA_LIST"] == "SEABandwidthClosedLoop":
                        if values["DOMAIN"] == "TimeDomain":
                            raw_plots["raw_sea_bandwidth_closed_loop_plot_time"](fig, path, filename)
                        elif values["DOMAIN"] == "FrequencyDomain":
                            raw_plots["raw_sea_bandwidth_closed_loop_plot_frequency"](fig, path, filename)

                    if values["DATA_LIST"] == "ATIBandwidthClosedLoop":
                        if values["DOMAIN"] == "TimeDomain":
                            raw_plots["raw_ati_bandwidth_closed_loop_plot_time"](fig, path, filename)
                        elif values["DOMAIN"] == "FrequencyDomain":
                            raw_plots["raw_ati_bandwidth_closed_loop_plot_frequency"](fig, path, filename)

                    if values["DATA_LIST"] == "OriginalMotorStepResponse":
                        raw_plots["raw_step_response_plot"](fig, path, filename)
                    if values["DATA_LIST"] == "OriginalMotorStepResponseAdjusted":
                        raw_plots["raw_step_response_adjusted_plot"](fig, path, filename)
                    if values["DATA_LIST"] == "SEAStepResponse":
                        raw_plots["raw_sea_step_response_plot"](fig, path, filename)
                    if values["DATA_LIST"] == "KalmanFiltering":
                        raw_plots["raw_kalman_step_response_plot"](fig, path, filename)
                    if values["DATA_LIST"] == "SEAStepResponseClosedLoop":
                        raw_plots["raw_sea_step_response_closed_loop_plot"](fig, path, filename)

                    draw_figure_w_toolbar(window['FIG_CV'].TKCanvas, fig, window['CONTROLS_CV'].TKCanvas)
                    fig.canvas.draw()

            # RAW DATA POST PROCESSING
            elif values["OP_LIST"] == "Post Process Data":
                data_selection = data_selection_0
                window.find_element('DATA_LIST').update(values=data_selection, value=values['DATA_LIST'])
                path = "TestData" + "\\" + values["DATA_LIST"]

                window.find_element('PRO_LIST').update(values=processor_list_0, visible=True,
                                                       value=values["PRO_LIST"])

                if values["DATA_LIST"] == "OriginalMotorBandwidth" \
                        or values["DATA_LIST"] == "SEAMotorBandwidth" \
                        or values["DATA_LIST"] == "SEABandwidthClosedLoop" \
                        or values["DATA_LIST"] == "ATIBandwidthClosedLoop":
                    window.find_element('PRO_LIST').update(values=processor_list_0, visible=True,
                                                           value=values["PRO_LIST"])
                elif values["DATA_LIST"] == "OriginalMotorStepResponse":
                    window.find_element('PRO_LIST').update(values=processor_list_1, visible=True,
                                                           value=values["PRO_LIST"])
                elif values["DATA_LIST"] == "OriginalMotorStepResponseAdjusted":
                    window.find_element('PRO_LIST').update(values=processor_list_2, visible=True,
                                                           value=values["PRO_LIST"])
                elif values["DATA_LIST"] == "StiffnessTesting":
                    window.find_element('PRO_LIST').update(values=processor_list_3, visible=True,
                                                           value=values["PRO_LIST"])

                if event == 'Process':
                    if values["PRO_LIST"] == "Process Bandwidth":
                        post_processors["process_bandwidth_results"](path)
                    elif values["PRO_LIST"] == "Process Torque Constant":
                        post_processors["process_torque_constant"](path)
                    elif values["PRO_LIST"] == "Process System Identification":
                        post_processors["process_system_identification"](path)
                    elif values["PRO_LIST"] == "Process Step Response":
                        post_processors["process_step_response"](path)
                    elif values["PRO_LIST"] == "Process Stiffness":
                        post_processors["process_stiffness"](path)
                    elif values["PRO_LIST"] == "Process Bandwidth Statistics":
                        post_processors["process_bandwidth_statistics"](path)

            # PROCESSED DATA PLOTTING
            elif values["OP_LIST"] == "Plot Processed Results":
                data_selection = data_selection_1
                window.find_element('DATA_LIST').update(values=data_selection, value=values['DATA_LIST'])
                window.find_element('PRO_LIST').update(visible=False)
                path = "TestResults" + "\\" + values["DATA_LIST"] + ".csv"

                if event == 'Plot':
                    fig.clear()
                    fig.set_size_inches(14, 6)

                    if values["DATA_LIST"] == "StiffnessResults":
                        processed_plots["processed_stiffness_plot"](fig, path)
                    elif values["DATA_LIST"] == "OriginalMotorBandwidth":
                        processed_plots["processed_bandwidth_plot"](fig, path)
                    elif values["DATA_LIST"] == "SEAMotorBandwidth":
                        processed_plots["processed_bandwidth_plot"](fig, path)
                    elif values["DATA_LIST"] == "SEABandwidthClosedLoop":
                        processed_plots["processed_bandwidth_plot"](fig, path)
                    elif values["DATA_LIST"] == "ATIBandwidthClosedLoop":
                        processed_plots["processed_bandwidth_plot"](fig, path)
                    elif values["DATA_LIST"] == "StepResponseResults":
                        processed_plots["processed_step_response"](fig, path)
                    elif values["DATA_LIST"] == "TimeConstantResults":
                        processed_plots["processed_time_constant"](fig, path)
                    elif values["DATA_LIST"] == "AggregateBandwidthResults":
                        processed_plots["aggregate_bandwidth_results"](fig, "TestResults")
                    elif values["DATA_LIST"] == "OriginalMotorStepResponseTorqueConstant":
                        processed_plots["torque_constant_results"](fig, path)

                    draw_figure_w_toolbar(window['FIG_CV'].TKCanvas, fig, window['CONTROLS_CV'].TKCanvas)
                    fig.canvas.draw()

            if event == sg.WIN_CLOSED or event == "Exit":
                break
            elif event == 'Clear Output':
                window['OUTPUT'].update('')

        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            window.close()


if __name__ == "__main__":
    main()
