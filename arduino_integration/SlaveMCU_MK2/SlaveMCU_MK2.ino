#include <avr/wdt.h>          // AVR Watchdog Timer
//Flow Meter includes
#include <sfm3000wedo.h>

SFM3000wedo measFlow(64);

unsigned int flowOffset = 32768; // Offset for the SFM3300 sensor 

float flowScale = 120.0; // Scale factor for SFM3300

float flow;
const int serialUpdateInterval = 50;
const int flowUpdateInterval = 50;

unsigned long currentMillis = 0;
unsigned long previousInspirationFlowReadMillis = 0;
unsigned long previousSerialWriteMillis = 0;
int sensorConsecutiveErrorReadCount = 0;

const int MAX_CONSECUTIVE_SENSOR_READ_ERROR_COUNT = 5;

const float MAX_FLOW_SENSOR_READING=200.0;
const float MIN_FLOW_SENSOR_READING=-200.0;

void setup() {
  Serial.begin(9600); // initialize the serial interface towards the Master MCU
  wdt_enable(WDTO_500MS); //watchdog timer with 500ms time out
  measFlow.init(); // initialize the Inspiration Flow Sensor
}

void loop() {
  wdt_reset();
  currentMillis = millis();   // capture the latest value of millis()
  getInspirationFlow(); // read from flow sensor
  writeSerial(); // write flow reading towards Master MCU
}

void(* resetMCU) (void) = 0; //declare reset function @ address 0

void getInspirationFlow(){
  if (currentMillis - previousInspirationFlowReadMillis >= flowUpdateInterval) {

    unsigned int flowResult = measFlow.getvalue();

    flow = ((float)flowResult - flowOffset) / flowScale;
    if (flow > MAX_FLOW_SENSOR_READING || flow < MIN_FLOW_SENSOR_READING){
        if (sensorConsecutiveErrorReadCount == MAX_CONSECUTIVE_SENSOR_READ_ERROR_COUNT){
            resetMCU();
        }
        else {
            sensorConsecutiveErrorReadCount++;
        }
    }
    previousInspirationFlowReadMillis=currentMillis;
  }
}

void writeSerial(){
  if (currentMillis - previousSerialWriteMillis >= serialUpdateInterval) {
      Serial.println(flow);
  
  previousSerialWriteMillis=currentMillis;
  }
}
