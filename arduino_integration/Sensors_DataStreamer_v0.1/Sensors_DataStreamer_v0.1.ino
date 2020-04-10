

#include <SPI.h>
#include <Wire.h>

//Pressure Sensor includes
#include <Adafruit_Sensor.h>
#include <Adafruit_BMP3XX.h>

//Flow Meter includes
#include <sfm3000wedo.h>

#define SEALEVELPRESSURE_HPA (1013.25)

Adafruit_BMP3XX inspirationPressureSensor;

SFM3000wedo measInspFlow(64);
#include "Plotter.h"
Plotter p;
double x;


unsigned int flowOffset = 32768; // Offset for the SFM3300 sensor 

float flowScale = 120.0; // Scale factor for SFM3300

const byte inspirationO2SensorPin = A0;

const int numO2readings = 100;                   //number of smoothing points for the O2 readout
float inspirationO2readings[numO2readings];      // the readings from the analog input
int   inspirationO2readIndex = 0;              // the index of the current reading
float inspirationO2total = 0.00;                  // the running total
float inspirationO2average = 0.00;                // the average
int   message_id = 0;

float inspiratoryO2percentage;
float inspiratoryPressure = 0.00;
float inspiratoryFlow;

const int O2Offset = 28;
float inspiratoryPressureOffset;


const int serialUpdateInterval = 50;
const int inspirationO2UpdateInterval = 100;
const int inspirationFlowUpdateInterval = 50;
const int InspirationVolumeUpdateInterval = 50;
const int inspirationPressureUpdateInterval = 50;

unsigned long currentMillis = 0;
unsigned long previousInspirationFlowReadMillis = 0;
unsigned long previousInspirationPressureReadMillis = 0;
unsigned long previousO2ReadMillis = 0;
unsigned long previousSerialWriteMillis = 0;


int inspiration_O2_raw_perc=0;
float inspiratoryO2Percentage=0.00;

float inspiratoryVolume = 0.00;

bool enableGraphs = false;

void setup() {
  Wire.begin();

 if (enableGraphs){
     p.Begin();
     Serial.begin(115200);
     p.AddTimeGraph( "Inspiratory Pressure", 1000, "", inspiratoryPressure );
     p.AddTimeGraph( "Inspiratory O2%", 1000, "", inspiratoryO2Percentage );
     p.AddTimeGraph( "Inspiratory Flow", 1000, "", inspiratoryFlow );
     p.AddTimeGraph( "Inspiratory Volume", 1000, "", inspiratoryVolume );
  }
  else {
    Serial.flush ();   // wait for send buffer to empty
    delay (2);    // let last character be sent
    Serial.end ();
    Serial.begin(115200);
  }
  
  unsigned status;
  status = inspirationPressureSensor.begin();
  if (!status) {
        Serial.println("Could not find a valid BMP388 (inspiration) sensor, check wiring, address, sensor ID!");
  }
  
  // initialize the Inspiration Flow Sensor
  measInspFlow.init();

  pinMode(inspirationO2SensorPin, INPUT);
 
 //initialize the O2 sensor smoothing array
 for (int thisReading = 0; thisReading < numO2readings; thisReading++) {
    inspirationO2readings[thisReading] = 0; // reset O2readings array
  }
 
}
int i = 0;
void loop() {
  currentMillis = millis();   // capture the latest value of millis()
 
  if (i==0){
    getInspirationPressure();
    delay(3000);
    Serial.print("Setting baseline pressure offset (this means that the circuit should be at room pressure at this point), pressure = ");
    Serial.println(inspiratoryPressure);
    inspiratoryPressureOffset= inspiratoryPressure;
    i++;                       
  }
  getInspirationO2perc();
  getInspirationFlow();
  getInspirationPressure();

  
  if  (enableGraphs){
    p.Plot();
  }
  else{
    writeSerial();
  }
  
  
}



void getInspirationFlow(){
  if (currentMillis - previousInspirationFlowReadMillis >= inspirationFlowUpdateInterval) {
    //inspiratoryFlow = ((float) measInspFlow.getvalue() - flowOffset) / flowScale;

    unsigned int flowResult = measInspFlow.getvalue();

    inspiratoryFlow = ((float)flowResult - flowOffset) / flowScale;
    inspiratoryVolume = inspiratoryVolume + (inspiratoryFlow * (currentMillis - previousInspirationFlowReadMillis)/60);
    
    previousInspirationFlowReadMillis=currentMillis;
  }
}

void getInspirationPressure(){
  if (currentMillis - previousInspirationPressureReadMillis >= inspirationPressureUpdateInterval) {
    //Serial.print("Sensor reading is: ");
    //Serial.println(inspirationPressureSensor.readPressure() / 100.0 * 1.019744288922);
    //Serial.print("pressure offset is: ");
    //Serial.println(inspiratoryPressureOffset);
    inspiratoryPressure = (inspirationPressureSensor.readPressure() / 100.0 * 1.019744288922 ) - inspiratoryPressureOffset ; //CmH2O
    inspiratoryPressure =  (inspirationPressureSensor.readPressure() / 100.0 * 1.019744288922) - inspiratoryPressureOffset ;
    previousInspirationPressureReadMillis = currentMillis;
  }
}


void getInspirationO2perc(){
  if (currentMillis - previousO2ReadMillis >= inspirationO2UpdateInterval) {
    inspirationO2total = inspirationO2total - inspirationO2readings[inspirationO2readIndex];
    // read from the sensor: 
    inspiration_O2_raw_perc = analogRead(inspirationO2SensorPin);
    inspiratoryO2Percentage=map(inspiration_O2_raw_perc, 806, 740, 0, 10000)/100.00;
    inspirationO2readings[inspirationO2readIndex] = inspiratoryO2Percentage;
    // add the reading to the total:
    inspirationO2total = inspirationO2total + inspirationO2readings[inspirationO2readIndex];
    // advance to the next position in the array:
    inspirationO2readIndex++;
  
    // if we're at the end of the array...
    if (inspirationO2readIndex >= numO2readings) {
      // ...wrap around to the beginning:
      inspirationO2readIndex = 0;
    }
    // calculate the average:
    inspiratoryO2Percentage = inspirationO2total / (float) numO2readings + O2Offset;
    // send it to the computer as ASCII digits
    previousO2ReadMillis=currentMillis;
  }
}

void writeSerial(){
  if (currentMillis - previousSerialWriteMillis >= serialUpdateInterval) {
    if (message_id >= 999){
      message_id=0;
     }
    else {
      message_id++;
    }
      Serial.print(message_id);
      Serial.print(";");
      Serial.print(inspiratoryO2Percentage);
      Serial.print(";");
      Serial.print(inspiratoryPressure/2.00);
      Serial.print(";");
      Serial.print(inspiratoryFlow/2.00);
      Serial.print(";");
      Serial.println(inspiratoryVolume/2.00);
  
  previousSerialWriteMillis=currentMillis;
  }
}
