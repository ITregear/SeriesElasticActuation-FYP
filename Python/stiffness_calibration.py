# Author: ivantregear
# Date Created: 26/02/2023
# Description: 

# When I wrote this code only God I and knew how it worked.
# Now only god knows it.


import winsound

from series_elastic_actuator import SeriesElasticActuator
from NetFT import Sensor
from file_logging import save_file


def torque_profile(t, T):

    if 5 <= t < 10:
        torque = T * (t - 5) / 5
    elif 10 <= t < 15:
        torque = T
    elif 15 <= t < 25:
        torque = T * (20 - t) / 5
    elif 25 <= t < 30:
        torque = -T
    elif 30 <= t < 35:
        torque = - T * (35 - t) / 5
    else:
        torque = 0

    return torque


def main():
    # Hardware initialization
    sea = SeriesElasticActuator("COM5", "COM9")
    sea.init_hardware()

    ati_gamma = Sensor("192.168.1.1")
    ati_gamma.tare(100)

    # Variable Declaration
    cpf = 1000000  # Counts per Force (from ATI Gamma calibration file)

    test_type = "kt"  # kt = K_theta
    torque_amplitude = 9  # Amps
    spring_id = 5  # Spring identifier

    period = 35  # Seconds

    data_log = {
        "time": [],
        "torque_in": [],
        "torque_out": [],
        "displacement": []
    }

    while True:
        try:

            sea.update()
            sea.get_torque()
            time = sea.time

            if time > 5:
                demanded_torque = torque_profile(time, torque_amplitude)
            else:
                demanded_torque = 0

            sea.rmd.set_torque(demanded_torque)

            actual_torque = -ati_gamma.getMeasurement()[5] / cpf

            displacement = -sea.displacement_deg

            print(round(actual_torque, 3), round(displacement, 3))
            data_log["torque_in"] += [demanded_torque]
            data_log["torque_out"] += [actual_torque]
            data_log["displacement"] += [displacement]
            data_log["time"] += [time]

            if time > period:
                raise KeyboardInterrupt

        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            # File Creation
            sea.rmd.disable_motor()
            winsound.Beep(440, 500)
            test_path = "D:\\OneDrive - Imperial College London\\Imperial\\ME4\\Final Year " \
                        "Project\\Code\\Python\\TestData"

            save_file(test_type, torque_amplitude, spring_id, data_log, test_path)
            print("File Saved")
            break


if __name__ == "__main__":
    main()
