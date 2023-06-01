# Author: ivantregear
# Date Created: 03/03/2023
# Description: 

# When I wrote this code only God I and knew how it worked.
# Now only god knows it.


import winsound
import numpy as np

from series_elastic_actuator import SeriesElasticActuator
from NetFT import Sensor
from file_logging import save_file


def main():
    # Hardware initialization
    sea = SeriesElasticActuator("COM5", "COM9")
    sea.init_hardware()

    ati_gamma = Sensor("192.168.1.1")
    ati_gamma.tare(100)
    cpf = 1000000  # Counts per Force (from ATI Gamma calibration file)

    test_type = "sr_kal"  # bw = Bandwidth, sr = Step Response
    torque_amplitude = 1  # Nm
    period = 6  # In case incorrectly defined

    # Setup Kalman Filter
    sea.covariance = 100
    sea.measurement_noise = 0.1
    sea.init_filter()

    # Setup PID Controller
    sea.feedback = True
    kp = 1
    ki = 0
    kd = 0
    sea.init_pid(kp, ki, kd)

    data_log = {
        "time": [],
        "torque_in": [],
        "torque_ati": [],
        "torque_sea": [],
        "torque_sea_filtered": []
    }
    while True:
        try:
            sea.update()
            sea.get_torque()
            time = sea.time

            print(round(time, 1))

            if time > 3:
                demanded_torque = torque_amplitude
            else:
                demanded_torque = 0
            sea.controller(demanded_torque)

            actual_torque = -ati_gamma.getMeasurement()[5] / cpf

            data_log["torque_in"] += [demanded_torque]
            data_log["torque_ati"] += [actual_torque]
            data_log["torque_sea"] += [sea.enc_torque]
            data_log["torque_sea_filtered"] += [sea.filtered_torque]
            data_log["time"] += [time]

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

            save_file(test_type, sea.covariance, sea.measurement_noise, data_log, test_path)

            break


if __name__ == "__main__":
    main()
