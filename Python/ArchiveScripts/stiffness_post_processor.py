# Author: ivantregear
# Date Created: 26/02/2023
# Description: 

# When I wrote this code only God I and knew how it worked.
# Now only god knows it.

import matplotlib.pyplot as plt
import pandas as pd
import os
import scipy.stats as st
import numpy as np


def main():

    plot_single = False
    post_process = False
    plot_result = True

    test_path = "../TestData/StiffnessTesting"
    results_path = "../TestResults"
    results_filename = "StiffnessResults"

    if plot_single:
        data_id = 44

        for file in os.listdir(test_path):
            if int(file.split("-")[3]) == data_id:
                filename = file

        torque_amplitude = float(filename.split("-")[1])
        spring_id = int(filename.split("-")[4])

        df = pd.read_csv(test_path + "\\" + filename)

        m, c, r_value, _, _ = st.linregress(np.array(df['displacement']), np.array(df['torque_out']))

        limits = np.array([np.min(df['displacement']), np.max(df['displacement'])])
        torque_bf = m * limits + c

        print(m)

        fig1, ax = plt.subplots(figsize=(17, 6), ncols=2)
        fig1.suptitle("Torque, Displacement vs Time at {}Nm Amplitude".format(torque_amplitude))
        plt.title("Test ID: {}".format(data_id), fontsize=8)
        ax[0].set_title("Measurements vs Time")
        ax[0].set_xlabel("Time [s]")
        ax[0].set_ylabel("Torque [Nm] / Displacement [deg]")
        ax[0].grid()
        ax[0].plot(df['time'], df['torque_in'], label="Demanded Torque")
        ax[0].plot(df['time'], df['torque_out'], label="Measured Torque")
        ax[0].plot(df['time'], df['displacement'], label="Displacement")
        ax[0].legend()
        ax[1].set_title("Torque vs Displacement")
        ax[1].set_xlabel("Displacement [deg]")
        ax[1].set_ylabel("Torque [Nm]")
        ax[1].grid()
        ax[1].plot(df['displacement'], df['torque_out'])
        ax[1].plot(limits, torque_bf, linestyle='--', c='r')
        fig1.show()
        plt.show()

    if post_process:

        results_dict = {'spring_id': [],
                        'torque_amplitude': [],
                        'stiffness': []}

        for file in os.listdir(test_path):
            torque_amplitude = file.split("-")[1]
            test_number = file.split("-")[2]
            test_id = file.split("-")[3]
            spring_id = file.split("-")[4]

            df = pd.read_csv(test_path + "\\" + file)

            m, c, r_value, _, _ = st.linregress(np.array(df['displacement']), np.array(df['torque_out']))

            stiffness = m * 180 / np.pi  # Converting to Nm/rad

            results_dict['spring_id'] += [spring_id]
            results_dict['torque_amplitude'] += [torque_amplitude]
            results_dict['stiffness'] += [stiffness]

        results_df = pd.DataFrame.from_dict(results_dict)
        results_df.to_csv(results_path + "\\" + results_filename + ".csv")

    if plot_result:

        # Spring 1 = Water jet cut 3mm
        # Spring 2 = Laser cut 7mm
        # Spring 3 = Laser cut 3mm
        # Spring 4 = Laser cut 2mm

        df = pd.read_csv(results_path + "\\" + results_filename)
        springs = {"spring1": [],
                   "spring2": [],
                   "spring3": [],
                   "spring4": [],
                   "torque1": [],
                   "torque2": [],
                   "torque3": [],
                   "torque4": [],
                   "spring_id": ["Waterjet 3mm", "Lasercut 7mm", "Lasercut 3mm", "Lasercut 2mm"]}

        for index, row in df.iterrows():
            i = int(row['spring_id'])
            springs["spring{}".format(i)] += [row['stiffness']]
            springs["torque{}".format(i)] += [row['torque_amplitude']]

        print("Average Stiffness:")

        for i in range(1, 5):
            plt.scatter(springs['torque{}'.format(i)], springs['spring{}'.format(i)], label=springs['spring_id'][i-1],
                        marker='x')
            k_arr = np.array(springs['spring{}'.format(i)])
            print(springs['spring_id'][i-1], ": ", np.average(k_arr), " & ",
                  k_arr[(k_arr > k_arr[0]*0.9) & (k_arr < k_arr[0]*1.1)].mean())
        plt.title("Spring Stiffness against Maximum applied Torque")
        plt.xlabel("Applied Torque Amplitude [Nm]")
        plt.ylabel("Stiffness [Nm/rad]")
        plt.legend()
        plt.grid()
        plt.show()


if __name__ == "__main__":
    main()
