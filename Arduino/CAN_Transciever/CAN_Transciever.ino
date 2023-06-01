#include <ACAN2515.h>
#include <SPI.h>


// Configure CAN bus adapter.
static const byte MCP2515_CS  = 10; // CS input of MCP2515
static const byte MCP2515_INT =  2; // INT output of MCP2515
ACAN2515 can (MCP2515_CS, SPI, MCP2515_INT);

// Select the quartz frequency of your MPC2515 - 8MHz or 16MHz are often used.
static const uint32_t QUARTZ_FREQUENCY = 16UL * 1000UL * 1000UL; // 8 MHz quartz
// Select CAN frequency: 500kbps or 1Mbps can be used.
// Note however that, if a 8MHz quartz is used on the MPC2515, only 500kbps can be used, 1MHz is too fast.
static const uint32_t CAN_BAUDRATE = 1000UL * 1000UL; // 500kpbs CAN

byte recvFrame[8] = {0, 0, 0, 0, 0, 0, 0, 0};
byte sendFrame[8] = {0, 0, 0, 0, 0, 0, 0, 0};

// Serial Read Parameters
const byte numChars = 32;  // Length of received char array from Serial
char receivedChars[numChars];  // Received char array from Serial
char tempChars[numChars];        // Temporary array for use when parsing
bool newData = false;  // Flag to check if newData has been received

unsigned long previous_millis = 0;
const long interval = 5;


void setup() {
  Serial.begin(115200);
  delay(1000);
  SPI.begin();

  ACAN2515Settings settings (QUARTZ_FREQUENCY, CAN_BAUDRATE);
  const uint16_t errorCode = can.begin (settings, [] { can.isr () ; });
  settings.mRequestedMode = ACAN2515Settings::NormalMode;
  delay(1000);

}

void loop() {

  CANMessage frame;

  frame.id = 0x140 + 1;
  frame.len = 8;

  // Do not touch this section
  recvWithStartEndMarkers();  // Check Serial and receive data if there is newData
  if (newData == true) {
      strcpy(tempChars, receivedChars);  // Copy variables to prevent them being altered
      parseData();  // Parse data (split where there are commas)
      
      for (int i = 0; i  < 8; i++){
        frame.data[i] = sendFrame[i];
      }

      can.tryToSend(frame);

      newData = false;  // Set to false
  }
  // Following removed to increase fs from 125Hz to 600Hz
  // Uncomment, and also uncomment complimentary lines in Python to read data from motor
  
  // if (can.available()){
  //   can.receive(frame);
  //   
  //   for (int i = 0; i < 8; i++){
  //     recvFrame[i] = frame.data[i];
  //   }
  //   printFrame();
// 
  // }
  
  

  unsigned long current_millis = millis();

  if (current_millis - previous_millis >= interval){
    previous_millis = current_millis;
    
  }

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

// Only touch this function if more data is being sent from Python code
void parseData() {      // split the data into its parts

    char * strtokIndx; // this is used by strtok() as an index

    strtokIndx = strtok(tempChars," ");
    sendFrame[0] = atoi(strtokIndx);

    strtokIndx = strtok(NULL," ");
    sendFrame[1] = atoi(strtokIndx);

    strtokIndx = strtok(NULL," ");
    sendFrame[2] = atoi(strtokIndx);

    strtokIndx = strtok(NULL," ");
    sendFrame[3] = atoi(strtokIndx);

    strtokIndx = strtok(NULL," ");
    sendFrame[4] = atoi(strtokIndx);

    strtokIndx = strtok(NULL," ");
    sendFrame[5] = atoi(strtokIndx);

    strtokIndx = strtok(NULL," ");
    sendFrame[6] = atoi(strtokIndx);
 
    strtokIndx = strtok(NULL, " ");
    sendFrame[7] = atoi(strtokIndx);


    // How to add a new variable
    // Currently, data is sent as <0, 0, 0, 0>
    // If a fourth parameter was to be sent (<0, 0, 0, 0, 1>), the following lines need to be added

    // strtokIndx = strtok(NULL, ", "); This reads the string, from where it was previously cut, up until the next comma
    // newVariableName = atoi(strtokIndx); atoi is 'to integer'. If newVariable is a float, atof is needed etc


}


void printFrame(){
  
  for (int i = 0; i < 8; i++){
    Serial.print(recvFrame[i]);
    Serial.print(" ");
  }
  Serial.println();

}
