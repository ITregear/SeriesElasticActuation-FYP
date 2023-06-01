#include "AS5311.h"

// Script used to calibrate the AS5311 magnetic encoder
// Type desired angle rotation into Serial, and after pre-determined time period
// Total measured angle will be returned
// This will then calculate the true count to angle [deg] required

AS5311 myAS5311(2,3,4,5); // data, clock, chip select, index

double count = 0;
double enc_pos = 0;
double enc_pos_last = 0;
double coeff = 0.0008153475;
double angle = 0;

bool testFlag = false;
bool testComplete = false;
float testAngle = 0;
const long testTime = 5000;  // 5 seconds
const long loadingBarInterval = 500;  // 0.5 seconds
long startTime = 0;
long lastLoadingBar = 0;

double initialAngle = 0;
double finalAngle = 0;
double newCoeff = 0;

// Serial Read Parameters
const byte numChars = 32;  // Length of received char array from Serial
char receivedChars[numChars];  // Received char array from Serial
char tempChars[numChars];        // Temporary array for use when parsing
bool newData = false;  // Flag to check if newData has been received



void setup()
{
  Serial.begin(115200);

  Serial.println("Type in angle as <angle> and press enter to start test");
}

void loop()
{
  enc_pos = myAS5311.encoder_value();

  if (enc_pos_last > 4096*0.75 && enc_pos < 4096*0.25){
    count += 1;
  }
  if (enc_pos_last < 4096*0.25 && enc_pos > 4096*0.75){
    count -= 1;
  }
  enc_pos_last = enc_pos;

  angle = coeff * (4096.0*count + enc_pos);

  // Do not touch this section
  recvWithStartEndMarkers();  // Check Serial and receive data if there is newData

  if (newData == true){
      testFlag = true;
      initialAngle = angle;
      startTime = millis();
      Serial.println("Test Progress:");
      Serial.print("[");
    }

  if (newData == true) {
      strcpy(tempChars, receivedChars);  // Copy variables to prevent them being altered
      parseData();  // Parse data (split where there are commas)

      newData = false;  // Set to false
  }

  

  if (testFlag == true){

    finalAngle = angle;
    if (millis() - startTime >= testTime){
      testFlag = false;
      testComplete = true;
    }

    if (millis() - lastLoadingBar >= loadingBarInterval){
      Serial.print(" __ ");
      lastLoadingBar = millis();
    }
    
  }

  if (testComplete == true){
    Serial.println(" ]");
    Serial.print("Original Coefficient: ");
    Serial.println(coeff, 10);

    newCoeff = abs(testAngle / (finalAngle - initialAngle)) * coeff;
    testComplete = false;

    Serial.print("New Coefficient: ");
    Serial.println(newCoeff, 10);
    Serial.println("");
    Serial.print("Percentage Error:");
    Serial.print((newCoeff - coeff) / coeff * 100);
    Serial.println("%");
    Serial.print("Total Angle Change: ");
    Serial.print(finalAngle - initialAngle, 4);
    Serial.println("deg");
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
    testAngle = atof(strtokIndx);

    // How to add a new variable
    // Currently, data is sent as <0, 0, 0, 0>
    // If a fourth parameter was to be sent (<0, 0, 0, 0, 1>), the following lines need to be added

    // strtokIndx = strtok(NULL, ", "); This reads the string, from where it was previously cut, up until the next comma
    // newVariableName = atoi(strtokIndx); atoi is 'to integer'. If newVariable is a float, atof is needed etc


}