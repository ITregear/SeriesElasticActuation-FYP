#include "AS5311.h"

AS5311 myAS5311(2,3,4,5); // data, clock, chip select, index

double count = 0;
double enc_pos = 0;
double enc_pos_last = 0;
double coeff = 0.0008044484;
double angle = 0;


void setup()
{
  Serial.begin(115200);
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

  Serial.println(angle, 4);
  
}