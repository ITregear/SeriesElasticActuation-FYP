# Author: ivantregear
# Date Created: 28/11/2022
# Description:
# When I wrote this code only got I and knew how it worked.
# Now only god knows it.


import numpy as np
import serial
import time as t
import keyboard
import matplotlib.pyplot as plt


class Motor:
    def __init__(self):
        self.ser = None
        self.receive_frame = np.zeros(8)
        self.last_receive_frame = np.zeros(8)
        self.send_frame = np.zeros(8)
        self.command_list = {
            "READ_POS_KP": 0x30,
            "READ_POS_KI": 0x31,
            "READ_SPEED_KP": 0x32,
            "READ_SPEED_KI": 0x33,
            "READ_CURRENT_KP": 0x34,
            "READ_CURRENT_KI": 0x35,
            "WRITE_POS_KP_RAM": 0x36,
            "WRITE_POS_KI_RAM": 0x37,
            "WRITE_SPEED_KP_RAM": 0x38,
            "WRITE_SPEED_KI_RAM": 0x39,
            "WRITE_CURRENT_KP_RAM": 0x3A,
            "WRITE_CURRENT_KI_RAM": 0x3B,
            "WRITE_POS_KP_ROM": 0x3C,
            "WRITE_POS_KI_ROM": 0x3D,
            "WRITE_SPEED_KP_ROM": 0x3E,
            "WRITE_SPEED_KI_ROM": 0x3F,
            "WRITE_CURRENT_KP_ROM": 0x40,
            "WRITE_CURRENT_KI_ROM": 0x41,
            "READ_ACCEL": 0x42,
            "WRITE_ACCEL_ROM": 0x43,
            "READ_MULTITURN_POS": 0x60,
            "READ_MULTITURN_POS_ORIGINAL": 0x61,
            "READ_MULTITURN_OFFSET": 0x62,
            "WRITE_MULTITURN_TO_ROM": 0x63,
            "WRITE_CURRENT_MULTITURN_TO_ROM": 0x64,
            "READ_ENCODER_DATA": 0x90,
            "WRITE_ENCODER_TO_ROM": 0x91,
            "WRITE_CURRENT_POS_TO_ROM": 0x19,
            "READ_MULTITURN_ANGLE": 0x92,
            "READ_SINGLE_ANGLE_COMMAND": 0x94,
            "READ_STATUS_1_&_ERRORS": 0x9A,
            "READ_STATUS_2": 0x9C,
            "READ_STATUS_3": 0x9D,
            "MOTOR_OFF": 0x80,
            "MOTOR_STOP": 0x81,
            "MOTOR_RUN": 0x88,
            "SET_TORQUE": 0xA1,
            "SET_SPEED": 0xA2,
            "SET_POS_1": 0xA3,
            "SET_POS_2": 0xA4,
            "SET_POS_3": 0xA5,
            "SET_POS_4": 0xA6,
            "SET_POS_5": 0xA7,
            "SET_POS_6": 0xA8,
            "SET_MULTITURN_INCREMENTAL_1": 0xA7,
            "SET_MULTITURN_INCREMENTAL_2": 0xA8,
            "READ_MODE": 0x70,
            "READ_POWER": 0x71,
            "READ_VOLTAGE": 0x72,
            "TF": 0x73,
            "SYSTEM_RESET": 0x76,
            "OPEN_BRAKE": 0x77,
            "CLOSE_BRAKE": 0x78,
            "SET_CAN_ID": 0x79
        }

        self.temperature_bytes = 0
        self.current_bytes = 0
        self.speed_bytes = 0
        self.position_bytes = 0

        self.motor_position = 0
        self.motor_speed = 0
        self.load_position = 0
        self.load_speed = 0
        self.current = 0

        self.motor_position_last = 0
        self.reduction_ratio = 9
        self.torque_constant = 1.393  # Nm/A
        self.zero_cross = 0

        self.speed_limit = 2**16 - 1
        self.encoder_offset_single = 0
        self.encoder_offset_multiturn = 0
        self.encoder_bytes_raw = 0

    def serial_begin(self, port, baudrate):
        self.ser = serial.Serial(port, baudrate)
        self.ser.flushInput()
        self.ser.flushOutput()
        print("Connected to Serial Port " + port)
        t.sleep(1)

    def send_cam_frame(self, frame):

        self.send_frame = frame
        string_to_send = "<" + str(int(frame[0])) + " " + \
                         str(int(frame[1])) + " " + \
                         str(int(frame[2])) + " " + \
                         str(int(frame[3])) + " " + \
                         str(int(frame[4])) + " " + \
                         str(int(frame[5])) + " " + \
                         str(int(frame[6])) + " " + \
                         str(int(frame[7])) + ">"

        self.ser.write(string_to_send.encode('UTF-8'))
        # self.receive_can_frame()

    def decode_can_frame(self):
        self.temperature_bytes = self.receive_frame[1]
        self.current_bytes = self.receive_frame[2] + (self.receive_frame[3] << 8)
        self.speed_bytes = self.receive_frame[4] + (self.receive_frame[5] << 8)
        self.position_bytes = self.receive_frame[6] + (self.receive_frame[7] << 8)

        self.motor_position = self.position_bytes * 360 / 2 ** 16
        self.motor_speed = self.speed_bytes.astype('int16')
        self.current = self.current_bytes.astype('int16') * 32 / 2000

        if self.motor_position_last > 270 and self.motor_position < 90:
            self.zero_cross += 1
        if self.motor_position_last < 90 and self.motor_position > 270:
            self.zero_cross -= 1

        self.motor_position_last = self.motor_position

        self.load_position = ((self.zero_cross * 360 + self.motor_position) / self.reduction_ratio) % 360
        self.load_speed = self.motor_speed / self.reduction_ratio

    def receive_can_frame(self):

        # All instances removed for testing as reading from CAN slows refresh rate down to 125Hz
        # With nothing read back from CAN Arduino, refresh rate as high as 600Hz possible
        # To read from motor, must uncomment complimentary lines on Arduino, and add
        # self.receive_can_frame() and self.decode_can_frame() back to any and all commands that speak to motor

        if self.ser.in_waiting > 1:
            self.ser.flush()

        get_data = self.ser.readline().decode('UTF-8', errors='ignore')[0:][:-2]
        self.receive_frame = np.fromstring(get_data, dtype='int', count=8, sep=' ')

    def enable_motor(self):
        frame = [self.command_list["MOTOR_RUN"], 0, 0, 0, 0, 0, 0, 0]
        self.send_cam_frame(frame)

    def disable_motor(self):
        frame = [self.command_list["MOTOR_OFF"], 0, 0, 0, 0, 0, 0, 0]
        self.send_cam_frame(frame)

    def stop_motor(self):
        frame = [self.command_list["MOTOR_STOP"], 0, 0, 0, 0, 0, 0, 0]
        self.send_cam_frame(frame)
        t.sleep(1)

    def set_zero(self):
        frame = [self.command_list["WRITE_CURRENT_MULTITURN_TO_ROM"], 0, 0, 0, 0, 0, 0, 0]
        self.send_cam_frame(frame)

    def set_speed(self, speed):
        speed = int(speed * 100 * self.reduction_ratio)
        frame = [self.command_list["SET_SPEED"], 0, 0, 0, speed & 0xFF, (speed >> 8) & 0xFF, (speed >> 16) & 0xFF,
                 (speed >> 24) & 0xFF]
        self.send_cam_frame(frame)
        # self.decode_can_frame()

    def set_position(self, position):
        position = int(position * 100 * self.reduction_ratio)
        frame = [self.command_list["SET_POS_2"], 0, self.speed_limit & 0xFF, (self.speed_limit >> 8) & 0xFF,
                 position & 0xFF, (position >> 8) & 0xFF, (position >> 16) & 0xFF, (position >> 24) & 0xFF]
        self.send_cam_frame(frame)
        # self.decode_can_frame()

    def set_torque(self, torque):
        torque = int(self.constrain(torque * 2000 / 32 / self.torque_constant, -2000, 2000))
        frame = [self.command_list["SET_TORQUE"], 0, 0, 0, torque & 0xFF, (torque >> 8) & 0xFF, (torque >> 16) & 0xFF,
                 (torque >> 24) & 0xFF]
        self.send_cam_frame(frame)
        # self.decode_can_frame()

    def constrain(self, val, val_min, val_max):
        return min(val_max, max(val_min, val))


