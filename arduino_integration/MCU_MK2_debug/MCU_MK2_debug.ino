#include <Adafruit_MCP4725.h> // https://github.com/adafruit/Adafruit_MCP4725 Adafruit MCP4725 12-bit DAC Driver Library
//#include <PID_v1.h>           // https://github.com/br3ttb/Arduino-PID-Library/ Arduino PID Library v1.2.1 by Brett Beauregard
//#include <avr/wdt.h>          // AVR Watchdog Timer

//Pressure Sensor includes
#include <Adafruit_BMP3XX.h>

#define SEALEVELPRESSURE_HPA (1013.25)

Adafruit_BMP3XX pressureSensor;

Adafruit_MCP4725 dac;

//initialize the two strings being received from the controller
String intendedChangeValue;
int intendedChange;

// a string to hold incoming data
String stringFromEPICs = "";
String stringFromSlaveMCU = "";
boolean stringFromEPICsComplete = false;
boolean stringFromSlaveMCUComplete = false;
int currentState;
boolean isLedOn = false;
boolean isInspirationValveOpen = false;
boolean isExpirationValveOpen = false;

const int expiratoryValvePin = 2;
const byte O2SensorPin = A0;

const float MIN_TARGET_INSP_FLOW = 0.00;       //Litres per minute
const float MAX_TARGET_INSP_FLOW = 200.00;     //Litres per minute
const float MIN_TARGET_INSP_PRESSURE = 0.00;   //cmH2O
const float MAX_TARGET_INSP_PRESSURE = 300.00; // cmH2O (0.3 Bar)
const float MIN_TARGET_INSP_VOLUME = 0.00;     //ml
const float MAX_TARGET_INSP_VOLUME = 1000.00;  //ml

const int INSPIRATION_APERTURE_TARGET = 80;

const int MIN_INSP_VALVE_APERTURE = 350; // 0V - Hoerbiger / Bronkhorst
//const int MAX_INSP_VALVE_APERTURE = 820; // 1V - Hoerbiger
const int MAX_INSP_VALVE_APERTURE = 4095; // 5V - Bronkhorst

const int MIN_TARGET_APERTURE = 0;
const int MAX_TARGET_APERTURE = 255;

// target command byte, as delivered by EPICs controller
const int targetInspFlow = 0;
const int targetInspPressure = 1;
const int targetInspValveAperture = 2;
const int targetExpValveAperture = 3;
const int targetState = 4;

// target state byte, as delivered by EPICs controller
const int expirationHold = 0;
const int inspiration = 1;
const int expiration = 2;
const int inspirationHold = 3;


float inspiratoryVolume = 0.00;
float expiratoryVolume = 0.00;
float tidalVolume = 0.00;

float tidalVolumeUpperLimit = 0.6;
bool inspirationValveIsOpen;
bool expirationValveIsOpen;

int cyclePhase = inspiration;

// Hard-coded Variables
float peakInspirationPressure = 1200.00; //hPa (PIP)
float positiveEndExpiratoryPressure = 1100.00; //hpa (PEEP)

int breathsPerMinute = 12; // 5s breaths
int inspirationPhaseDuration = 60000 / breathsPerMinute * 0.25; //25% of each Breath Cycle
int inspirationHoldPhaseDuration = 60000 / breathsPerMinute * 0.05; //5% of each Breath Cycle
int expirationPhaseDuration = (60000 / breathsPerMinute) - (inspirationHoldPhaseDuration + inspirationPhaseDuration); //remainder of each Breath Cycle


int message_id = 0;

float pressure = 0.00;
float flow;

const int numO2readings = 100;   //number of smoothing points for the O2 readout
float O2readings[numO2readings]; // the readings from the analog input
int O2readIndex = 0;             // the index of the current reading
float O2total = 0.00;            // the running total
float O2average = 0.00;          // the average
int O2RawPercentage = 0;
float O2Percentage = 0.00;

unsigned long currentMillis = 0;
unsigned long previousFlowReadMillis = 0;
unsigned long previousPressureReadMillis = 0;
unsigned long previousO2ReadMillis = 0;
unsigned long previousSerialWriteMillis = 0;
unsigned long previousControlCycleMillis = 0;
unsigned long inspirationPhaseStartMillis = 0;

unsigned long inspirationHoldPhaseStartMillis = 0;
unsigned long expirationPhaseStartMillis = 0;

const int O2Offset = 28;
const float pressureOffsetMultiplier = 2.7;
float pressureOffset = 0.0;
const float flowOffsetMultiplier = 2.0;

const int serialUpdateInterval = 50;
const int O2UpdateInterval = 100;
const int flowUpdateInterval = 50;
const int volumeUpdateInterval = 50;
const int pressureUpdateInterval = 50;
const int controlCycleInterval = 10;


//float tidalVolume = 0.00;

