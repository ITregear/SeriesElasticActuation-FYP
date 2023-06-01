# Author: ivantregear
# Date Created: 06/12/2022
# Description:
# When I wrote this code only got I and knew how it worked.
# Now only god knows it.


import numpy as np
import time as t
import keyboard
import os

from can_transceiver import Motor
from file_logging import save_file
from NetFT import Sensor


def sine_sweep_exp(t, T, f1, f2):
    return np.sin(2 * np.pi * f1 * T / np.log(f2 / f1) * (np.exp(t / T * np.log(f2 / f1)) - 1))


def sine_sweep_lin(t, T, f1, f2):
    return np.sin(2 * np.pi * (f1 * t + (f2 - f1) / (2 * T) * t**2))


def get_directory_attributes(directory_path):
    return next(os.walk(directory_path))


def count_items(directory_path, type):
    path, dirs, files = next(os.walk(directory_path))

    if type == "dir":
        return len(dirs)
    elif type == "files":
        return len(files)


def main():
    # RMD X8 V2 Setup
    arduino_port = "COM3"  # Default COM port
    baud_rate = 115200  # Default Baud Rate
    rmd = Motor()
    rmd.serial_begin(baudrate=baud_rate, port=arduino_port)
    # ATI Gamma Setup
    ati_gamma = Sensor("192.168.1.1")
    ati_gamma.tare(100)

    t.sleep(1)  # Wait for hardware to initialise

    # Variable Declaration
    enable_flag = False  # True if motor is enabled
    cpf = 1000000  # Counts per Force (from ATI Gamma calibration file)

    test_type = "sr"  # bw = Bandwidth, sr = Step Response
    torque_amplitude = 1  # Amps
    t0 = 0  # Initial time
    f0 = 0  # Sine sweep initial frequency
    f1 = 100  # Sine sweep final frequency

    if test_type == "bw":
        period = 100  # Sine sweep test length
    elif test_type == "sr":
        period = 6

    data_log = {
        "time": [],
        "torque_in": [],
        "torque_out": []
    }

    while True:
        try:

            if not enable_flag:
                rmd.enable_motor()
                rmd.set_zero()
                t.sleep(6)
                enable_flag = True
                t0 = t.perf_counter()

            if enable_flag:
                t1 = t.perf_counter()
                time = t1 - t0

                if test_type == "bw":
                    demanded_torque = torque_amplitude * sine_sweep_lin(time, period, f0, f1)
                    rmd.set_torque(demanded_torque)

                if test_type == "sr":
                    if time > 3:
                        demanded_torque = torque_amplitude
                    else:
                        demanded_torque = 0
                    rmd.set_torque(demanded_torque)

                actual_torque = -ati_gamma.getMeasurement()[5] / cpf

                data_log["torque_in"] += [demanded_torque]
                data_log["torque_out"] += [actual_torque]
                data_log["time"] += [time]

                print(demanded_torque)

                if time > period:
                    raise KeyboardInterrupt

        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            # File Creation
            rmd.disable_motor()

            time_arr = np.array(data_log['time'])
            freq = np.zeros(len(time_arr)-1)
            for i in range(0, len(time_arr)-1):
                freq[i] = 1 / (time_arr[i+1] - time_arr[i])

            print("Average Sampling Frequency: {}Hz".format(round(np.average(freq), 3)))

            test_path = "D:\\OneDrive - Imperial College London\\Imperial\\ME4\\Final Year " \
                        "Project\\Code\\Python\\TestData"

            # save_file(test_type, torque_amplitude, f1, data_log, test_path)

            break


if __name__ == "__main__":
    main()
