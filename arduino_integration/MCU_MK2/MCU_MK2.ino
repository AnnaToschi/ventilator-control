#include <Adafruit_MCP4725.h> // https://github.com/adafruit/Adafruit_MCP4725 Adafruit MCP4725 12-bit DAC Driver Library
#include <PID_v1.h>			  // https://github.com/br3ttb/Arduino-PID-Library/ Arduino PID Library v1.2.1 by Brett Beauregard
//#include <avr/wdt.h>			 // AVR Watchdog Timer
#include <EEPROM.h>
//Pressure Sensor includes
#include <Adafruit_BMP3XX.h>
#include <Regexp.h>

#define SEALEVELPRESSURE_HPA (1013.25)

Adafruit_BMP3XX pressureSensor;

Adafruit_MCP4725 dac;

//PID - Define the aggressive and conservative Tuning Parameters
double aggKp=4, aggKi=0.2, aggKd=1;
double consKp=1, consKi=0.05, consKd=0.25;

//initialize the two strings being received from the controller
String intendedChangeValue;
int intendedChange;

// a string to hold incoming data
String stringFromUILayer = "";
String stringFromSlaveMCU = "";
boolean stringFromUILayerComplete = false;
boolean stringFromSlaveMCUComplete = false;
int currentState;
boolean isLedOn = false;
boolean isInspirationValveOpen = false;
boolean expirationValveIsOpen = false;

double pidControlledInspiratoryAperture;
double targetInspPressure = 0.00; 
double targetInspTidalVolume = 0.00;


const int expiratoryValvePin = 2;
const byte O2SensorPin = A0;

const float MIN_TARGET_INSP_FLOW = 0.00;		 //Litres per minute
const float MAX_TARGET_INSP_FLOW = 200.00;	  //Litres per minute
const float MIN_TARGET_INSP_PRESSURE = 0.00;	//cmH2O
const float MAX_TARGET_INSP_PRESSURE = 100.00; // cmH2O (0.1 Bar)
const float MIN_TARGET_INSP_VOLUME = 0.00;	  //ml
const float MAX_TARGET_INSP_VOLUME = 1500.00;  //ml

const int INSPIRATION_APERTURE_TARGET = 255;

const int MIN_INSP_VALVE_APERTURE = 0; // 0V - Hoerbiger / Bronkhorst
//const int MAX_INSP_VALVE_APERTURE = 820; // 1V - Hoerbiger
const int MAX_INSP_VALVE_APERTURE = 4095; // 5V - Bronkhorst

const int MIN_TARGET_APERTURE = 0;
const int MAX_TARGET_APERTURE = 255;


// target state byte, as delivered by UILayer controller
const int expirationHold = 0;
const int inspiration = 1;
const int expiration = 2;
const int inspirationHold = 3;

// message type
const int sensorReadings = 1;
const int inspiratorySummary = 2;
const int expiratorySummary = 3;
const int PCSettings = 4;
const int VCSettings = 5;
const int alarmThresholds = 6;
const int alarmMessage = 7;
const int debugMessage = 99;

// ventilator supported modes
const int pressureControl = 0;
const int volumeControl = 1;

int currentVentilatorMode = pressureControl;

const String messageSeparator = ";";

double tidalVolume = 0.00;
float measuredInspirationVolume = 0.00;
float measuredExpirationVolume = 0.00;

float tidalVolumeUpperLimit = 1000.0;
bool inspirationValveIsOpen = false;

const boolean isDebugEnabled = true;
int cyclePhase = inspiration;

String debugString = "";
String alarmString = "";

// Hard-coded Variables
float targetPIP = 46.00; //cmH2O (PIP)
float targetPEEP = 5.00; //cmH2O (PEEP)

float targetIERatio = 2.0;
float targetInspPausePerc = 30.0;
int targetRR = 10; // 5s breaths
int inspirationPhaseDuration = (int) (60000 / targetRR / (1.0 + targetIERatio));
int inspirationHoldPhaseDuration = inspirationPhaseDuration * (targetInspPausePerc/100.0);
int inspirationPhaseMinusHoldDuration = inspirationPhaseDuration - inspirationHoldPhaseDuration;
int expirationPhaseDuration = (60000 / targetRR) - inspirationPhaseDuration;
// int inspirationPhaseDuration = 60000 / targetRR * 0.5; //25% of each Breath Cycle
// int inspirationHoldPhaseDuration = 60000 / targetRR * 0.00; //5% of each Breath Cycle
// int expirationPhaseDuration = (60000 / targetRR) - (inspirationHoldPhaseDuration + inspirationPhaseDuration); //remainder of each Breath Cycle
// int inspirationPhaseMinusHoldDuration = 0;

int message_id = 0;

double pressure = 0.00;
float flow;

const int numO2readings = 100;	//number of smoothing points for the O2 readout
float O2readings[numO2readings]; // the readings from the analog input
int O2readIndex = 0;				 // the index of the current reading
float O2total = 0.00;				// the running total
float O2average = 0.00;			 // the average
int O2RawPercentage = 0;
float O2Percentage = 0.00;


const int numPressureReadings = 5;	//number of smoothing points for the O2 readout
float pressureReadings[numPressureReadings]; // the readings from the analog input
int pressureReadIndex = 0;				 // the index of the current reading
float pressureTotal = 0.00;				// the running total
float pressureAverage = 0.00;			 // the average
//int pressurePercentage = 0;
//float pressurePercentage = 0.00;