// realistic mockup data for graphs
//float flow[] = {0, 13.009, 25.037, 28.738, 31.956, 33.654, 34.567, 35.022, 35.212, 35.242, 35.183, 35.079, 34.95, 34.81, 34.668, 35.69, 35.477, 35.183, 34.949, 34.744, 34.554, 8.0112, -12.002, -20.371, -23.919, -25.319, -25.638, -25.362, -24.699, -23.885, -23, -22.049, -21.102, -20.147, -19.188, -18.23, -17.277, -16.341, -15.427, -14.546, -13.709, -12.913, -12.16, -11.448, -10.778, -10.148, -9.5569, -9.0041, -8.4873, -8.0048, -7.5546, -7.1346, -6.7429, -6.3777, -6.0368, -5.7189, -5.422, -5.1449, -4.8858, -4.6437, -4.4172, -4.2052, -4.0065, -3.8204, -3.6458, -3.4818, -3.3278, -3.183, -3.0468, -2.9186, -2.7977, -2.6838, -2.5763, -2.4748, -2.3787, -2.2877, -2.2015, -2.1197, -2.0419, -1.9681, -1.8975, 6.9948, 17.004, 18.669, 20.214, 20.979, 21.365, 21.845, 22.896, 24.205, 25.484, 26.632, 27.622, 28.458, 29.155, 29.727, 30.191, 30.571, 30.881, 31.133, 31.339, 7.127, -10.194, -17.708, -21.042, -22.449, -22.824, -22.587, -21.98, -21.203, -20.316, -19.39, -18.435, -17.475, -16.524, -15.596, -14.703, -13.846, -13.038, -12.275, -11.553, -10.875, -10.236, -9.6373, -9.0771, -8.5538, -8.0653, -7.6098, -7.185, -6.789, -6.4197, -6.0754, -5.754, -5.4542, -5.1744, -4.913, -4.6685, -4.4399, -4.2259, -4.0255, -3.8377, -3.6616, -3.4962, -3.3409, -3.1949, -3.0576, -2.9282, -2.8064, -2.6915, -2.5831, -2.4806, -2.3836, -2.2917, -2.2046, -2.1218, -2.0433, -1.9687, -1.8977, -1.8301, -1.7658, -1.7042, 6.929, 16.961, 18.579, 20.139, 20.863, 21.265, 21.725, 22.653, 23.923, 25.192, 26.333, 27.326, 28.165, 28.864, 29.448, 29.93, 30.325, 30.649, 30.913, 31.132, 7.3089, -9.8614, -17.245, -20.577, -21.943, -22.345, -22.115, -21.516, -20.734, -19.855, -18.923, -17.97, -17.017, -16.076, -15.164, -14.288, -13.456, -12.668, -11.924, -11.224, -10.563, -9.9435, -9.3633, -8.821, -8.3146, -7.8422, -7.4016, -6.9908, -6.6079, -6.2508, -5.9177, -5.6069, -5.3169, -5.0461, -4.7929, -4.5562, -4.3348, -4.1274, -3.9332, -3.7511, -3.5802, -3.4198, -3.269, -3.1272, -2.9938, -2.8681, -2.7497, -2.638, -2.5325, -2.4327, -2.3381, -2.2485, -2.1635, -2.0828, -2.0062, -1.9333, -1.8639, -1.7979, -1.735, -1.6747, 6.9013, 16.945, 18.554, 20.108, 20.843, 21.25, 21.704, 22.611, 23.881, 25.146, 26.281, 27.274, 28.115, 28.821, 29.405, 29.89, 30.286, 30.612, 30.877, 31.1, 7.3177, -9.5395, -17.171, -20.488, -21.906, -22.279, -22.049, -21.445, -20.668, -19.785, -18.851, -17.901, -16.947, -16.008, -15.095, -14.221, -13.395, -12.612, -11.87, -11.173, -10.515, -9.8986, -9.3211, -8.7815, -8.2776, -7.8077, -7.3698, -6.9613, -6.5801, -6.2228, -5.8916, -5.5834, -5.2943, -5.025, -4.7734, -4.5383, -4.318, -4.1118, -3.9185, -3.7373, -3.5673, -3.4076, -3.2576, -3.1165, -2.9837, -2.8587, -2.7407, -2.6295, -2.5245, -2.4251, -2.3309, -2.2417, -2.157, -2.0767, -2.0003, -1.9277, -1.8585, -1.7928, -1.7301, -1.6703, 6.9099, 16.938, 18.547, 20.102, 20.836, 21.245, 21.7, 22.605, 23.871, 25.136, 26.27, 27.263, 28.104, 28.811, 29.396, 29.88, 30.277, 30.604, 30.87, 31.093, 7.3374, -9.6585, -17.167, -20.484, -21.876, -22.263, -22.037, -21.432, -20.656, -19.772, -18.84, -17.888, -16.935, -15.995, -15.083, -14.21, -13.383, -12.602, -11.864, -11.165, -10.508, -9.8919, -9.315, -8.7758, -8.2725, -7.8028, -7.3649, -6.9566, -6.5759, -6.221, -5.8899, -5.5809, -5.2926, -5.0234, -4.7717, -4.5364, -4.3162, -4.11, -3.9169, -3.7358, -3.5658, -3.4062, -3.2563, -3.1152, -2.9825, -2.8575, -2.7397, -2.6285, -2.5235, -2.4241, -2.33, -2.2408, -2.1562, -2.0759, -1.9995, -1.9269, -1.8578, -1.7921, -1.7294, -1.6694, 6.9101, 16.937, 18.546, 20.101, 20.836, 21.244, 21.698, 22.603, 23.869, 25.134, 26.269, 27.261, 28.103, 28.81, 29.394, 29.879, 30.276, 30.603, 30.869, 31.092, 7.3385, -9.6223, -17.163, -20.479, -21.888, -22.256, -22.035, -21.432, -20.654, -19.769, -18.837, -17.886, -16.933, -15.993, -15.081, -14.214, -13.386, -12.603, -11.862, -11.163, -10.506, -9.8899, -9.3131, -8.774, -8.2708, -7.8012, -7.3634, -6.9552, -6.5747, -6.2198, -5.8888, -5.5799, -5.2917, -5.0224, -4.7708, -4.5356, -4.3154, -4.1093, -3.9162, -3.7351, -3.5652, -3.4057, -3.2557, -3.1147, -2.9821, -2.8572, -2.7393, -2.6282, -2.5231, -2.4238, -2.3297, -2.2405, -2.1559, -2.0756, -1.9992, -1.9267, -1.8576, -1.7919, -1.7292, -1.6692, 6.91, 16.937, 18.546, 20.101, 20.835, 21.244, 21.698, 22.603, 23.869, 25.134, 26.268, 27.261, 28.102, 28.809, 29.394, 29.879, 30.275, 30.602, 30.868, 31.092, 7.3386, -9.6331, -17.143, -20.474, -21.861, -22.24, -22.03, -21.434, -20.651, -19.768, -18.836, -17.884, -16.932, -15.993, -15.08, -14.21, -13.384, -12.601, -11.859, -11.159, -10.506, -9.8899, -9.3132, -8.7741, -8.2708, -7.8013, -7.3635, -6.9553, -6.5747, -6.2198, -5.8889, -5.58, -5.2918, -5.0224, -4.7708, -4.5357, -4.3155, -4.1094, -3.9163, -3.7352, -3.5653, -3.4057, -3.2558, -3.1148, -2.9821, -2.8571, -2.7393, -2.6281, -2.5231, -2.4238, -2.3297, -2.2405, -2.1559, -2.0756, -1.9993, -1.9267, -1.8576, -1.7919, -1.7292, -1.6693, 6.91, 16.937, 18.546, 20.101, 20.835, 21.244, 21.698, 22.603, 23.869, 25.134, 26.268, 27.261, 28.102, 28.809, 29.394, 29.879, 30.275, 30.602, 30.868, 31.092, 7.3387, -9.5957, -17.145, -20.475, -21.861, -22.24, -22.03, -21.433, -20.651, -19.768, -18.835, -17.885, -16.931, -15.993, -15.08, -14.21, -13.384, -12.6, -11.858, -11.158};
//float pressure[] = {0, 0.40961, 1.0912, 1.4903, 1.9085, 2.281, 2.626, 2.9543, 3.272, 3.5822, 3.8872, 4.1884, 4.4864, 4.7818, 5.0751, 5.412, 5.7117, 6.0009, 6.2898, 6.5774, 6.8634, 6.2285, 5.4722, 5.0297, 4.7197, 4.4669, 4.2461, 4.0459, 3.8637, 3.693, 3.5311, 3.3794, 3.236, 3.0998, 2.9708, 2.8511, 2.7376, 2.6322, 2.5331, 2.4405, 2.3539, 2.272, 2.1951, 2.1227, 2.0546, 1.9904, 1.9299, 1.8728, 1.8188, 1.7678, 1.7194, 1.6736, 1.6302, 1.589, 1.5498, 1.5125, 1.4771, 1.4433, 1.4111, 1.3803, 1.351, 1.3229, 1.2961, 1.2704, 1.2459, 1.2223, 1.1997, 1.178, 1.1572, 1.1371, 1.1179, 1.0993, 1.0815, 1.0643, 1.0477, 1.0317, 1.0163, 1.0014, 0.98706, 0.97318, 0.95972, 1.2139, 1.703, 1.9059, 2.1214, 2.3195, 2.5085, 2.7025, 2.9217, 3.1599, 3.4103, 3.6659, 3.925, 4.1864, 4.4493, 4.7132, 4.9777, 5.2425, 5.5076, 5.7728, 6.0381, 5.469, 4.8258, 4.4373, 4.1583, 3.9295, 3.7302, 3.5517, 3.3897, 3.2391, 3.1002, 2.9683, 2.846, 2.7322, 2.625, 2.5252, 2.4323, 2.344, 2.2615, 2.1842, 2.1113, 2.0429, 1.9783, 1.9173, 1.8598, 1.8055, 1.7542, 1.7055, 1.6595, 1.6158, 1.5743, 1.5349, 1.4975, 1.4618, 1.4279, 1.3955, 1.3647, 1.3352, 1.307, 1.2801, 1.2543, 1.2297, 1.206, 1.1834, 1.1616, 1.1407, 1.1206, 1.1013, 1.0828, 1.0649, 1.0477, 1.0311, 1.0151, 0.99968, 0.98481, 0.97045, 0.95659, 0.9432, 0.93026, 0.91775, 0.90561, 1.152, 1.6408, 1.841, 2.0547, 2.2497, 2.437, 2.6286, 2.8401, 3.074, 3.319, 3.5704, 3.8255, 4.083, 4.3423, 4.6028, 4.8641, 5.126, 5.3883, 5.6509, 5.9138, 5.3568, 4.7254, 4.3451, 4.0701, 3.8464, 3.6502, 3.4752, 3.3166, 3.1702, 3.0338, 2.9069, 2.7883, 2.6776, 2.5742, 2.4779, 2.3872, 2.302, 2.2218, 2.1466, 2.076, 2.0093, 1.9465, 1.8873, 1.8313, 1.7785, 1.7284, 1.6811, 1.6362, 1.5936, 1.5531, 1.5147, 1.4782, 1.4433, 1.4102, 1.3785, 1.3484, 1.3195, 1.292, 1.2656, 1.2404, 1.2162, 1.1931, 1.1709, 1.1495, 1.129, 1.1093, 1.0904, 1.0722, 1.0546, 1.0377, 1.0214, 1.0057, 0.99058, 0.97597, 0.96186, 0.94824, 0.93507, 0.92235, 0.91005, 0.8981, 1.1428, 1.6316, 1.8312, 2.0442, 2.2391, 2.4261, 2.6171, 2.8271, 3.0607, 3.3051, 3.5556, 3.8099, 4.0668, 4.3254, 4.5853, 4.8461, 5.1074, 5.3692, 5.6314, 5.8938, 5.3385, 4.7184, 4.3312, 4.0571, 3.8325, 3.6376, 3.4633, 3.3055, 3.1592, 3.0237, 2.8981, 2.7794, 2.6692, 2.5662, 2.4701, 2.3798, 2.2951, 2.2158, 2.1406, 2.0704, 2.004, 1.9415, 1.8825, 1.8268, 1.7742, 1.7244, 1.6772, 1.6325, 1.5901, 1.5496, 1.5113, 1.475, 1.4402, 1.4072, 1.3757, 1.3457, 1.317, 1.2895, 1.2633, 1.2381, 1.214, 1.1909, 1.1688, 1.1475, 1.1271, 1.1075, 1.0886, 1.0704, 1.0529, 1.0361, 1.0198, 1.0042, 0.98906, 0.97449, 0.96042, 0.94683, 0.9337, 0.92101, 0.90874, 0.89687, 1.1416, 1.63, 1.8294, 2.0424, 2.2371, 2.4242, 2.615, 2.8249, 3.0582, 3.3025, 3.5529, 3.807, 4.0638, 4.3223, 4.582, 4.8427, 5.104, 5.3657, 5.6277, 5.8901, 5.3352, 4.7126, 4.3285, 4.0545, 3.8307, 3.6356, 3.4612, 3.3036, 3.1573, 3.022, 2.8959, 2.7782, 2.6676, 2.5648, 2.4687, 2.3786, 2.2939, 2.2146, 2.14, 2.0695, 2.0032, 1.9407, 1.8818, 1.8261, 1.7735, 1.7237, 1.6766, 1.6319, 1.5895, 1.5492, 1.5109, 1.4745, 1.4399, 1.4068, 1.3753, 1.3453, 1.3166, 1.2891, 1.2629, 1.2377, 1.2137, 1.1906, 1.1684, 1.1472, 1.1268, 1.1072, 1.0883, 1.0701, 1.0526, 1.0358, 1.0195, 1.0039, 0.98879, 0.97422, 0.96016, 0.94657, 0.93345, 0.92077, 0.9085, 0.89659, 1.1413, 1.6296, 1.8291, 2.042, 2.2368, 2.4238, 2.6146, 2.8244, 3.0577, 3.3019, 3.5523, 3.8065, 4.0632, 4.3217, 4.5814, 4.842, 5.1033, 5.365, 5.627, 5.8893, 5.3346, 4.713, 4.328, 4.0541, 3.8298, 3.6353, 3.4608, 3.303, 3.1569, 3.0217, 2.8957, 2.7778, 2.6677, 2.5645, 2.4685, 2.379, 2.2942, 2.2146, 2.1397, 2.0693, 2.003, 1.9405, 1.8815, 1.8259, 1.7733, 1.7235, 1.6764, 1.6317, 1.5893, 1.5491, 1.5108, 1.4744, 1.4397, 1.4067, 1.3752, 1.3452, 1.3165, 1.289, 1.2628, 1.2376, 1.2136, 1.1905, 1.1684, 1.1471, 1.1267, 1.1071, 1.0882, 1.07, 1.0525, 1.0357, 1.0195, 1.0038, 0.98872, 0.97415, 0.96009, 0.94651, 0.93339, 0.92071, 0.90845, 0.89654, 1.1413, 1.6296, 1.829, 2.042, 2.2367, 2.4237, 2.6145, 2.8244, 3.0576, 3.3018, 3.5522, 3.8063, 4.0631, 4.3216, 4.5813, 4.8419, 5.1031, 5.3648, 5.6269, 5.8892, 5.3345, 4.7126, 4.3284, 4.0541, 3.8305, 3.6357, 3.4608, 3.3027, 3.1569, 3.0215, 2.8953, 2.7782, 2.6673, 2.5646, 2.4685, 2.3785, 2.294, 2.2144, 2.1395, 2.0689, 2.003, 1.9405, 1.8816, 1.8259, 1.7733, 1.7235, 1.6764, 1.6317, 1.5893, 1.5491, 1.5108, 1.4744, 1.4397, 1.4067, 1.3752, 1.3452, 1.3165, 1.289, 1.2628, 1.2376, 1.2136, 1.1905, 1.1684, 1.1471, 1.1267, 1.1071, 1.0882, 1.07, 1.0525, 1.0357, 1.0195, 1.0038, 0.98872, 0.97415, 0.96009, 0.94651, 0.93339, 0.92071, 0.90845, 0.89654, 1.1413, 1.6296, 1.829, 2.0419, 2.2367, 2.4237, 2.6145, 2.8244, 3.0576, 3.3018, 3.5522, 3.8063, 4.063, 4.3216, 4.5813, 4.8419, 5.1031, 5.3648, 5.6269, 5.8892, 5.3345, 4.7136, 4.3283, 4.054, 3.8305, 3.6357, 3.4608, 3.3026, 3.1569, 3.0215, 2.8961, 2.7773, 2.6673, 2.5647, 2.4684, 2.3786, 2.294, 2.2142, 2.1393, 2.0688};
//float volume[] = {800, 801.2, 808.08, 817.36, 828.24, 840.08, 852.44, 865, 877.64, 890.24, 902.8, 915.28, 927.64, 939.88, 952.08, 964.28, 976.64, 988.84, 1000.96, 1012.92, 1024.8, 1033.28, 1033.08, 1028, 1020.84, 1012.88, 1004.6, 996.28, 988.12, 980.2, 972.56, 965.2, 958.2, 951.44, 945, 938.92, 933.08, 927.6, 922.4, 917.48, 912.88, 908.52, 904.4, 900.56, 896.92, 893.48, 890.24, 887.2, 884.36, 881.64, 879.08, 876.68, 874.4, 872.28, 870.24, 868.32, 866.48, 864.76, 863.12, 861.56, 860.08, 858.64, 857.32, 856.04, 854.8, 853.64, 852.52, 851.48, 850.44, 849.48, 848.52, 847.64, 846.76, 845.96, 845.16, 844.4, 843.64, 842.96, 842.28, 841.6, 840.96, 841, 845.2, 850.96, 857.32, 864.08, 871.04, 878.12, 885.48, 893.2, 901.4, 910, 918.96, 928.2, 937.72, 947.44, 957.36, 967.4, 977.56, 987.8, 998.12, 1005.44, 1005.16, 1000.8, 994.56, 987.52, 980.16, 972.76, 965.48, 958.44, 951.68, 945.16, 939, 933.12, 927.56, 922.28, 917.36, 912.68, 908.28, 904.12, 900.24, 896.56, 893.12, 889.84, 886.8, 883.92, 881.2, 878.6, 876.2, 873.92, 871.76, 869.68, 867.76, 865.92, 864.2, 862.52, 860.96, 859.48, 858.04, 856.72, 855.4, 854.2, 853, 851.88, 850.84, 849.8, 848.84, 847.88, 847, 846.12, 845.28, 844.48, 843.72, 843, 842.28, 841.6, 840.96, 840.32, 839.72, 839.12, 838.56, 838.6, 842.8, 848.52, 854.84, 861.56, 868.44, 875.48, 882.72, 890.32, 898.36, 906.8, 915.6, 924.72, 934.08, 943.64, 953.4, 963.32, 973.32, 983.44, 993.64, 1000.88, 1000.76, 996.48, 990.4, 983.48, 976.28, 969.04, 961.92, 955.04, 948.4, 942.08, 936.04, 930.32, 924.92, 919.8, 915, 910.44, 906.16, 902.16, 898.36, 894.8, 891.44, 888.28, 885.32, 882.48, 879.84, 877.36, 875, 872.76, 870.68, 868.68, 866.8, 865, 863.28, 861.68, 860.16, 858.72, 857.32, 856, 854.72, 853.52, 852.4, 851.28, 850.24, 849.24, 848.28, 847.36, 846.48, 845.64, 844.84, 844.04, 843.28, 842.56, 841.88, 841.2, 840.56, 839.96, 839.36, 838.76, 838.2, 838.28, 842.44, 848.2, 854.48, 861.16, 868.04, 875.08, 882.28, 889.88, 897.92, 906.32, 915.12, 924.16, 933.52, 943.04, 952.8, 962.68, 972.68, 982.76, 992.96, 1000.16, 1000, 995.8, 989.76, 982.88, 975.72, 968.48, 961.4, 954.52, 947.92, 941.64, 935.6, 929.88, 924.48, 919.4, 914.6, 910.08, 905.84, 901.84, 898.08, 894.52, 891.2, 888.04, 885.08, 882.28, 879.64, 877.16, 874.8, 872.6, 870.48, 868.52, 866.64, 864.84, 863.16, 861.56, 860.04, 858.56, 857.2, 855.88, 854.64, 853.44, 852.28, 851.2, 850.16, 849.16, 848.2, 847.28, 846.4, 845.56, 844.76, 843.96, 843.24, 842.52, 841.8, 841.16, 840.52, 839.88, 839.28, 838.72, 838.16, 838.2, 842.4, 848.12, 854.4, 861.12, 868, 875, 882.24, 889.8, 897.84, 906.24, 915, 924.08, 933.4, 942.96, 952.68, 962.56, 972.56, 982.64, 992.8, 1000, 999.96, 995.72, 989.64, 982.76, 975.6, 968.4, 961.32, 954.44, 947.84, 941.52, 935.52, 929.8, 924.44, 919.32, 914.56, 910.04, 905.8, 901.8, 898.04, 894.48, 891.16, 888, 885.04, 882.24, 879.6, 877.12, 874.76, 872.56, 870.48, 868.48, 866.6, 864.84, 863.12, 861.52, 860, 858.56, 857.16, 855.88, 854.6, 853.4, 852.28, 851.2, 850.16, 849.16, 848.2, 847.28, 846.4, 845.56, 844.72, 843.96, 843.2, 842.48, 841.8, 841.12, 840.48, 839.88, 839.28, 838.72, 838.16, 838.2, 842.4, 848.12, 854.4, 861.08, 867.96, 875, 882.2, 889.8, 897.8, 906.24, 915, 924.04, 933.4, 942.92, 952.64, 962.52, 972.52, 982.6, 992.8, 1000, 999.92, 995.68, 989.6, 982.76, 975.6, 968.36, 961.28, 954.4, 947.8, 941.52, 935.52, 929.8, 924.4, 919.32, 914.56, 910.04, 905.8, 901.8, 898, 894.48, 891.12, 888, 885.04, 882.24, 879.6, 877.12, 874.76, 872.56, 870.44, 868.48, 866.6, 864.8, 863.12, 861.52, 860, 858.56, 857.16, 855.84, 854.6, 853.4, 852.28, 851.16, 850.12, 849.12, 848.2, 847.28, 846.4, 845.56, 844.72, 843.96, 843.2, 842.48, 841.8, 841.12, 840.48, 839.88, 839.28, 838.68, 838.12, 838.2, 842.4, 848.12, 854.4, 861.08, 867.96, 875, 882.2, 889.8, 897.8, 906.24, 915, 924.04, 933.4, 942.92, 952.64, 962.52, 972.52, 982.6, 992.8, 1000, 999.92, 995.68, 989.6, 982.76, 975.56, 968.36, 961.28, 954.4, 947.8, 941.48, 935.52, 929.8, 924.4, 919.32, 914.56, 910.04, 905.8, 901.76, 898, 894.48, 891.12, 888, 885.04, 882.24, 879.6, 877.12, 874.76, 872.56, 870.44, 868.48, 866.6, 864.8, 863.12, 861.52, 860, 858.56, 857.16, 855.84, 854.6, 853.4, 852.28, 851.16, 850.12, 849.12, 848.2, 847.28, 846.4, 845.56, 844.72, 843.96, 843.2, 842.48, 841.8, 841.12, 840.48, 839.88, 839.28, 838.68, 838.12, 838.2, 842.4, 848.12, 854.4, 861.08, 867.96, 875, 882.2, 889.8, 897.8, 906.24, 915, 924.04, 933.36, 942.92, 952.64, 962.52, 972.52, 982.6, 992.76, 1000, 999.88, 995.68, 989.6, 982.76, 975.56, 968.36, 961.28, 954.4, 947.8, 941.52, 935.48, 929.8, 924.4, 919.32, 914.56, 910.04, 905.76, 901.76, 898};

