#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

MAX30105 particleSensor;

long lastBeat = 0; // Time at which the last beat occurred
float beatsPerMinute;

void setup() {
  Serial.begin(115200);
  // Serial.println("Initializing...");

  // Initialize sensor
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) { //
    Serial.println("MAX30102 was not found. Please check wiring/power. ");
    while (1); 
  }
  // Serial.println("Place your index finger on the sensor with steady pressure.");

  particleSensor.setup(); // Configure sensor with default settings
  particleSensor.setPulseAmplitudeRed(0x0A); // Turn Red LED to low to indicate sensor is running
  particleSensor.setPulseAmplitudeGreen(0); // Turn off Green LED
}

void loop() {
  long irValue = particleSensor.getIR();

  // Check for a heartbeat
  if (checkForBeat(irValue) == true) {
    // A beat was sensed!
    long delta = millis() - lastBeat;
    lastBeat = millis(); 

    // Calculate the instantaneous beats per minute
    beatsPerMinute = 60 / (delta / 1000.0);

    // Check if the reading is within a realistic range and print it
    if (beatsPerMinute < 255 && beatsPerMinute > 20) { 
      Serial.println(beatsPerMinute);
    }
  }
}