unsigned long currentMillis = 0;
unsigned long previousFlowReadMillis = 0;
unsigned long previousPressureReadMillis = 0;
unsigned long previousO2ReadMillis = 0;
unsigned long previousImmediateSensorOutputMillis = 0;
unsigned long previousControlCycleMillis = 0;
unsigned long inspirationPhaseStartMillis = 0;
unsigned long previousSettingsUpdateMillis = 0;

unsigned long inspirationHoldPhaseStartMillis = 0;
unsigned long expirationPhaseStartMillis = 0;
float measuredInspirationRiseTimeInSecs = 0.0;

const int O2Offset = 28;
const float pressureOffsetMultiplier = 0.85;
float pressureOffset = 0.0;
const float flowOffsetMultiplier = 1.0;

const int immediateSensorOutputInterval = 50;
const int O2UpdateInterval = 100;
const int flowUpdateInterval = 50;
const int volumeUpdateInterval = 50;
const int pressureUpdateInterval = 10;
const int controlCycleInterval = 10;
const int settingsUpdateInterval = 3000;

float measuredRR = 0.0;
float measuredPIP = 0.0;
float measuredPEEP = 0.0;
float measuredPIF = 0.0;
float measuredPEF = 0.0;

float targetInspirationRiseTime = 0.8;
float targetVt = 500.0;

float lowerInspirationVolumeThreshold = 0.0;
float upperInspirationVolumeThreshold = 800.0;
float lowerInspirationPressureThreshold = 3.0;
float upperInspirationPressureThreshold = 80.0;

bool PIPReached = false;
bool PEEPReached = false;
bool targetVtReached = false;
bool isInspirationStart=true;
MatchState ms;

//float tidalVolume = 0.00;

bool pressureCalibrationDone = false;
int eeBaseAddress= 0;


//Specify the links and initial tuning parameters for the pressure PID
PID pressurePID( &pressure,  &pidControlledInspiratoryAperture, &targetInspPressure, consKp, consKi, consKd, DIRECT);
PID volumePID(&tidalVolume, &pidControlledInspiratoryAperture, &targetInspTidalVolume, consKp, consKi, consKd, DIRECT);

void setup()
{

  Serial.begin(115200); // Initialize Serial interface towards UILayer controller
  Serial1.begin(115200);  // Initialize Serial interface towards Slave MCU reading Flow Sensor
  
  pressurePID.SetMode(AUTOMATIC);
  volumePID.SetMode(AUTOMATIC);

  stringFromUILayer.reserve(200);
  stringFromSlaveMCU.reserve(200);
  debugString.reserve(200);
  alarmString.reserve(200);

  pinMode(expiratoryValvePin, OUTPUT);
  dac.begin(0x60);

 // wdt_enable(WDTO_500MS); //watchdog timer with 500ms time out
  
  unsigned status;
  status = pressureSensor.begin(0x76);
  if (!status)
  {
  	Serial.println("Could not find a valid BMP388 (inspiration) sensor, check wiring, address, sensor ID!");
  }

  pinMode(O2SensorPin, INPUT);

  //initialize the pressure and O2 sensor smoothing array
  for (int thisReading = 0; thisReading < numPressureReadings; thisReading++)
  {
	 pressureReadings[thisReading] = 0.0; // reset O2readings array
	}

	for (int thisReading = 0; thisReading < numO2readings; thisReading++)
	{
	 O2readings[thisReading] = 0; // reset O2readings array
	}
	readSettingsFromEEPROM();
}

void loop()
{
  //wdt_reset();
  currentMillis = millis(); // capture the latest value of millis()
  
  getO2perc();
  //getInspirationFlow(); // Flow is received through Slave MCU
  getPressure();
  if (stringFromSlaveMCUComplete)
  {
  	interpretSlaveMCUReading();
  }
  if (stringFromUILayerComplete)
  {
  	interpretUILayerCommand();
  }
  switch(currentVentilatorMode){
  	case pressureControl:
  	pressureControlCycle();
  	break;
  	case volumeControl:
  	volumeControlCycle();
  	break;
  }
  settingsSync();
  
  outputMessage(sensorReadings);
}

void handleInspiratoryValveAperture(int targetInspiratoryAperture)
{
	debugString = "HandleInspiratoryValveAperture, changing aperture to : ";
	debugString += targetInspiratoryAperture;

	outputMessage(debugMessage);
	if(targetInspiratoryAperture == MIN_TARGET_APERTURE){
		inspirationValveIsOpen=false;
	}else {
		inspirationValveIsOpen=true;
	}
	dac.setVoltage(map(targetInspiratoryAperture, MIN_TARGET_APERTURE, MAX_TARGET_APERTURE, MIN_INSP_VALVE_APERTURE, MAX_INSP_VALVE_APERTURE), false);
}

void handleExpiratoryValveAperture(int targetExpiratoryAperture)
{
	debugString = "HandleExpiratoryValveAperture, changing aperture to : ";
	debugString += targetExpiratoryAperture;
	outputMessage(debugMessage);
	if (targetExpiratoryAperture == MIN_TARGET_APERTURE && expirationValveIsOpen)
	{
		digitalWrite(expiratoryValvePin, LOW);
		expirationValveIsOpen = false;
	}
	else if (targetExpiratoryAperture > MIN_TARGET_APERTURE && !expirationValveIsOpen)
	{
		digitalWrite(expiratoryValvePin, HIGH);
		expirationValveIsOpen = true;
	}
}

void sendAlarm(String alarmStringAux){
	alarmString=alarmStringAux;
	outputMessage(alarmMessage);

}