int icycle = 0;
int i = 0;

void setup()
{
 
  Serial.begin(115200); // Initialize Serial interface towards EPICs controller
  Serial1.begin(115200);  // Initialize Serial interface towards Slave MCU reading Flow Sensor

  stringFromEPICs.reserve(200);
  stringFromSlaveMCU.reserve(200);
  
  pinMode(expiratoryValvePin, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT); // For Debug purpose, initialize onboard led for physical feedback

  dac.begin(0x60);

 // wdt_enable(WDTO_500MS); //watchdog timer with 500ms time out

  unsigned status;
  status = pressureSensor.begin(0x76);
  if (!status)
  {
    Serial.println("Could not find a valid BMP388 (inspiration) sensor, check wiring, address, sensor ID!");
  }

  pinMode(O2SensorPin, INPUT);

  //initialize the O2 sensor smoothing array
  for (int thisReading = 0; thisReading < numO2readings; thisReading++)
  {
    O2readings[thisReading] = 0; // reset O2readings array
  }
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
  if (stringFromEPICsComplete)
  {
    interpretEPICsCommand();
  }
  pressureControlCycle();
  writeSerial();
}

void switchOnBoardLEDState()
{
  if (isLedOn)
  {
    digitalWrite(LED_BUILTIN, LOW);
    isLedOn = false;
    return;
  }
  else
  {
    digitalWrite(LED_BUILTIN, HIGH);
    isLedOn = true;
  }
}

