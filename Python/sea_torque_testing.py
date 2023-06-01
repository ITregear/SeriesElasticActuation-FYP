# Author: ivantregear
# Date Created: 02/03/2023
# Description: 

# When I wrote this code only God I and knew how it worked.
# Now only god knows it.

import winsound
import numpy as np

from series_elastic_actuator import SeriesElasticActuator
from NetFT import Sensor
from file_logging import save_file
from original_motor_torque_testing import sine_sweep_lin


def main():
    # Hardware initialization
    sea = SeriesElasticActuator("COM5", "COM9")
    sea.init_hardware()
    sea.stiffness = 2425  # Nm/rad

    ati_gamma = Sensor("192.168.1.1")
    ati_gamma.tare(100)
    cpf = 1000000  # Counts per Force (from ATI Gamma calibration file)

    test_type = "bw_sea_cl"  # bw = Bandwidth, sr = Step Response
    torque_amplitude = 0.1  # Nm
    f0 = 0  # Sine sweep initial frequency
    f1 = 40  # Sine sweep final frequency
    demanded_torque = 0  # Torque input
    actual_torque = 0  # ATI Gamma torque
    period = 0  # In case incorrectly defined

    if test_type == "bw_sea_cl" or test_type == "bw_sea" or "bw_ati_cl":
        period = 40  # Sine sweep test length
    elif test_type == "sr_sea_cl":
        period = 6

    # Setup Kalman Filter
    sea.covariance = 100
    sea.measurement_noise = 0.1
    sea.init_filter()

    # Setup PID Controller
    sea.feedback = True  # False if not closed loop test
    sea.init_pid(1, 0, 0)

    data_log = {
        "time": [],
        "torque_in": [],
        "torque_ati": [],
        "torque_sea": []
    }
    while True:
        try:
            sea.update()
            sea.get_torque()
            time = sea.time

            actual_torque = -ati_gamma.getMeasurement()[5] / cpf

            if test_type == "bw_sea_cl" or test_type == "bw_sea" or test_type == "bw_ati_cl":
                demanded_torque = torque_amplitude * sine_sweep_lin(time, period, f0, f1)
                sea.ati_torque = actual_torque
                sea.controller(demanded_torque)

            if test_type == "sr_sea_cl":
                if time > 3:
                    demanded_torque = torque_amplitude
                else:
                    demanded_torque = 0
                sea.controller(demanded_torque)

            data_log["torque_in"] += [demanded_torque]
            data_log["torque_ati"] += [actual_torque]
            data_log["torque_sea"] += [sea.filtered_torque]
            data_log["time"] += [time]

            print(round(time, 1))

            if time > period:
                raise KeyboardInterrupt

        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            winsound.Beep(440, 500)
            sea.rmd.disable_motor()

            time_arr = np.array(data_log['time'])
            freq = np.zeros(len(time_arr) - 1)
            for i in range(0, len(time_arr) - 1):
                freq[i] = 1 / (time_arr[i + 1] - time_arr[i])

            print("Average Sampling Frequency: {}Hz".format(round(np.average(freq), 3)))

            # File Creation
            sea.rmd.disable_motor()

            test_path = "D:\\OneDrive - Imperial College London\\Imperial\\ME4\\Final Year " \
                        "Project\\Code\\Python\\TestData"

            pid_gains = sea.pid.tunings

            save_file(test_type, torque_amplitude, pid_gains, data_log, test_path)  # f1 if open loop, pid_gains if closed

            break


if __name__ == "__main__":
    main()