void getPressure(){
	if (currentMillis - previousPressureReadMillis >= pressureUpdateInterval) {
		if (!pressureCalibrationDone){
			delay(2000);
			pressure = (pressureSensor.readPressure() / 100.0 * 1.019744288922 );
			debugString = ("1st pressure reading (calibration): ");
			debugString += pressure;
			outputMessage(debugMessage);
			delay(2000);
			debugString = ("2nd pressure reading (calibration): ");
			debugString += pressure;
			outputMessage(debugMessage);
			pressure = (pressureSensor.readPressure() / 100.0 * 1.019744288922 );
			delay(2000);
			pressure = (pressureSensor.readPressure() / 100.0 * 1.019744288922 );
			debugString = ("3rd pressure reading (calibration): ");
			debugString += pressure;
			outputMessage(debugMessage);
			debugString = "Setting baseline pressure offset (this means that the circuit should be at room pressure at this point), pressureOffset being set to ";
			debugString += pressure;
			outputMessage(debugMessage);

			pressureOffset= pressure;
			pressureCalibrationDone = true;               
		}
	 pressure = ((pressureSensor.readPressure() / 100.0 * 1.019744288922 ) - pressureOffset) / pressureOffsetMultiplier;  //CmH2O, two readings for weird stability issues
	 //pressure = ((pressureSensor.readPressure() / 100.0 * 1.019744288922 ) - pressureOffset) / pressureOffsetMultiplier; 
	 //Serial.print("pressure reading is: ");
	 //Serial.println(pressure);

	 pressureTotal = pressureTotal - pressureReadings[pressureReadIndex];
	 pressureReadings[pressureReadIndex] = pressure;
	 // add the reading to the total:
	 pressureTotal = pressureTotal + pressureReadings[pressureReadIndex];
	 // advance to the next position in the array:
	 pressureReadIndex++;

	 // if we're at the end of the array...
	 if (pressureReadIndex >= numPressureReadings)
	 {
		// ...wrap around to the beginning:
	 	pressureReadIndex = 0;
	 }
	 // calculate the average:
	 pressureAverage = pressureTotal / (float)numPressureReadings;

	 switch (cyclePhase){
	 	case inspiration:
	 	if (pressure > measuredPIP){
	 		measuredPIP = pressure;
	 	}
	 	break;
	 	case inspirationHold:
	 	if (pressure > measuredPIP){
	 		measuredPIP = pressure;
	 	}
	 	break;
	 	case expiration:
	 	if (pressureAverage < measuredPEEP){
	 		measuredPEEP = pressureAverage;
	 	}
	 }
	 
	 previousPressureReadMillis = currentMillis;
	}
}

void settingsSync(){
	if (currentMillis - previousSettingsUpdateMillis >= settingsUpdateInterval)
	{
		outputMessage(VCSettings);
		outputMessage(PCSettings);
		outputMessage(alarmThresholds);
		previousSettingsUpdateMillis = currentMillis;
	}


}
void getO2perc()
{
	if (currentMillis - previousO2ReadMillis >= O2UpdateInterval)
	{
		O2total = O2total - O2readings[O2readIndex];
	 // read from the sensor:
		O2RawPercentage = analogRead(O2SensorPin);
		O2Percentage = map(O2RawPercentage, 806, 740, 0, 10000) / 100.00;
		O2readings[O2readIndex] = O2Percentage;
	 // add the reading to the total:
		O2total = O2total + O2readings[O2readIndex];
	 // advance to the next position in the array:
		O2readIndex++;

	 // if we're at the end of the array...
		if (O2readIndex >= numO2readings)
		{
		// ...wrap around to the beginning:
			O2readIndex = 0;
		}
	 // calculate the average:
		O2Percentage = O2total / (float)numO2readings + O2Offset;
	 // send it to the computer as ASCII digits
		previousO2ReadMillis = currentMillis;
	}
}

void iterateMessageId(){
	if (message_id >= 999)
	{
		message_id = 0;
	}
	else
	{
		message_id++;
	}
}


void writeSettingsToEEPROM(){
	debugString = "Saving settings in MCUs EEPROM";

	outputMessage(debugMessage);
	int eeAddress = eeBaseAddress;
	EEPROM.put(eeAddress, targetPEEP);
	eeAddress += sizeof(float);
	EEPROM.put(eeAddress, targetPIP);
	eeAddress += sizeof(float);
	EEPROM.put(eeAddress, targetRR);
	eeAddress += sizeof(float);
	EEPROM.put(eeAddress, targetIERatio);
	eeAddress += sizeof(float);
	EEPROM.put(eeAddress, targetInspirationRiseTime);
	eeAddress += sizeof(float);
	EEPROM.put(eeAddress, targetVt);
	eeAddress += sizeof(float);
	EEPROM.put(eeAddress, targetInspPausePerc);
	eeAddress += sizeof(float);
	EEPROM.put(eeAddress, lowerInspirationVolumeThreshold);
	eeAddress += sizeof(float);
	EEPROM.put(eeAddress, upperInspirationVolumeThreshold);
	eeAddress += sizeof(float);
	EEPROM.put(eeAddress, lowerInspirationPressureThreshold);
	eeAddress += sizeof(float);
	EEPROM.put(eeAddress, upperInspirationPressureThreshold);
	eeAddress += sizeof(float);
	EEPROM.put(eeAddress, currentVentilatorMode);
}


