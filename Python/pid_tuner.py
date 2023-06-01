# Author: ivantregear
# Date Created: 05/03/2023
# Description: 

# When I wrote this code only God I and knew how it worked.
# Now only god knows it.

import numpy as np
import matplotlib.pyplot as plt
import keyboard

from series_elastic_actuator import SeriesElasticActuator
from NetFT import Sensor


def main():
    # Hardware initialization
    sea = SeriesElasticActuator("COM5", "COM9")
    sea.init_hardware()

    ati_gamma = Sensor("192.168.1.1")
    ati_gamma.tare(100)
    cpf = 1000000  # Counts per Force (from ATI Gamma calibration file)

    torque_amplitude = 1  # Nm
    demanded_torque = 0  # Torque input
    direction = False

    # Setup Kalman Filter
    sea.covariance = 100
    sea.measurement_noise = 0.1
    sea.init_filter()

    # Setup PID Controller
    sea.feedback = True
    kp = 0.1
    ki = 0
    kd = 0
    sea.init_pid(kp, ki, kd)

    data_log = {
        "time": [],
        "torque_in": [],
        "torque_ati": [],
        "torque_sea": []
    }

    # Plotting initialization
    fig, ax = plt.subplots()
    torque_in, = ax.plot([0, 1], [0, 1], label="Demanded Torque")
    torque_ati, = ax.plot([0, 1], [0, 1], label="ATI Torque")
    torque_sea, = ax.plot([0, 1], [0, 1], label="SEA Torque")
    ax.legend()
    ax.set_title("Torque Step Response for PID Tuning")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Torque [Nm]")

    plt.ion()

    max_x = 30
    max_x_flag = False
    plot_flag = True

    while True:
        try:
            sea.update()
            sea.get_torque()
            time = sea.time

            actual_torque = -ati_gamma.getMeasurement()[5] / cpf

            data_log["torque_in"] += [demanded_torque]
            data_log["torque_ati"] += [actual_torque]
            data_log["torque_sea"] += [sea.filtered_torque]
            data_log["time"] += [time]

            if keyboard.is_pressed('space'):
                direction = not direction
                demanded_torque = direction * torque_amplitude

            if keyboard.is_pressed('q'):
                kp += 0.001
            if keyboard.is_pressed('w'):
                ki += 0.001
            if keyboard.is_pressed('e'):
                kd += 0.001
            if keyboard.is_pressed('a'):
                kp -= 0.001
            if keyboard.is_pressed('s'):
                ki -= 0.001
            if keyboard.is_pressed('d'):
                kd -= 0.001

            sea.pid.tunings = (kp, ki, kd)
            sea.controller(demanded_torque)

            print("Kp:", sea.pid.tunings[0], "\t", "Ki:", sea.pid.tunings[1], "\t", "Kd:", sea.pid.tunings[2])

            if time >= max_x:
                if not max_x_flag:
                    i2 = len(data_log["time"])
                    i_len = i2
                    max_x_flag = True
                i2 = len(data_log["time"])
                i1 = i2 - i_len

                ax.set_xlim(data_log["time"][-1] - max_x, data_log["time"][-1])
                ax.set_ylim(np.min(np.column_stack([data_log["torque_in"][i1:i2], data_log["torque_ati"][i1:i2],
                                                    data_log["torque_sea"][i1:i2]])),
                            np.max(np.column_stack([data_log["torque_in"][i1:i2], data_log["torque_ati"][i1:i2],
                                                    data_log["torque_sea"][i1:i2]])))
            else:
                ax.set_xlim(0, data_log["time"][-1])
                ax.set_ylim(np.min(np.column_stack([data_log["torque_in"], data_log["torque_ati"],
                                                    data_log["torque_sea"]])),
                            np.max(np.column_stack([data_log["torque_in"], data_log["torque_ati"],
                                                    data_log["torque_sea"]])))
            if plot_flag:
                torque_in.set_data(data_log["time"], data_log["torque_in"])
                torque_ati.set_data(data_log["time"], data_log["torque_ati"])
                torque_sea.set_data(data_log["time"], data_log["torque_sea"])
                plt.pause(0.0001)

        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            sea.rmd.disable_motor()


if __name__ == "__main__":
    main()
