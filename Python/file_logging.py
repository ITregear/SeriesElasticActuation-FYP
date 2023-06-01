# Author: ivantregear
# Date Created: 07/12/2022
# Description: 

# When I wrote this code only got I and knew how it worked.
# Now only god knows it.


import pandas as pd
import os
from datetime import datetime
import numpy as np


def save_file(test_type, amplitude, max_freq, data_log, test_path):

    now = datetime.now()
    dt_string = now.strftime("%d%m%Y-%H%M%S")

    if test_type == "bw":
        test_path += "\\OriginalMotorBandwidth"

    if test_type == "sr":
        test_path += "\\OriginalMotorStepResponse"
        max_freq = "00"

    if test_type == "kt":
        test_path += "\\StiffnessTesting"

    if test_type == "bw_sea":
        test_path += "\\SEAMotorBandwidth"

    if test_type == "sr_sea":
        test_path += "\\SEAStepResponse"

    if test_type == "sr_kal":
        test_path += "\\KalmanFiltering"

    if test_type == "sr_sea_cl":
        test_path += "\\SEAStepResponseClosedLoop"

    if test_type == "bw_sea_cl":
        test_path += "\\SEABandwidthClosedLoop"

    if test_type == "bw_ati_cl":
        test_path += "\\ATIBandwidthClosedLoop"

    if not os.path.exists(test_path):
        os.makedirs(test_path)

    arr = os.listdir(test_path)
    test_ids = []
    test_numbers = []
    for file in arr:
        test_id = file.split("-")[3]
        torque = file.split("-")[1]
        test_number = file.split("-")[2]
        test_ids += [test_id]
        if float(torque) == amplitude:
            test_numbers += [test_number]

    if len(test_numbers) == 0:
        test_number_new = 1
    else:
        test_number_new = int(max(test_numbers)) + 1

    if len(test_ids) == 0:
        test_id_new = 1
    else:
        test_id_new = max(list(map(int, test_ids))) + 1

    filename = "{}-{}-{}-{}-{}-{}".format(
        *[test_type, amplitude, test_number_new, test_id_new, max_freq, dt_string])

    df = pd.DataFrame.from_dict(data_log)

    df.to_csv(test_path + "/" + filename)


def main():
    test_type = "kt"
    torque_amplitude = 0.3
    spring_id = 1
    data_log = {"torque_in": [1, 2, 3],
                "torque_out": [4, 5, 6]
                }
    test_path = "D:\\OneDrive - Imperial College London\\Imperial\\ME4\\Final Year Project\\Code\\Python\\TestData"

    save_file(test_type, torque_amplitude, spring_id, data_log, test_path)


if __name__ == "__main__":
    main()