void readSettingsFromEEPROM(){
	debugString = "Reading saved settings from MCUs EEPROM and sending to UI Layer";

	outputMessage(debugMessage);
	int eeAddress = eeBaseAddress;
	EEPROM.get(eeAddress, targetPEEP);
	if (isnan(targetPEEP)){
		targetPEEP=5.0;
	}
	eeAddress += sizeof(float);

	EEPROM.get(eeAddress, targetPIP);
	if (isnan(targetPIP)){
		targetPIP=50.0;
	}
	eeAddress += sizeof(float);

	EEPROM.get(eeAddress, targetRR);
	if (isnan(targetRR)||targetRR<0){
		targetRR=10.0;
	}
	eeAddress += sizeof(float);

	EEPROM.get(eeAddress, targetIERatio);
	if (isnan(targetIERatio)){
		targetIERatio=2.0;
	}
	eeAddress += sizeof(float);
	EEPROM.get(eeAddress, targetInspirationRiseTime);
	if (isnan(targetInspirationRiseTime)){
		targetInspirationRiseTime=0.8;
	}
	eeAddress += sizeof(float);
	EEPROM.get(eeAddress, targetVt);
	if (isnan(targetVt)){
		targetVt=0.8;
	}
	eeAddress += sizeof(float);
	EEPROM.get(eeAddress, targetInspPausePerc);
	if (isnan(targetInspPausePerc)){
		targetInspPausePerc=30.0;
	}
	eeAddress += sizeof(float);
	EEPROM.get(eeAddress, lowerInspirationVolumeThreshold);
	if (isnan(lowerInspirationVolumeThreshold)){
		lowerInspirationVolumeThreshold=50.0;
	}
	eeAddress += sizeof(float);
	EEPROM.get(eeAddress, upperInspirationVolumeThreshold);
	if (isnan(upperInspirationVolumeThreshold)){
		upperInspirationVolumeThreshold=1500.0;
	}
	eeAddress += sizeof(float);
	EEPROM.get(eeAddress, lowerInspirationPressureThreshold);
	if (isnan(lowerInspirationPressureThreshold)){
		lowerInspirationPressureThreshold=10.0;
	}
	eeAddress += sizeof(float);
	EEPROM.get(eeAddress, upperInspirationPressureThreshold);
	if (isnan(upperInspirationPressureThreshold)){
		upperInspirationPressureThreshold=70.0;
	}
	eeAddress += sizeof(float);
	EEPROM.get(eeAddress, currentVentilatorMode);
	if (currentVentilatorMode!=pressureControl || currentVentilatorMode!=volumeControl){
		currentVentilatorMode=pressureControl;
	}
	inspirationPhaseDuration = (int) (60000 / targetRR / (1.0 + targetIERatio)); 
	expirationPhaseDuration = (60000 / targetRR) - inspirationPhaseDuration;
	inspirationHoldPhaseDuration = inspirationPhaseDuration * (targetInspPausePerc/100.0);
	inspirationPhaseMinusHoldDuration = inspirationPhaseDuration - inspirationHoldPhaseDuration;
	expirationPhaseDuration = (60000 / targetRR) - inspirationPhaseDuration;

	outputMessage(VCSettings);
	outputMessage(PCSettings);
	outputMessage(alarmThresholds);
}



