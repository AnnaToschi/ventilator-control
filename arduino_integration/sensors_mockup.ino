
#include <Wire.h>


const int serialUpdateInterval = 50;

int message_id = 0;
float O2_percentage;
float inspiratory_pressure;
float inspiratory_flow;
float expiratory_pressure;
float expiratory_flow;
float tidal_volume;
float combined_flow;

float reserved1;

unsigned long currentMillis = 0;
unsigned long previousSerialWriteMillis = 0;


void setup(){

  Serial.begin(115200);
}

void loop(){
  currentMillis = millis();   // capture the latest value of millis()                        
  writeSerial();
}


void writeSerial(){
  if (currentMillis - previousSerialWriteMillis >= serialUpdateInterval) {
    if (message_id >= 999){
      message_id=0;
     }
    else {
      message_id++;
     }

  O2_percentage=random(0,10000)/100.0;
  inspiratory_pressure=random(0,100000)/100.0;
  inspiratory_flow=random(0,12000)/100.0;
  expiratory_pressure=random(0,100000)/100.0;
  expiratory_flow=random(0,12000)/100.0;
  tidal_volume=random(0,140000)/100.0;
  combined_flow=inspiratory_flow-expiratory_flow;
  reserved1 = 0.00;
  
  Serial.print(message_id);
  Serial.print(";");
  Serial.print(O2_percentage);
  Serial.print(";");
  Serial.print(inspiratory_pressure);
  Serial.print(";");
  Serial.print(inspiratory_flow);
  Serial.print(";");
  Serial.print(expiratory_pressure);
  Serial.print(";");
  Serial.print(expiratory_flow);
  Serial.print(";");
  Serial.print(tidal_volume);
  Serial.print(";");
  Serial.print(combined_flow);
  Serial.print(";");
  Serial.println(reserved1);
  
  previousSerialWriteMillis=currentMillis;
  }
}
