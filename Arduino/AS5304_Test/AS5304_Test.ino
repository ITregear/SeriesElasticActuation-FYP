#include <Encoder.h>

Encoder AS5304(2, 3);

void setup() {
  Serial.begin(115200);
}

long posEnc  = -999;
float sensitivity = 0.03255;

void loop() {
  long newEnc;
  newEnc = AS5304.read();

  if (newEnc != posEnc) {
    posEnc = newEnc;
  }

  Serial.print(newEnc * sensitivity);
  Serial.println();

}
