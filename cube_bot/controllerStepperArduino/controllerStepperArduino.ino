// Pin definitions for Stepper Driver (D3 and D4 on Nano)
const int STEP_PIN = 3;
const int DIR_PIN = 4;

// Constant speed configuration (Lower delay = Faster movement)
const int STEP_DELAY_US = 800; 

// Bitmask values sent from your ROS 2 Node
const int BUTTON_A_MASK = 1; // 1 << 0 (Binary 0001) -> Move DOWN
const int BUTTON_Y_MASK = 8; // 1 << 3 (Binary 1000) -> Move UP

int current_button_state = 0;

void setup() {
  Serial.begin(115200);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
}

void loop() {
  // 1. Read the latest button state packet if available
  if (Serial.available() > 0) {
    current_button_state = Serial.parseInt();
    
    // Clear out trailing newlines
    while (Serial.available() > 0 && (Serial.peek() == '\n' || Serial.peek() == '\r')) {
      Serial.read();
    }
  }

  // 2. Decode the bitmask and move the motor
  // Checking if Button Y is pressed (Move Up)
  if ((current_button_state & BUTTON_Y_MASK) != 0) {
    digitalWrite(DIR_PIN, HIGH); // Set direction Up
    executeStep();
  } 
  // Checking if Button A is pressed (Move Down)
  else if ((current_button_state & BUTTON_A_MASK) != 0) {
    digitalWrite(DIR_PIN, LOW);  // Set direction Down
    executeStep();
  }
  // If no buttons are pressed, the motor naturally stays perfectly still
}

// Helper function to step the motor once
void executeStep() {
  digitalWrite(STEP_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(STEP_PIN, LOW);
  delayMicroseconds(STEP_DELAY_US);
}