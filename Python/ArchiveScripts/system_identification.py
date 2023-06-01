import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import control.matlab as control


def second_order_system_identification(time, xt, yt):

    n = len(time)

    y_ss = np.mean(yt[int(4/6*n) : int(5/6*n)])
    x_ss = xt[-1]

    k = y_ss / x_ss  # Steady state gain (A_0)

    y_ss_25 = 0.25 * y_ss
    y_ss_75 = 0.75 * y_ss

    t_25 = time[np.where(yt >= y_ss_25)[0][0]]
    t_75 = time[np.where(yt >= y_ss_75)[0][0]]

    r = t_25 / t_75

    P = -18.56075 * r + 0.57311 / (r - 0.20747) + 4.16423

    X = 14.2797 * r**3 - 9.3891 * r**2 + 0.25437 * r + 1.32148

    tau_2 = (t_75 - t_25) / (X * (1 + 1/P))
    tau_1 = tau_2 / P

    return k, tau_1, tau_2


def first_order_system_identification(time, xt, yt):

    n = len(time)

    y_ss = np.mean(yt[int(4/6*n) : int(5/6*n)])
    x_ss = xt[-1]

    k = y_ss / x_ss  # Steady state gain (A_0)

    y_ss_63 = 0.63 * y_ss  # t=tau
    y_ss_86 = 0.86 * y_ss  # t=2*tau
    y_ss_95 = 0.95 * y_ss  # t=3*tau

    t_63 = time[np.where(yt >= y_ss_63)[0][0]] - 3
    t_75 = time[np.where(yt >= y_ss_86)[0][0]] - 3
    t_95 = time[np.where(yt >= y_ss_95)[0][0]] - 3

    tau = (t_63 + t_75/2 + t_95/3) / 3

    return k, tau


def main():

    step_path = "../TestData/OriginalMotorStepResponseAdjusted"

    plot_single = True
    plot_all_tau = False
    save_results = False

    data_id = 45

    if plot_all_tau:
        time_constant_dict = {'torque': [],
                              'time_constant': []}

        for file in os.listdir(step_path):

            df = pd.read_csv(step_path + "/" + file)
            x_t = np.array(df['torque_in'])
            y_t = np.array(df['torque_out'])
            t = np.array(df['time'])

            step_amplitude = round(x_t[-1], 2)

            gain, tau = first_order_system_identification(t, x_t, y_t)

            time_constant_dict['torque'] += [step_amplitude]
            time_constant_dict['time_constant'] += [tau]

            tau_average = np.mean([i for i in time_constant_dict['time_constant'] if i <= 0.07])

        plt.suptitle("Time Constants vs Demanded Torque")
        plt.title("Average Time Constant: {}".format(round(tau_average, 5)), fontsize=10)
        plt.xlabel("Torque Step [Nm]")
        plt.ylabel("Time Constant [-]")
        plt.grid()
        plt.plot([0, max(time_constant_dict['torque'])], [tau_average, tau_average], color='black', linestyle='--')
        plt.scatter(time_constant_dict['torque'], time_constant_dict['time_constant'], marker='x', color='red')
        plt.xlim([0, max(time_constant_dict['torque'])])
        plt.ylim([0, None])
        plt.show()

    if save_results:
        results_path = "../TestResults"

        df_tau = pd.DataFrame.from_dict(time_constant_dict)

        df_tau.to_csv(results_path + "/" + "TimeConstantResults.csv")

    if plot_single:

        for file in os.listdir(step_path):
            if int(file.split("-")[3]) == data_id:
                filename = file

        df = pd.read_csv(step_path + "/" + filename)
        x_t = np.array(df['torque_in'])
        y_t = np.array(df['torque_out'])
        t = np.array(df['time'])

        step_amplitude = round(x_t[-1], 2)

        gain, tau = first_order_system_identification(t, x_t, y_t)

        l = 0.22e-3  # Inductance from datasheet
        r = 0.4  # Resistance from datasheet

        s = control.tf('s')

        g_identified = gain / (tau * s + 1)

        g_theoretical = 1 / ((l / r) * s + 1)

        y_i, t_i = control.step(g_identified, T=3)
        y_e, t_e = control.step(g_theoretical, T=3)

        plt.suptitle("System Identification for Step Response @ {}Nm Amplitude".format(round(step_amplitude, 2)))
        plt.title("Test ID: {}".format(data_id), fontsize=8)
        plt.xlabel("Time [s]")
        plt.ylabel("Torque [Nm]")
        plt.plot(t, x_t, label='Input Step')
        plt.plot(t_i + 3, step_amplitude * y_i, label='Identified System')
        plt.plot(t_e + 3, step_amplitude * y_e, label='Theoretical System')
        plt.plot(t, y_t, label='Measured Response')
        plt.xlim([0, 6])
        plt.ylim([0, None])
        plt.grid()
        plt.legend()
        plt.show()


if __name__ == "__main__":
    main()