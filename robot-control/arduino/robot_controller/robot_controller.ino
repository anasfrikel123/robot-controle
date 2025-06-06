/*
 * Robot Controller
 * 
 * This Arduino sketch controls DC motors via L298N driver,
 * reads data from photosensitive and ultrasonic sensors,
 * and communicates with Raspberry Pi via Serial.
 */

// Pin definitions for L298N Motor Driver
const int ENA = 10;  // Enable pin for Motor A
const int IN1 = 9;   // Control pin 1 for Motor A
const int IN2 = 8;   // Control pin 2 for Motor A
const int ENB = 5;   // Enable pin for Motor B
const int IN3 = 7;   // Control pin 1 for Motor B
const int IN4 = 6;   // Control pin 2 for Motor B

// Pin definitions for sensors
const int PHOTO_SENSOR_PIN = A0;  // Photosensitive sensor analog pin
const int ULTRASONIC_TRIG_PIN = 2;  // Ultrasonic sensor trigger pin
const int ULTRASONIC_ECHO_PIN = 3;  // Ultrasonic sensor echo pin

// Variables for sensor readings
int lightLevel = 0;
float distance = 0.0;

// Variables for motor control
int leftMotorSpeed = 0;
int rightMotorSpeed = 0;
bool leftMotorForward = true;
bool rightMotorForward = true;

// Communication protocol
const char START_MARKER = '<';
const char END_MARKER = '>';
const int MAX_MESSAGE_LENGTH = 32;
char receivedChars[MAX_MESSAGE_LENGTH];
boolean newData = false;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Initialize motor control pins
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  
  // Initialize sensor pins
  pinMode(PHOTO_SENSOR_PIN, INPUT);
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);
  
  // Initially stop motors
  stopMotors();
  
  Serial.println("Robot controller initialized");
}

void loop() {
  // Check for commands from Raspberry Pi
  receiveData();
  
  if (newData) {
    processCommand();
    newData = false;
  }
  
  // Read sensor data
  readSensors();
  
  // Send sensor data to Raspberry Pi every 100ms
  static unsigned long lastSensorUpdate = 0;
  if (millis() - lastSensorUpdate > 100) {
    sendSensorData();
    lastSensorUpdate = millis();
  }
}

void receiveData() {
  static boolean recvInProgress = false;
  static int ndx = 0;
  char rc;
  
  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();
    
    if (recvInProgress == true) {
      if (rc != END_MARKER) {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= MAX_MESSAGE_LENGTH) {
          ndx = MAX_MESSAGE_LENGTH - 1;
        }
      } else {
        receivedChars[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    } else if (rc == START_MARKER) {
      recvInProgress = true;
    }
  }
}

void processCommand() {
  // Command format: <CMD,ARG1,ARG2>
  // Commands:
  // - MOV,leftSpeed,rightSpeed (values -255 to 255, negative for reverse)
  // - STP (stop motors)
  
  char* command = strtok(receivedChars, ",");
  
  if (strcmp(command, "MOV") == 0) {
    char* arg1 = strtok(NULL, ",");
    char* arg2 = strtok(NULL, ",");
    
    if (arg1 != NULL && arg2 != NULL) {
      int leftSpeed = atoi(arg1);
      int rightSpeed = atoi(arg2);
      
      setMotorSpeed(leftSpeed, rightSpeed);
      
      // Acknowledge command
      Serial.print("<ACK,MOV,");
      Serial.print(leftSpeed);
      Serial.print(",");
      Serial.print(rightSpeed);
      Serial.println(">");
    }
  } 
  else if (strcmp(command, "STP") == 0) {
    stopMotors();
    
    // Acknowledge command
    Serial.println("<ACK,STP>");
  }
}

void setMotorSpeed(int leftSpeed, int rightSpeed) {
  // Set left motor direction and speed
  leftMotorForward = (leftSpeed >= 0);
  leftMotorSpeed = abs(leftSpeed);
  
  // Set right motor direction and speed
  rightMotorForward = (rightSpeed >= 0);
  rightMotorSpeed = abs(rightSpeed);
  
  // Apply motor settings
  digitalWrite(IN1, leftMotorForward ? HIGH : LOW);
  digitalWrite(IN2, leftMotorForward ? LOW : HIGH);
  analogWrite(ENA, leftMotorSpeed);
  
  digitalWrite(IN3, rightMotorForward ? HIGH : LOW);
  digitalWrite(IN4, rightMotorForward ? LOW : HIGH);
  analogWrite(ENB, rightMotorSpeed);
}

void stopMotors() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 0);
  
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  analogWrite(ENB, 0);
  
  leftMotorSpeed = 0;
  rightMotorSpeed = 0;
}

void readSensors() {
  // Read photosensitive sensor (light level)
  lightLevel = analogRead(PHOTO_SENSOR_PIN);
  
  // Read ultrasonic sensor (distance in cm)
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  
  long duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH);
  distance = duration * 0.034 / 2; // Speed of sound wave divided by 2 (go and back)
}

void sendSensorData() {
  Serial.print("<SEN,");
  Serial.print(lightLevel);
  Serial.print(",");
  Serial.print(distance);
  Serial.println(">");
}
