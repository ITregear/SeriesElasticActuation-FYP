#include <ACAN2515.h>
#include <SPI.h>
#include "rmd_driver.h"

// Define JoyStick Pins
#define UP A1
#define DOWN A3
#define LEFT A2
#define RIGHT A5
#define CLICK A4

// Define LED Pins
#define LED2 8
#define LED3 7

// Configure CAN bus adapter.
static const byte MCP2515_CS  = 10; // CS input of MCP2515
static const byte MCP2515_INT =  2; // INT output of MCP2515
ACAN2515 can (MCP2515_CS, SPI, MCP2515_INT);

// Select the quartz frequency of your MPC2515 - 8MHz or 16MHz are often used.
static const uint32_t QUARTZ_FREQUENCY = 8UL * 1000UL * 1000UL; // 8 MHz quartz
// Select CAN frequency: 500kbps or 1Mbps can be used.
// Note however that, if a 8MHz quartz is used on the MPC2515, only 500kbps can be used, 1MHz is too fast.
static const uint32_t CAN_BAUDRATE = 500UL * 1000UL; // 500kpbs CAN

RMDX motor(&can);  // Create motor object

int motor_enable = 1;  // 1 if motor is enabled
int32_t var_demand = 0;  // Demanded variable (could be current, position or speed)

// Serial Read Parameters
const byte numChars = 32;  // Length of received char array from Serial
char receivedChars[numChars];  // Received char array from Serial
char tempChars[numChars];        // Temporary array for use when parsing
bool newData = false;  // Flag to check if newData has been received

void setup() {
  Serial.begin(115200);
  delay(1000);
  SPI.begin();
  
  ACAN2515Settings settings (QUARTZ_FREQUENCY, CAN_BAUDRATE);
  const uint16_t errorCode = can.begin (settings, [] { can.isr () ; });
  settings.mRequestedMode = ACAN2515Settings::NormalMode;
  // Enable the motor with ID 1 (i.e. 141), and give it some time to start up.

  motor.enable(1);
  delay(1000);

  pinMode(UP, INPUT_PULLUP);
  pinMode(DOWN, INPUT_PULLUP);
  pinMode(LEFT, INPUT_PULLUP);
  pinMode(RIGHT, INPUT_PULLUP);

  digitalWrite(LED2, LOW);
  digitalWrite(LED3, LOW);

}


void loop() {

  if (motor_enable == 0){
    motor.disable(1);
  }

  var_demand = 36000;

  // Do not touch this section
  recvWithStartEndMarkers();  // Check Serial and receive data if there is newData
  if (newData == true) {
      strcpy(tempChars, receivedChars);  // Copy variables to prevent them being altered
      parseData();  // Parse data (split where there are commas)
      newData = false;  // Set to false
  }

  motor.setSpeed(1, var_demand);
  
 /* Serial.print(motor.current);
  Serial.print(",");
  Serial.print(motor.speed_l, 4);
  Serial.print(",");
  Serial.println(motor.position_l, 4); */


}


// Do not touch this function
void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static byte ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;

    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();

        if (recvInProgress == true) {
            if (rc != endMarker) {
                receivedChars[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else {
                receivedChars[ndx] = '\0'; // terminate the string
                recvInProgress = false;
                ndx = 0;
                newData = true;
            }
        }

        else if (rc == startMarker) {
            recvInProgress = true;
        }
    }
}

// Only touch this function if more data is being sent to Python code
void parseData() {      // split the data into its parts

    char * strtokIndx; // this is used by strtok() as an index

    strtokIndx = strtok(tempChars,",");
    var_demand = atoi(strtokIndx);
 
    //strtokIndx = strtok(NULL, ",");
    //var_demand = atoi(strtokIndx);


    // How to add a new variable
    // Currently, data is sent as <0, 0, 0, 0>
    // If a fourth parameter was to be sent (<0, 0, 0, 0, 1>), the following lines need to be added

    // strtokIndx = strtok(NULL, ", "); This reads the string, from where it was previously cut, up until the next comma
    // newVariableName = atoi(strtokIndx); atoi is 'to integer'. If newVariable is a float, atof is needed etc


}