void outputMessage(int messageType){

	

	switch (messageType){

		case sensorReadings:
		if (currentMillis - previousImmediateSensorOutputMillis >= immediateSensorOutputInterval)
		{
			Serial.print(sensorReadings);
			Serial.print(messageSeparator);
				Serial.print(message_id); //messageId
				Serial.print(messageSeparator);
				Serial.print(pressure); //immediatePressure
				Serial.print(messageSeparator);
				Serial.print(flow); //immediateFlow
				Serial.print(messageSeparator);
				Serial.println(tidalVolume); //immediateTidalVolume
				previousImmediateSensorOutputMillis = currentMillis;
				iterateMessageId();
			}
			break;

			case inspiratorySummary:
		 		//2;messageId;measuredInspirationRiseTimeInSecs;measuredPIP;measuredInspirationVolume;measuredPIF;O2Percentage //inspiratory summary, sent at the end of the inspiratory phase
			Serial.print(inspiratorySummary);
			Serial.print(messageSeparator);
			Serial.print(message_id); //messageId
			Serial.print(messageSeparator);
			Serial.print(measuredInspirationRiseTimeInSecs); //measuredInspirationRiseTimeInSecs
			Serial.print(messageSeparator);
			Serial.print(measuredPIP); //measuredPIP
			Serial.print(messageSeparator);
			Serial.print(measuredInspirationVolume); //measuredInspirationVolume
			Serial.print(messageSeparator);
			Serial.print(measuredPIF); //measuredPIF
			Serial.print(messageSeparator);
			Serial.println(O2Percentage); //O2Percentage
			iterateMessageId();
			break;

			case expiratorySummary:
		 		//3;messageId;measuredPEEP;measuredExpirationVolume;measuredPEF;O2% //expiratory summary, sent at the end of the expiratory phase
			Serial.print(expiratorySummary);
			Serial.print(messageSeparator);
			Serial.print(message_id); //messageId
			Serial.print(messageSeparator);
			Serial.print(measuredPEEP); //measuredPEEP
			Serial.print(messageSeparator);
			Serial.print(measuredExpirationVolume); //measuredExpirationVolume
			Serial.print(messageSeparator);
			Serial.print(measuredPEF); //measuredPEF
			Serial.print(messageSeparator);
			Serial.print(O2Percentage); //O2Percentage
			Serial.print(messageSeparator);
			Serial.println(measuredRR);
			iterateMessageId();
			break;

			case PCSettings:
		 		//4;messageId;targetPEEP;targetPIP;targetRR;targetI/ERatio;targetInspirationRiseTime //current PC settings, sent once every X (default 10) seconds, and immediately after a settings change
			Serial.print(PCSettings);
			Serial.print(messageSeparator);
			Serial.print(message_id); //messageId
			Serial.print(messageSeparator);
			Serial.print(targetPEEP); //targetPEEP
			Serial.print(messageSeparator);
			Serial.print(targetPIP); //targetPIP
			Serial.print(messageSeparator);
			Serial.print(targetRR); //targetRR
			Serial.print(messageSeparator);
			Serial.print(targetIERatio); //targetIERatio
			Serial.print(messageSeparator);
			Serial.println(targetInspirationRiseTime); //targetInspirationRiseTime
			iterateMessageId();
			break;

			case VCSettings:
		 		//5;messageId;targetPEEP;targetVt;targetRR;targetI/ERatio;targetInspPausePerc //current VC settings, sent once every X (default 10) seconds, and immediately after a settings change
			Serial.print(VCSettings);
			Serial.print(messageSeparator);
			Serial.print(message_id); //messageId
			Serial.print(messageSeparator);
			Serial.print(targetPEEP); //targetPEEP
			Serial.print(messageSeparator);
			Serial.print(targetVt); //targetPIP
			Serial.print(messageSeparator);
			Serial.print(targetRR); //targetRR
			Serial.print(messageSeparator);
			Serial.print(targetIERatio); //targetIERatio
			Serial.print(messageSeparator);
			Serial.println(targetInspPausePerc); //targetInspPausePerc
			iterateMessageId();
			break;

			case alarmThresholds:
		 		//6;messageId;lowerInspirationVolumeThreshold;upperInspirationVolumeThreshold;lowerInspirationPressureThreshold;upperInspirationPressureThreshold //current alarm settings, sent once every X (default 10) seconds, and immediately after a alarm threshold settings change
			Serial.print(alarmThresholds);
			Serial.print(messageSeparator);
			Serial.print(message_id); //messageId
			Serial.print(messageSeparator);
			Serial.print(lowerInspirationVolumeThreshold); //lowerInspirationVolumeThreshold
			Serial.print(messageSeparator);
			Serial.print(upperInspirationVolumeThreshold); //upperInspirationVolumeThreshold
			Serial.print(messageSeparator);
			Serial.print(lowerInspirationPressureThreshold); //lowerInspirationPressureThreshold
			Serial.print(messageSeparator);
			Serial.println(upperInspirationPressureThreshold); //upperInspirationPressureThreshold
			iterateMessageId();
			break;

			case alarmMessage:
			
				//7;messageId;alarmString //alarm message
			Serial.print(alarmMessage);
			Serial.print(messageSeparator);
			Serial.print(message_id);
			Serial.print(messageSeparator);
			Serial.println(alarmString);
			iterateMessageId();
			break;

			case debugMessage:
			if (isDebugEnabled){
				//99;messageId;debugString //to be used for debug purposes only, either displayed in the python console or some text box in the QT dashboard
				Serial.print(debugMessage);
				Serial.print(messageSeparator);
				Serial.print(message_id);
				Serial.print(messageSeparator);
				Serial.println(debugString);
				iterateMessageId();
				break;
			}
		}

	}

	void pressureControlCycle(){
		if (currentMillis - previousControlCycleMillis >= controlCycleInterval) {
			switch (cyclePhase) {
				case inspiration:
				debugString = "Pressure Contol - Inspiration Phase, pressure = ";
				debugString += pressure;
				debugString += " , flow = ";
				debugString += flow;
				debugString += " , measuredInspirationVolume = ";
				debugString += measuredInspirationVolume;
				debugString += " , pidControlledInspiratoryAperture = ";
				debugString += pidControlledInspiratoryAperture;
				outputMessage(debugMessage);


				if (isInspirationStart) {
					int targetAperture=INSPIRATION_APERTURE_TARGET *0.5;
					pidControlledInspiratoryAperture = (double) targetAperture;
					
					handleInspiratoryValveAperture(targetAperture);

					inspirationPhaseStartMillis=currentMillis;
					isInspirationStart=false;
					debugString = "Inspiration Cycle start, inspiration Valve is Open";
					outputMessage(debugMessage);
				}
				else{
					debugString = "Inspiration Valve is Open";
					outputMessage(debugMessage);
					if (PIPReached && pressure < (targetPIP *0.95)) {
						targetAperture = targetAperture + (targetAperture*0.1);
						handleInspiratoryValveAperture(targetAperture);
						
					}
					if ((pressure >= (targetPIP*0.8))&& !PIPReached){
						if(!PIPReached){
							measuredInspirationRiseTimeInSecs = (millis() - inspirationPhaseStartMillis) / 1000.0;
							PIPReached=true;
						}
						debugString = "closing inspiration valve due to measuredPIP = ";
						debugString += measuredPIP;
						debugString += " ,targetPIP = ";
						debugString += targetPIP;



						outputMessage(debugMessage);
						targetAperture = targetAperture - (targetAperture*0.2);
						handleInspiratoryValveAperture(targetAperture);
						
					}
					
					if (PIPReached && pressure > (targetPIP *1.1)) {
						handleInspiratoryValveAperture(MIN_TARGET_APERTURE);
						targetAperture = targetAperture - (targetAperture*0.1);
						handleInspiratoryValveAperture(targetAperture);
					}

					


					if (tidalVolume > tidalVolumeUpperLimit){ // Volume Upper Threshold reached?


						debugString = "Volume upper threshold reached: ";
						debugString += tidalVolume;
						debugString += " switching to expiration phase";
						outputMessage(debugMessage);

						//inspirationVolumeThresholdAlarm();
						handleExpiratoryValveAperture(MAX_TARGET_APERTURE);
						handleInspiratoryValveAperture(MIN_TARGET_APERTURE); // close inspiration valve
						cyclePhase = expiration; // switch to expiration
						outputMessage(inspiratorySummary);
						expirationPhaseStartMillis=millis();
						break;
					}
					if (currentMillis - inspirationPhaseStartMillis > inspirationPhaseDuration){ // Inspiration Time Upper Limit reached?
							//inspirationTimerThresholdAlarm();
						debugString = "Reached Inspiration Timer: ";
						debugString += inspirationPhaseDuration;
						debugString += " switching to expiration phase";
						outputMessage(debugMessage);
						
						handleExpiratoryValveAperture(MAX_TARGET_APERTURE);
						handleInspiratoryValveAperture(MIN_TARGET_APERTURE);
						cyclePhase = expiration;
						outputMessage(inspiratorySummary);
						expirationPhaseStartMillis=millis();
						break;
					}

				 	// if none of the exit conditions apply, lets continue applying pressure PID

					double pressureGap = abs(targetPIP-pressure); //distance away from setpoint
					/*if (pressureGap < 10.0)
						{  //we're close to setpoint, use conservative tuning parameters
					pressurePID.SetTunings(consKp, consKi, consKd);
					}
					else   //we're far from setpoint, use aggressive tuning parameters
					{*/

					pressurePID.SetTunings(aggKp, aggKi, aggKd);
					//}

					/*pressurePID.Compute();
					if (PIPReached){
						handleInspiratoryValveAperture((int) pidControlledInspiratoryAperture);
					}*/
					
         //handleInspiratoryValveAperture(INSPIRATION_APERTURE_TARGET);
				}

				break;

			case inspirationHold: // this state is not part of pressure control, staying here just for the good memories of when we thought it would make sense :)

				 if (currentMillis - inspirationPhaseStartMillis > inspirationPhaseDuration){ // Inspiration hold duration reached?
				 	debugString = "Inspiration hold phase duration reached";
				 	outputMessage(debugMessage);

				 	handleExpiratoryValveAperture(MAX_TARGET_APERTURE);
				 	cyclePhase = expiration;
				 	expirationPhaseStartMillis=currentMillis;
				 }
				 break;

				 case expiration:
				 debugString = "Expiration Phase, pressure = ";
				 debugString += pressure;
				 debugString += " , flow = ";
				 debugString += flow;
				 debugString += " , measuredExpirationVolume = ";
				 debugString += measuredExpirationVolume;
				 outputMessage(debugMessage);
				 if (PEEPReached && pressure < targetPEEP){
				 	handleInspiratoryValveAperture(MAX_TARGET_APERTURE);
				 }
				 
				 if (PEEPReached && pressure >= (targetPEEP - 1.0)){
				 	handleInspiratoryValveAperture(MIN_TARGET_APERTURE);
				 }

				 if (pressureAverage < targetPEEP){
				 	debugString = "PEEP Reached: ";
				 	debugString += pressureAverage;
				 	outputMessage(debugMessage);
				 	PEEPReached=true;

				 	handleExpiratoryValveAperture(MIN_TARGET_APERTURE);
							//handleInspiratoryValveAperture(INSPIRATION_APERTURE_TARGET);
							//cyclePhase = inspiration;
							//tidalVolume=0.0;
							//inspirationPhaseStartMillis=currentMillis;
				 }
					  if (currentMillis - expirationPhaseStartMillis > expirationPhaseDuration){ // Expiration Time Upper Limit reached?
					  	debugString = "Expiration phase duration reached";
					  	outputMessage(debugMessage);
					  	handleExpiratoryValveAperture(MIN_TARGET_APERTURE);
					  	handleInspiratoryValveAperture(INSPIRATION_APERTURE_TARGET);
					  	pidControlledInspiratoryAperture = (double) INSPIRATION_APERTURE_TARGET;
					  	cyclePhase = inspiration;
					  	measuredRR= 60000 / (millis() - inspirationPhaseStartMillis);
					  	outputMessage(expiratorySummary);
					  	tidalVolume=0.0;

					  	measuredPIP=0.0;
					  	PEEPReached=false;
					  	measuredInspirationVolume=0.0;
					  	measuredExpirationVolume=0.0;
					  	measuredPIF=0.0;
					  	measuredPEF=0.0;
					  	measuredInspirationRiseTimeInSecs=0;
					  	measuredPEEP=999.0; //insanely high value
					  	PIPReached=false;

					  	inspirationPhaseStartMillis=currentMillis;
					  }
					  break;
					}
					previousControlCycleMillis = currentMillis;
				}

			}



			void volumeControlCycle(){
				if (currentMillis - previousControlCycleMillis >= controlCycleInterval) {
					switch (cyclePhase) {
						case inspiration:
						debugString = "Volume Contol - Inspiration Phase, pressure = ";
						debugString += pressure;
						debugString += " , flow = ";
						debugString += flow;
						debugString += " , measuredInspirationVolume = ";
						debugString += measuredInspirationVolume;
						debugString += " , pidControlledInspiratoryAperture = ";
						debugString += pidControlledInspiratoryAperture;
						outputMessage(debugMessage);


						if (isInspirationStart) {
							handleInspiratoryValveAperture(INSPIRATION_APERTURE_TARGET);
							pidControlledInspiratoryAperture = (double) INSPIRATION_APERTURE_TARGET;
							inspirationPhaseStartMillis=currentMillis;
							isInspirationStart=false;
							debugString = "Inspiration Cycle start, inspiration Valve is Open";
							outputMessage(debugMessage);
						}
						else{


							if (measuredInspirationVolume >=targetVt && !targetVtReached){

								debugString = "Reached targetVt, switching to inspiration hold phase ";

								outputMessage(debugMessage);

								measuredInspirationRiseTimeInSecs = (millis() - inspirationPhaseStartMillis) / 1000.0;
								targetVtReached=true;

							handleInspiratoryValveAperture(MIN_TARGET_APERTURE); // close inspiration valve
							cyclePhase = inspirationHold; // switch to expiration
							inspirationHoldPhaseStartMillis=millis();
							break;
						}

						if (measuredPIP > upperInspirationPressureThreshold){ // Pressure Upper Threshold reached?

							debugString = "Pressure upper threshold reached: ";
							debugString += measuredPIP;
							outputMessage(debugMessage);

							sendAlarm(debugString);
							return;
						}
						if (currentMillis - inspirationPhaseStartMillis > inspirationPhaseMinusHoldDuration){ // Inspiration Time minus Hold Upper Limit reached?
								//inspirationTimerThresholdAlarm();
							debugString = "Vt not reached within inspiration time";

							outputMessage(debugMessage);

							sendAlarm(debugString);

							handleInspiratoryValveAperture(MIN_TARGET_APERTURE);
							cyclePhase = inspirationHold;
							//outputMessage(inspiratorySummary);
							inspirationHoldPhaseStartMillis=millis();
							return;
						}

					 	// if none of the exit conditions apply, lets continue applying volume PID

						double volumeGap = abs(targetVt-tidalVolume); //distance away from setpoint
						if (volumeGap < 100.0)
							{  //we're close to setpoint, use conservative tuning parameters
						volumePID.SetTunings(consKp, consKi, consKd);
					}
						else   //we're far from setpoint, use aggressive tuning parameters
						{
							volumePID.SetTunings(aggKp, aggKi, aggKd);
						}

						volumePID.Compute();
						//handleInspiratoryValveAperture((int) pidControlledInspiratoryAperture);
						//handleInspiratoryValveAperture(INSPIRATION_APERTURE_TARGET);
					}

					

					break;

					case inspirationHold: 

					if (measuredInspirationVolume < lowerInspirationVolumeThreshold){
						debugString = "Inspiration Volume lower than threshold";
						outputMessage(debugMessage);
						sendAlarm(debugString);

					}

					 if (currentMillis - inspirationHoldPhaseStartMillis > inspirationHoldPhaseDuration){ // Inspiration hold duration reached?
					 	debugString = "Inspiration hold phase duration reached, its set at ";
					 	debugString += inspirationHoldPhaseDuration;
					 	debugString += " ms";
					 	outputMessage(debugMessage);

					 	if (measuredPIP < lowerInspirationPressureThreshold){
					 		debugString = "Inspiration low pressure alarm (possible leak)";
					 		outputMessage(debugMessage);
					 		sendAlarm(debugString);
					 	}
					 	outputMessage(inspiratorySummary);
					 	handleExpiratoryValveAperture(MAX_TARGET_APERTURE);
					 	cyclePhase = expiration;
					 	expirationPhaseStartMillis=currentMillis;
					 }
					 break;

					 case expiration:
					 debugString = "Expiration Phase, pressure = ";
					 debugString += pressure;
					 debugString += " , flow = ";
					 debugString += flow;
					 debugString += " , measuredExpirationVolume = ";
					 debugString += measuredExpirationVolume;
					 outputMessage(debugMessage);

					 if (pressureAverage < targetPEEP){
					 	debugString = "PEEP Reached: ";
					 	debugString += pressureAverage;
					 	outputMessage(debugMessage);

					 	handleExpiratoryValveAperture(MIN_TARGET_APERTURE);
							//handleInspiratoryValveAperture(INSPIRATION_APERTURE_TARGET);
							//cyclePhase = inspiration;
							//tidalVolume=0.0;
							//inspirationPhaseStartMillis=currentMillis;
					 }
					  if (currentMillis - expirationPhaseStartMillis > expirationPhaseDuration){ // Expiration Time Upper Limit reached?
					  	debugString = "Expiration phase duration reached";
					  	outputMessage(debugMessage);
					  	sendAlarm(debugString);
					  	handleExpiratoryValveAperture(MIN_TARGET_APERTURE);
					  	handleInspiratoryValveAperture(INSPIRATION_APERTURE_TARGET);
					  	pidControlledInspiratoryAperture = (double) INSPIRATION_APERTURE_TARGET;
					  	cyclePhase = inspiration;
					  	measuredRR = 60000 / (millis() - inspirationPhaseStartMillis);
					  	outputMessage(expiratorySummary);
					  	tidalVolume=0.0;

					  	measuredPIP=0.0;

					  	measuredInspirationVolume=0.0;
					  	measuredExpirationVolume=0.0;
					  	measuredPIF=0.0;
					  	measuredPEF=0.0;
					  	measuredInspirationRiseTimeInSecs=0;
					  	measuredPEEP=999.0; //insanely high value
					  	targetVtReached=false;

					  	inspirationPhaseStartMillis=currentMillis;
					  }
					  break;
					}
					previousControlCycleMillis = currentMillis;
				}

			}

			void interpretSlaveMCUReading()
			{

				unsigned long currentMCUReadMillis = millis();
				flow = stringFromSlaveMCU.toFloat() / flowOffsetMultiplier;
				tidalVolume = tidalVolume + (flow * (currentMCUReadMillis - previousFlowReadMillis) / 60);
				if (tidalVolume < 0.0){
					tidalVolume = 0.0;
				}
				switch (cyclePhase) {
					case expiration:
					measuredExpirationVolume = measuredExpirationVolume + abs(flow * (currentMCUReadMillis - previousFlowReadMillis) / 60);
					if (abs(flow) > measuredPEF  ){
						measuredPEF = abs(flow);
					}
					break;

					case inspiration:
					measuredInspirationVolume = abs(measuredInspirationVolume + (flow * (currentMCUReadMillis - previousFlowReadMillis) / 60));
					if (flow > measuredPIF  ){
						measuredPIF = flow;
					}
					break;
				}

				previousFlowReadMillis = currentMCUReadMillis;

				stringFromSlaveMCU = "";
				stringFromSlaveMCUComplete = false;
			}

			void interpretUILayerCommand()
			{
				if (stringFromUILayerComplete)
				{
          //Serial.println(stringFromUILayer);
					char copy[50];
					
					debugString = "MCU received the following message from Rpi: ";
					debugString += stringFromUILayer;
					outputMessage(debugMessage);
					stringFromUILayer.toCharArray(copy, 50);
					char *tok = strtok(copy, ";");
					int i = 1;

					int intendedMessageType = atoi(tok);
					//debugString = "intendedMessageType: ";
					//debugString += intendedMessageType;
					//outputMessage(debugMessage);
					switch (intendedMessageType){
						case PCSettings:
//DEBUG:root:error in received data: b'99;token=4\r\n'
//DEBUG:root:error in received data: b'99;token=1\r\n'
//DEBUG:root:error in received data: b'99;token=5\r\n'
//DEBUG:root:error in received data: b'99;token=113\r\n'
//DEBUG:root:error in received data: b'99;token=10.0\r\n'
//DEBUG:root:error in received data: b'99;token=2.0\r\n'
//DEBUG:root:error in received data: b'99;token=1.0\r\n'

				//4;messageId;targetPEEP;targetPIP;targetRR;targetIERatio;targetInspirationRiseTime //current PC settings, sent once every X (default 10) seconds, and immediately after a settings change
						while (tok) {
							tok = strtok(NULL, ";");
							
							if(i == 2){
								targetPEEP=atof(tok);
							}
							else if(i==3){
								targetPIP=atof(tok);
							}
							else if(i==4){
								targetRR=atof(tok);
							}
							else if(i==5){
								targetIERatio=atof(tok);
							}
							else if(i==6){
								targetInspirationRiseTime=atof(tok);
							}
							i++;
					    	// Note: NULL, not IncomingString
						}
						currentVentilatorMode = pressureControl;
						targetInspPressure= (double)targetPIP;
						inspirationPhaseDuration = (int) (60000 / targetRR / (1.0 + targetIERatio)); 
						expirationPhaseDuration = (60000 / targetRR) - inspirationPhaseDuration; //remainder of each Breath Cycle
						writeSettingsToEEPROM();
						outputMessage(PCSettings);
						break;

						case VCSettings:
				//5;messageId;targetPEEP;targetVt;targetRR;targetIERatio;targetInspPausePerc //current VC settings, sent once every X (default 10) seconds, and immediately after a settings change
						while (tok) {
							tok = strtok(NULL, ";");
							
							if(i == 2){
								targetPEEP=atof(tok);
							}
							else if(i==3){
								targetVt=atof(tok);
							}
							else if(i==4){
								targetRR=atof(tok);
							}
							else if(i==5){
								targetIERatio=atof(tok);
							}
							else if(i==6){
								targetInspPausePerc=atof(tok);
							}
							i++;
					    	// Note: NULL, not IncomingString
						}
						currentVentilatorMode = volumeControl;

						inspirationPhaseDuration = (int) (60000 / targetRR / (1.0 + targetIERatio));
						inspirationHoldPhaseDuration = inspirationPhaseDuration * (targetInspPausePerc/100.0);
						inspirationPhaseMinusHoldDuration = inspirationPhaseDuration - inspirationHoldPhaseDuration;
						expirationPhaseDuration = (60000 / targetRR) - inspirationPhaseDuration;
						writeSettingsToEEPROM();
						outputMessage(VCSettings);
						break;

						case alarmThresholds:
			    //6;messageId;lowerInspirationVolumeThreshold;upperInspirationVolumeThreshold;lowerInspirationPressureThreshold;upperInspirationPressureThreshold //current alarm settings, sent once every X (default 10) seconds, and immediately after a alarm threshold settings change
						while (tok) {
							tok = strtok(NULL, ";");
							
							if(i == 2){
								lowerInspirationVolumeThreshold=atof(tok);
							}
							else if(i==3){
								upperInspirationVolumeThreshold=atof(tok);
							}
							else if(i==4){
								lowerInspirationPressureThreshold=atof(tok);
							}
							else if(i==5){
								upperInspirationPressureThreshold=atof(tok);
							}
							i++;
					    	// Note: NULL, not IncomingString
						}
						writeSettingsToEEPROM();
						outputMessage(alarmThresholds);
						break;

					}

				}
				stringFromUILayer = "";
				stringFromUILayerComplete = false;
			}



			void serialEvent()
			{
				while (Serial.available())
				{

	 			// get the new byte:
					char inChar = (char)Serial.read();
	 			// add it to the inputString:
					if (inChar == '\n')
					{
						stringFromUILayerComplete = true;
					}else{
						stringFromUILayer += inChar;
					}
				 // if the incoming character is a newline, set a flag
				 // so other function spaces can do something about it:
				}
			}

			void serialEvent1()
			{
				while (Serial1.available())
				{

	 			// get the new byte:
					char inChar = (char)Serial1.read();
	 			// add it to the inputString:
					stringFromSlaveMCU += inChar;
	 			// if the incoming character is a newline, set a flag
	 			// so other function spaces can do something about it:
					if (inChar == '\n')
					{
						stringFromSlaveMCUComplete = true;
					}
				}
			}
