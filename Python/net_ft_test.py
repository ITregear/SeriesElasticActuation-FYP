# Author: ivantregear
# Date Created: 05/12/2022
# Description: 

# When I wrote this code only got I and knew how it worked.
# Now only god knows it.


from NetFT import Sensor
import matplotlib.pyplot as plt
import time
import numpy as np


def main():
    ati_gamma = Sensor("192.168.1.1")
    cpf = 1000000

    fig, ax = plt.subplots()

    line1, = ax.plot([0, 1], [0, 1], label="Fx")
    line2, = ax.plot([0, 1], [0, 1], label="Fy")
    line3, = ax.plot([0, 1], [0, 1], label="Fz")
    line4, = ax.plot([0, 1], [0, 1], label="Tx")
    line5, = ax.plot([0, 1], [0, 1], label="Ty")
    line6, = ax.plot([0, 1], [0, 1], label="Tz")
    ax.legend()
    ax.set_title("ATI Gamma Force-Torque Measurements")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Force/Torque [N/Nm]")
    t0 = time.perf_counter()

    t_arr = []
    fx_arr = []
    fy_arr = []
    fz_arr = []
    tx_arr = []
    ty_arr = []
    tz_arr = []

    plt.ion()

    max_x = 10
    max_x_flag = False
    plot_flag = True

    ati_gamma.tare(100)

    while True:
        try:

            data = np.array(ati_gamma.getMeasurement()) / cpf
            print(round(data[2], 3), "Nm" "\t", round(data[2] / 9.81 * 1000, 3), "g")

            t = time.perf_counter() - t0

            t_arr += [t]
            fx_arr += [data[0]]
            fy_arr += [data[1]]
            fz_arr += [data[2]]
            tx_arr += [data[3]]
            ty_arr += [data[4]]
            tz_arr += [data[5]]

            if t >= max_x:
                if not max_x_flag:
                    i2 = len(t_arr)
                    i_len = i2
                    max_x_flag = True
                i2 = len(t_arr)
                i1 = i2 - i_len

                ax.set_xlim(t_arr[-1] - max_x, t_arr[-1])
                ax.set_ylim(np.min(np.column_stack([fx_arr[i1:i2], fy_arr[i1:i2], fz_arr[i1:i2], tx_arr[i1:i2],
                                                    ty_arr[i1:i2], tz_arr[i1:i2]])),
                            np.max(np.column_stack([fx_arr[i1:i2], fy_arr[i1:i2], fz_arr[i1:i2], tx_arr[i1:i2],
                                                    ty_arr[i1:i2], tz_arr[i1:i2]])))
            else:
                ax.set_xlim(0, t_arr[-1])
                ax.set_ylim(np.min(np.column_stack([fx_arr, fy_arr, fz_arr, tx_arr,
                                                    ty_arr, tz_arr])),
                            np.max(np.column_stack([fx_arr, fy_arr, fz_arr, tx_arr,
                                                    ty_arr, tz_arr])))
            if plot_flag:
                line1.set_data(t_arr, fx_arr)
                line2.set_data(t_arr, fy_arr)
                line3.set_data(t_arr, fz_arr)
                line4.set_data(t_arr, tx_arr)
                line5.set_data(t_arr, ty_arr)
                line6.set_data(t_arr, tz_arr)
                plt.pause(0.0001)

        except KeyboardInterrupt:
            print("OOPS")
            break


if __name__ == "__main__":
    main()