def sine_sweep_exp(t, T, f1, f2):
    return np.sin(2 * np.pi * f1 * T / np.log(f2 / f1) * (np.exp(t / T * np.log(f2 / f1)) - 1))


def sine_sweep_lin(t, T, f1, f2):
    return np.sin(2 * np.pi * (f1 * t + (f2 - f1) / (2 * T) * t**2))


def wrap(array, phase):
    return (np.array(array) + phase) % (2 * phase) - phase


def main():
    # Hardware init
    arduino_port = "COM5"  # Default COM port
    baud_rate = 115200  # Default Baud Rate

    # Setting up Encoder Serial Port
    enc_ser = serial.Serial("COM9", baudrate=115200, timeout=0.1)

    rmd = Motor()
    rmd.serial_begin(baud=baud_rate, com=arduino_port)

    t.sleep(1)  # Wait for hardware to initialise

    # Variable Declaration
    enabled_flag = False  # True if motor is enabled
    plot_flag = True  # True if plot desired
    set_position = 0  # Motor set position
    enc_bytes = 0

    input_pos = np.empty(1)
    motor_encoder_pos = np.empty(1)
    external_encoder_pos = np.empty(1)
    time_array = np.empty(1)

    while True:
        try:

            if enc_ser.in_waiting > 0:
                while enc_ser.in_waiting > 30:
                    enc_ser.readline()
                enc_bytes = -float(enc_ser.readline().decode("UTF-8"))

            if keyboard.is_pressed('e'):
                rmd.enable_motor()
                t.sleep(6)
                enabled_flag = True
                t0 = t.perf_counter()
            if keyboard.is_pressed('f'):
                rmd.disable_motor()

            if enabled_flag:
                if keyboard.is_pressed('w'):
                    set_position += 0.1
                if keyboard.is_pressed('s'):
                    set_position -= 0.1

                rmd.set_position(set_position)

                time = t.perf_counter() - t0

                input_pos = np.append(input_pos, set_position)
                motor_encoder_pos = np.append(motor_encoder_pos, rmd.load_position)
                external_encoder_pos = np.append(external_encoder_pos, enc_bytes)
                time_array = np.append(time_array, time)

            print("Pos1: {}\tPos2: {}\tPos3: {}".format(round(set_position, 3), enc_bytes, round(rmd.load_position, 3)))

        except KeyboardInterrupt:
            rmd.disable_motor()
            print("Keyboard Interrupt")

            if plot_flag:

                motor_encoder_pos = motor_encoder_pos - np.mean(motor_encoder_pos[:300])
                external_encoder_pos = external_encoder_pos - np.mean(external_encoder_pos[:300])
                fig = plt.figure(figsize=(10, 5))
                plt.plot(time_array, input_pos, label="Desired Position")
                plt.plot(time_array, motor_encoder_pos, label="Motor Encoder")
                plt.plot(time_array, external_encoder_pos, label="External Encoder")
                plt.xlim([2, None])
                plt.title("Position Control Encoder Comparison")
                plt.grid()
                plt.legend()
                plt.xlabel("Time (s)")
                plt.ylabel("Position (deg)")
                plt.show()

            break


if __name__ == "__main__":
    main()