void handleflow(float targetflow)
{
  switchOnBoardLEDState();
}

void handlepressure(float targetpressure)
{
  switchOnBoardLEDState();
}

void handleInspiratoryValveAperture(int targetInspiratoryAperture)
{
  dac.setVoltage(map(targetInspiratoryAperture, MIN_TARGET_APERTURE, MAX_TARGET_APERTURE, MIN_INSP_VALVE_APERTURE, MAX_INSP_VALVE_APERTURE), false);
}

void handleExpiratoryValveAperture(int targetInspiratoryAperture)
{
  if (targetInspiratoryAperture == MIN_TARGET_APERTURE && isExpirationValveOpen)
  {
    digitalWrite(expiratoryValvePin, LOW);
    isExpirationValveOpen = false;
  }
  else if (targetInspiratoryAperture > MIN_TARGET_APERTURE && !isExpirationValveOpen)
  {
    digitalWrite(expiratoryValvePin, HIGH);
    isExpirationValveOpen = true;
  }
}

void getPressure(){
  if (currentMillis - previousPressureReadMillis >= pressureUpdateInterval) {
    pressure = ((pressureSensor.readPressure() / 100.0 * 1.019744288922 ) - pressureOffset) / pressureOffsetMultiplier;  //CmH2O, two readings for weird stability issues
    pressure = ((pressureSensor.readPressure() / 100.0 * 1.019744288922 ) - pressureOffset) / pressureOffsetMultiplier; 
    //Serial.print("pressure reading is: ");
    //Serial.println(pressure);
    if (i==0){
      delay(5000);
      pressure = (pressureSensor.readPressure() / 100.0 * 1.019744288922 );
    //Serial.print("Setting baseline pressure offset (this means that the circuit should be at room pressure at this point), pressure = ");
    //Serial.println(pressure);
    Serial.println("O2_Percentage pressure flow tidalVolume");
    pressureOffset= pressure;
    i++;                       
  }
    previousPressureReadMillis = currentMillis;
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

void writeSerial()
{
  if (currentMillis - previousSerialWriteMillis >= serialUpdateInterval)
  {


    //Serial.print(message_id);
    //Serial.print(";");
    Serial.print(O2Percentage);
    Serial.print(" ");
    //Serial.print(";");
    Serial.print(pressure);
     Serial.print(" ");
    Serial.print(flow);
     Serial.print(" ");
    Serial.println(tidalVolume);

    previousSerialWriteMillis = currentMillis;
  }
}


void interpretEPICsCommand()
{
  if (stringFromEPICsComplete)
  {
    //Serial.print("SERIAL ECHO: ");
    //Serial.println(stringFromEPICs)
    for (int i = 0; i < stringFromEPICs.length(); i++)
    {
      if (stringFromEPICs.substring(i, i + 1) == ";")
      {
        intendedChange = stringFromEPICs.substring(0, i).toInt();
        intendedChangeValue = stringFromEPICs.substring(i + 1);
        break;
      }
    }

    switch (intendedChange)
    {
      float intendedChangeValueAuxFloat;
      int intendedChangeValueAuxInt;
    case targetInspFlow: // define target Inspiration Flow in lpm, to be handled through the microcontroller/arduino PID controller.
      intendedChangeValueAuxFloat = intendedChangeValue.toFloat();
      constrain(intendedChangeValueAuxFloat, MIN_TARGET_INSP_FLOW, MAX_TARGET_INSP_FLOW); //sanitize/limit target inspiratory flow.
      handleflow(intendedChangeValueAuxFloat);
      break;

    case targetInspPressure: // define target Inspiration Pressure in cmH2O, to be handled through the microcontroller/arduino PID controller.
      intendedChangeValueAuxFloat = intendedChangeValue.toFloat();
      constrain(intendedChangeValueAuxFloat, MIN_TARGET_INSP_PRESSURE, MAX_TARGET_INSP_PRESSURE); //sanitize/limit target inspiratory pressure.
      handlepressure(intendedChangeValueAuxFloat);
      break;

    case targetInspValveAperture: // define target Inspiration Valve Aperture, in this mode the PID is controlled through EPICs.
      intendedChangeValueAuxInt = intendedChangeValue.toInt();
      constrain(intendedChangeValueAuxInt, MIN_TARGET_APERTURE, MAX_TARGET_APERTURE); //sanitize/limit target inspiratory pressure.
      handleInspiratoryValveAperture(intendedChangeValueAuxInt);
      break;

    case targetExpValveAperture: // define target Expiration Valve Aperture, in this mode the PID is controlled through EPICs.
      intendedChangeValueAuxInt = intendedChangeValue.toInt();
      constrain(intendedChangeValueAuxInt, MIN_TARGET_APERTURE, MAX_TARGET_APERTURE); //sanitize/limit target inspiratory pressure.
      handleExpiratoryValveAperture(intendedChangeValueAuxInt);
      break;

    case targetState: // current state, as defined by EPICs controller
      //switchOnBoardLEDState(); // for debug purposes only, switchOnBoardLEDState
      intendedChangeValueAuxInt = intendedChangeValue.toInt();
      if (intendedChangeValueAuxInt != currentState)
      {
        switch (intendedChangeValueAuxInt)
        {
        case inspiration: // close expiration valve. Opening of the inspiration valve will be handled by a direct command through EPICs, reset tidalVolume
          tidalVolume = 0.00;
          //handleExpiratoryValveAperture(MIN_TARGET_APERTURE);
          break;
        case expiration: // close inspiration valve, open expiration valve
          //handleInspiratoryValveAperture(MIN_TARGET_APERTURE);
          //handleExpiratoryValveAperture(MAX_TARGET_APERTURE);
          break;
        case expirationHold: // close both valves
          //handleInspiratoryValveAperture(MIN_TARGET_APERTURE);
          //handleExpiratoryValveAperture(MIN_TARGET_APERTURE);
          break;
        }
      }
    }
  stringFromEPICs = "";
  stringFromEPICsComplete = false;
  }
  
}



void pressureControlCycle(){
  if (currentMillis - previousControlCycleMillis >= controlCycleInterval) {
      switch (cyclePhase) {
        case inspiration:
            if (inspirationValveIsOpen) {
                if (pressure >= peakInspirationPressure){
                    handleInspiratoryValveAperture(MIN_TARGET_APERTURE);
                    cyclePhase = inspirationHold;
                    inspirationHoldPhaseStartMillis=currentMillis;
                }
                else if (tidalVolume > tidalVolumeUpperLimit){ // Volume Upper Threshold reached?
                  //inspirationVolumeThresholdAlarm();
                  handleInspiratoryValveAperture(MIN_TARGET_APERTURE);
                  cyclePhase = inspirationHold;
                  inspirationHoldPhaseStartMillis=currentMillis;
                }
                else if (currentMillis - inspirationPhaseStartMillis > inspirationPhaseDuration){ // Inspiration Time Upper Limit reached?
                  //inspirationTimerThresholdAlarm();
                  handleInspiratoryValveAperture(MIN_TARGET_APERTURE);
                  cyclePhase = inspirationHold;
                  inspirationHoldPhaseStartMillis=currentMillis;
                }
            }
            else { // just for the first time the function is called
             handleInspiratoryValveAperture(INSPIRATION_APERTURE_TARGET);
              inspirationPhaseStartMillis=currentMillis;
            }
            break;
        case inspirationHold:
             if (currentMillis - inspirationHoldPhaseStartMillis > inspirationHoldPhaseDuration){ // Inspiration hold duration reached?
                handleExpiratoryValveAperture(MAX_TARGET_APERTURE);
                cyclePhase = expiration;
                expirationPhaseStartMillis=currentMillis;
             }
             break;
        case expiration:
              if (pressure < positiveEndExpiratoryPressure){
                  handleExpiratoryValveAperture(MIN_TARGET_APERTURE);
                 handleInspiratoryValveAperture(INSPIRATION_APERTURE_TARGET);
                  cyclePhase = inspiration;
                  inspirationPhaseStartMillis=currentMillis;
              }
              else if (currentMillis - expirationPhaseStartMillis > expirationPhaseDuration){ // Expiration Time Upper Limit reached?
                  //expirationTimerThresholdAlarm();
                  handleExpiratoryValveAperture(MIN_TARGET_APERTURE);
                 handleInspiratoryValveAperture(INSPIRATION_APERTURE_TARGET);
                  cyclePhase = inspiration;
                  inspirationPhaseStartMillis=currentMillis;
              }
              break;
      }
      previousControlCycleMillis = currentMillis;
}

}

void interpretSlaveMCUReading()
{
  {
    unsigned long currentMCUReadMillis = millis();
    flow = stringFromSlaveMCU.toFloat() / flowOffsetMultiplier;
    tidalVolume = tidalVolume + (flow * (currentMCUReadMillis - previousFlowReadMillis) / 60);
    if (tidalVolume < 0){
      tidalVolume = 0;
    }
    previousFlowReadMillis = currentMCUReadMillis;
  }
  stringFromSlaveMCU = "";
  stringFromSlaveMCUComplete = false;
}

void serialEvent()
{
  while (Serial.available())
  {

    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    stringFromEPICs += inChar;
    // if the incoming character is a newline, set a flag
    // so other function spaces can do something about it:
    if (inChar == '\n')
    {
      stringFromEPICsComplete = true;
    }
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
