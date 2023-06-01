/// \file RMDX.h
/// \brief A simple driver for the RMDX brushless motor from MyActuator
///
/// \details This code is meant to work as a simple example for communicating with
///          the RMDX brushless motors. Note that only single-motor commands are implemented.

#ifndef MYACTUATOR_RMDX
#define MYACTUATOR_RMDX

#include <ACAN2515.h>
#include <Arduino.h>

namespace MyActuator::commands
{
    byte const READ_POS_KP = 0x30;
    byte const READ_POS_KI = 0x31;
    byte const READ_VEL_KP = 0x32;
    byte const READ_VEL_KI = 0x33;
    byte const READ_TORQUE_KP = 0x34;
    byte const READ_TORQUE_KI = 0x35;
    byte const WRITE_POS_KP_RAM = 0x36;
    byte const WRITE_POS_KI_RAM = 0x37;
    byte const WRITE_VEL_KP_RAM = 0x38;
    byte const WRITE_VEL_KI_RAM = 0x39;
    byte const WRITE_TORQUE_KP_RAM = 0x3A;
    byte const WRITE_TORQUE_KI_RAM = 0x3B;
    byte const WRITE_POS_KP_ROM = 0x3C;
    byte const WRITE_POS_KI_ROM = 0x3D;
    byte const WRITE_VEL_KP_ROM = 0x3E;
    byte const WRITE_VEL_KI_ROM = 0x3F;
    byte const WRITE_TORQUE_KP_ROM = 0x40;
    byte const WRITE_TORQUE_KI_ROM = 0x41;
    byte const READ_ACCEL = 0x42;
    byte const WRITE_ACCEL = 0x43;
    byte const READ_MULTITURN_POS = 0x60;
    byte const READ_ORIGINAL_POS = 0x61;
    byte const READ_MULTITURN_OFFSET = 0x62;
    byte const WRITE_ENCODER_ZERO = 0x63;
    byte const WRITE_ENCODER_CURRENT_POS_AS_ZERO = 0x64;
    byte const READ_MULTITURN_ANGLE = 0x92;

    byte const READ_MOTOR_STATUS1 = 0x9A;
    byte const READ_MOTOR_STATUS2 = 0x9C;
    byte const READ_MOTOR_STATUS3 = 0x9D;

    byte const SHUTDOWN = 0x80;
    byte const STOP = 0x81;
    byte const ENABLE = 0x88;

    byte const TORQUE_COMMAND = 0xA1;
    byte const SPEED_COMMAND = 0xA2;
    byte const ABS_POS_COMMAND = 0xA7;
    byte const REL_POS_COMMAND = 0xA8;

    byte const READ_OPERATING_MODE = 0x70;
    byte const READ_MOTOR_POWER = 0x71;
    byte const READ_AUXILIARY_VOLTAGE = 0x72;
    byte const WRITE_TORQUE_FEEDFORWARD = 0x73;

    byte const RESET = 0x76;
    byte const BRAKE_RELEASE = 0x77;
    byte const BRAKE_LOCK = 0x78;
    byte const CAN_ID_SETUP = 0x79;
    byte const READ_RUNTIME = 0xB1;
    byte const READ_SOFTWARE_VERSION = 0xB2;
    byte const COMM_INTERRUPT_TIMEOUT = 0xB3;
}


class RMDX{
    public:
        RMDX(ACAN2515 *canDriver);

        int8_t temperature;
        int16_t current;
        int16_t speed;
        uint16_t position;
        float speed_m;
        float position_m;
        float speed_l;
        float position_l;

        uint8_t print_message[8] = {0, 0, 0, 0, 0, 0, 0, 0};

        int zeroCross = 0;

        float pi = 3.14159265;

        uint8_t reductionRatio = 9;
        uint16_t maxSpeed = 36000;

        uint64_t encoderOffset = 0;
        bool encoderOffsetDirection = 0;         

        /// \brief Reset a given motor
        /// \param[in] motorId Motor id
        void reset(byte const& motorId);
        void enable(byte const& motorId);
        void disable(byte const& motorId);
        void setZero(byte const& motorId);
        void stop(byte const& motorId);

        /// \brief Close-loop speed contro: set motor target speed
        /// \param[in] motorId Motor id
        /// \param[in] targetSpeed Target speed, 0.01deg/s/LSB
        void setSpeed(byte const& motorId, int32_t const& targetSpeed);

        void setCurrent(byte const& motorId, int16_t const& targetCurrent);

        void setPosition(byte const& motorId, int32_t const& targetPosition);

        void getOffset(byte const& motorId);
        
    private:

        /// \brief Send and recieve a data frame from the motor.
        ///
        /// \param[in, out] message The message to send, modified in place.
        /// \param waitForReply Whether or not to wait for a reply
        /// \return 0 on succes ; -1 if write failed ; -2 if write succeeded but read failed.
        int canReadWrite(CANMessage& message, bool const& waitForReply = true);

        void decodeReturnMessage(CANMessage& message);

        float position_m_last;

        ACAN2515 *canDriver_;
};

#endif