#include "Arduino.h"
#include "rmd_driver.h"

// Utility functions
CANMessage createMessage(byte const& motorId, byte const& command, long const& data = 0, uint16_t const& speedLimit=0)
{
    CANMessage message;

    message.id = 0x140 + motorId;
    message.len = 8;
    message.data[0] = command;
    message.data[1] = 0x00;
    message.data[2] = speedLimit & 0xFF;
    message.data[3] = (speedLimit >> 8) & 0xFF;
    message.data[4] = data & 0xFF;
    message.data[5] = (data >> 8) & 0xFF;
    message.data[6] = (data >> 16) & 0xFF;
    message.data[7] = (data >> 24) & 0xFF;
    return message;

}


int32_t messageToInt32(CANMessage const& message)
{
    return message.data[4] + (message.data[5] >> 8) +  (int32_t(message.data[6]) >> 16) +  (int32_t(message.data[7]) >> 24);
}

RMDX::RMDX(ACAN2515 *canDriver):
    canDriver_(canDriver)
{
    
}

void RMDX::reset(byte const& motorId)
{
    CANMessage message = createMessage(motorId, MyActuator::commands::RESET);
    canReadWrite(message);
}

void RMDX::enable(byte const& motorId)
{
    CANMessage message = createMessage(motorId, MyActuator::commands::ENABLE);
    canReadWrite(message);
}

void RMDX::disable(byte const& motorId)
{
    CANMessage message = createMessage(motorId, MyActuator::commands::SHUTDOWN);
    canReadWrite(message);
}

void RMDX::stop(byte const& motorId){
    CANMessage message = createMessage(motorId, MyActuator::commands::STOP);
    canReadWrite(message);
}

void RMDX::setZero(byte const& motorId)
{
    CANMessage message = createMessage(motorId, MyActuator::commands::WRITE_ENCODER_CURRENT_POS_AS_ZERO);
    canReadWrite(message);
}

void RMDX::getOffset(byte const& motorId)
{
    CANMessage message = createMessage(motorId, MyActuator::commands::READ_MULTITURN_OFFSET);
    encoderOffset = message.data[1] + (message.data[2] << 8) + (message.data[3] << 16) + (message.data[4] << 24) + (message.data[5] << 32) + (message.data[6] << 40);
    encoderOffsetDirection = message.data[7];
  
}

void RMDX::setSpeed(byte const& motorId, int32_t const& targetSpeed)
{
    CANMessage message = createMessage(motorId, MyActuator::commands::SPEED_COMMAND, targetSpeed * 100 * reductionRatio);
  
    int result = canReadWrite(message);

    decodeReturnMessage(message);
}

void RMDX::setCurrent(byte const& motorId, int16_t const& targetCurrent)
{
    CANMessage message = createMessage(motorId, MyActuator::commands::TORQUE_COMMAND, targetCurrent * 62.5);
    int result = canReadWrite(message);
    decodeReturnMessage(message);
}

void RMDX::setPosition(byte const& motorId, int32_t const& targetPosition)
{
    CANMessage message = createMessage(motorId, 0xA4, targetPosition * 100 * reductionRatio, maxSpeed);
    int result = canReadWrite(message);
    decodeReturnMessage(message);
}


void RMDX::decodeReturnMessage(CANMessage& message)
{
  
  temperature = message.data[1];
  current = message.data[2] + (message.data[3] << 8);
  speed = message.data[4] + (message.data[5] << 8);  // deg/s
  position = message.data[6] + (message.data[7] << 8);

  for (int i = 0; i < 8; i++){
    Serial.print(message.data[i], HEX);
    Serial.print(" ");
  }
    Serial.println();

  position_m = position * 360.0 / 65535;
  speed_m = speed * pi / 180.0;

  if (position_m_last > 270 && position_m < 90){
    zeroCross++;
  }
  if (position_m_last < 90 && position_m > 270){
    zeroCross--;
  }

  position_m_last = position_m;

  position_l = fmod((zeroCross*360.0 + position_m) / reductionRatio, 360.0);  
  speed_l = speed_m / reductionRatio;
}
  
int RMDX::canReadWrite(CANMessage& message, bool const& waitForReply)
{
    CANMessage dump;
    while (canDriver_->available())
        canDriver_->receive(dump);

    if (!canDriver_->tryToSend(message))
        return -1;
    if (waitForReply)
    {
      unsigned long startTime = micros();
       while (!canDriver_->available() && micros() - startTime < 100000)
           delay(1);
       if (canDriver_->available())
          canDriver_->receive(message);
       else
          return -2;
    }
    return 0;
}