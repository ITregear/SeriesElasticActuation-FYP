# Author: ivantregear
# Date Created: 28/02/2023
# Description:
# When I wrote this code only God I and knew how it worked.
# Now only god knows it.


import numpy as np
import serial
import time as t
import keyboard
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
from simple_pid import PID

from can_transceiver import Motor
from NetFT import Sensor


class SeriesElasticActuator:
    def __init__(self, can_port, enc_port):
        self.can_port = can_port
        self.enc_port = enc_port
        self.can_baud = 115200
        self.enc_baud = 115200

        self.enc_ser = None
        self.stiffness = 2155.4  # Nm/rad, for 7mm Spring

        self.motor_enable_flag = False
        self.rmd = None
        self.n_calibration_samples = 100
        self.enc_initial = 0

        self.time = 0
        self.t0 = 0
        self.t1 = 0
        self.t1_last = 0
        self.sampling_freq = 0

        self.displacement_deg = 0
        self.displacement_rad = 0
        self.enc_torque = 0
        self.filtered_torque = 0
        self.ati_torque = 0

        self.feedback = False
        self.pid = None

        self.filter_on = False
        self.covariance = 0
        self.measurement_noise = 0
        self.f = None

    def init_hardware(self):
        self.rmd = Motor()
        self.rmd.serial_begin(port=self.can_port, baudrate=self.can_baud)
        self.enc_ser = serial.Serial(port=self.enc_port, baudrate=self.enc_baud)
        print("Connected to Serial Port {}".format(self.enc_port))
        if self.enc_ser.in_waiting > 30:
            self.enc_ser.readline()

        t.sleep(1)
        print("Calibrating Encoder")
        enc_sum = 0
        for _ in range(self.n_calibration_samples):
            try:
                while self.enc_ser.in_waiting > 5:
                    self.enc_ser.readline()
                enc_sum += float(self.enc_ser.readline().decode("UTF-8"))
            except:
                self.n_calibration_samples -= 1
                pass

        self.enc_initial = enc_sum / self.n_calibration_samples
        print("Encoder Calibrated, Zero: {}".format(self.enc_initial))

    def init_filter(self):
        self.f = KalmanFilter(dim_x=2, dim_z=1)
        self.f.x = np.array([0, 0])  # State Matrix
        self.f.F = np.array([[1, 1],
                             [0, 1]])  # State Transition Matrix
        self.f.H = np.array([[1, 0]])  # Measurement Function
        self.f.P *= self.covariance  # Covariance matrix (already Identity, so need to multiply not initiate)
        self.f.R = self.measurement_noise  # Measurement noise
        self.f.Q = Q_discrete_white_noise(dim=2, dt=0.001, var=0.13)  # Process noise

        self.filter_on = True

    def init_pid(self, kp, ki, kd):
        self.pid = PID(kp, ki, kd, setpoint=0)
        self.pid.output_limits = (-10, 10)

    def update(self):
        if not self.motor_enable_flag:
            print("Enabling Motor")
            self.rmd.enable_motor()
            self.rmd.set_zero()
            print("Motor Enabling")
            print("Waiting for Startup")
            t.sleep(6)
            self.motor_enable_flag = True
            self.t0 = t.perf_counter()
            print("Test Commenced")

        if self.motor_enable_flag:
            self.t1 = t.perf_counter()
            self.time = self.t1 - self.t0
            self.sampling_freq = 1 / (self.t1 - self.t1_last)
            self.t1_last = self.t1

    def get_torque(self):
        while self.enc_ser.in_waiting > 30:
            self.enc_ser.readline()
        self.displacement_deg = float(self.enc_ser.readline().decode("UTF-8")) - self.enc_initial
        self.displacement_rad = self.displacement_deg * np.pi / 180

        self.enc_torque = -self.stiffness * self.displacement_rad
        if self.filter_on:
            self.f.predict()
            self.f.update(self.enc_torque)
            self.filtered_torque = self.f.x[0]

    def controller(self, set_point):

        if self.feedback:
            self.pid.setpoint = set_point
            u = self.pid(self.filtered_torque) + set_point  # Use self.filtered_torque for SEA feedback
        else:
            u = set_point

        self.rmd.set_torque(u)


def main():
    sea = SeriesElasticActuator("COM5", "COM9")
    sea.init_hardware()

    ati_gamma = Sensor("192.168.1.1")
    ati_gamma.tare(100)
    cpf = 1000000  # Counts per Force (from ATI Gamma calibration file)
    set_torque = 0

    # Setup Kalman Filter
    sea.covariance = 100
    sea.measurement_noise = 0.1
    sea.init_filter()

    while True:
        try:
            sea.update()
            sea.get_torque()

            if keyboard.is_pressed('w'):
                set_torque += 0.001
            if keyboard.is_pressed('s'):
                set_torque -= 0.001

            sea.controller(set_point=set_torque)

            print(round(set_torque, 2), "\t",
                  round(-ati_gamma.getMeasurement()[5]/cpf, 2), "\t",
                  round(sea.filtered_torque, 2))

        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            sea.rmd.disable_motor()


if __name__ == "__main__":
    main()
