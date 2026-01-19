/*
 * Arduino Mouse Proxy Firmware
 *
 * Receives movement commands via Serial and executes them as HID mouse movements.
 * Designed for Arduino Leonardo or other boards with native USB HID support.
 */

#include <Mouse.h>

// Protocol constants
const uint8_t START_BYTE = 0xAA;
const uint8_t CMD_MOVE = 0x01;
const uint8_t PACKET_SIZE = 10;

// Response codes
const uint8_t ACK_OK = 0x00;
const uint8_t NAK_CHECKSUM = 0x01;
const uint8_t NAK_INVALID = 0x02;
const uint8_t NAK_INTERRUPTED = 0x03;

// Curve types
const uint8_t CURVE_LINEAR = 0;
const uint8_t CURVE_EASE_IN = 1;
const uint8_t CURVE_EASE_OUT = 2;
const uint8_t CURVE_EASE_IN_OUT = 3;

// Movement state
volatile bool isMoving = false;
int16_t targetDx = 0;
int16_t targetDy = 0;
uint16_t moveDuration = 0;
uint8_t moveCurve = CURVE_LINEAR;
unsigned long moveStartTime = 0;

// Accumulator for sub-pixel movement
float accumulatedX = 0.0;
float accumulatedY = 0.0;
float lastProgressX = 0.0;
float lastProgressY = 0.0;

// Serial buffer
uint8_t buffer[PACKET_SIZE];
uint8_t bufferIndex = 0;

void setup() {
  Serial.begin(115200);
  Mouse.begin();
}

void loop() {
  // Handle incoming serial data
  while (Serial.available() > 0) {
    uint8_t byte = Serial.read();

    // Look for start byte
    if (bufferIndex == 0) {
      if (byte == START_BYTE) {
        buffer[bufferIndex++] = byte;
      }
      continue;
    }

    buffer[bufferIndex++] = byte;

    // Complete packet received
    if (bufferIndex >= PACKET_SIZE) {
      processPacket();
      bufferIndex = 0;
    }
  }

  // Execute movement if active
  if (isMoving) {
    executeMovement();
  }
}

void processPacket() {
  // Verify checksum
  uint8_t checksum = 0;
  for (int i = 0; i < PACKET_SIZE - 1; i++) {
    checksum ^= buffer[i];
  }

  if (checksum != buffer[PACKET_SIZE - 1]) {
    Serial.write(NAK_CHECKSUM);
    return;
  }

  // Check command type
  if (buffer[1] != CMD_MOVE) {
    Serial.write(NAK_INVALID);
    return;
  }

  // Check curve validity
  uint8_t curve = buffer[8];
  if (curve > CURVE_EASE_IN_OUT) {
    Serial.write(NAK_INVALID);
    return;
  }

  // If currently moving, interrupt and signal
  if (isMoving) {
    isMoving = false;
    Serial.write(NAK_INTERRUPTED);
  }

  // Parse movement parameters (little-endian)
  targetDx = (int16_t)(buffer[2] | (buffer[3] << 8));
  targetDy = (int16_t)(buffer[4] | (buffer[5] << 8));
  moveDuration = (uint16_t)(buffer[6] | (buffer[7] << 8));
  moveCurve = curve;

  // Initialize movement
  moveStartTime = millis();
  accumulatedX = 0.0;
  accumulatedY = 0.0;
  lastProgressX = 0.0;
  lastProgressY = 0.0;
  isMoving = true;
}

float applyEasing(float t, uint8_t curve) {
  switch (curve) {
    case CURVE_EASE_IN:
      return t * t;
    case CURVE_EASE_OUT:
      return 1.0 - (1.0 - t) * (1.0 - t);
    case CURVE_EASE_IN_OUT:
      if (t < 0.5) {
        return 2.0 * t * t;
      } else {
        float adjusted = -2.0 * t + 2.0;
        return 1.0 - (adjusted * adjusted) / 2.0;
      }
    case CURVE_LINEAR:
    default:
      return t;
  }
}

void executeMovement() {
  unsigned long elapsed = millis() - moveStartTime;

  // Check if movement is complete
  if (elapsed >= moveDuration) {
    // Execute any remaining movement
    float remainingX = (float)targetDx - lastProgressX;
    float remainingY = (float)targetDy - lastProgressY;

    int8_t moveX = constrain((int)round(remainingX), -127, 127);
    int8_t moveY = constrain((int)round(remainingY), -127, 127);

    if (moveX != 0 || moveY != 0) {
      Mouse.move(moveX, moveY, 0);
    }

    isMoving = false;
    Serial.write(ACK_OK);
    return;
  }

  // Calculate progress with easing
  float t = (float)elapsed / (float)moveDuration;
  float easedT = applyEasing(t, moveCurve);

  // Calculate target position at this point in time
  float currentTargetX = (float)targetDx * easedT;
  float currentTargetY = (float)targetDy * easedT;

  // Calculate delta from last position
  float deltaX = currentTargetX - lastProgressX;
  float deltaY = currentTargetY - lastProgressY;

  // Accumulate sub-pixel movement
  accumulatedX += deltaX;
  accumulatedY += deltaY;

  // Extract integer pixels to move
  int8_t moveX = 0;
  int8_t moveY = 0;

  if (abs(accumulatedX) >= 1.0) {
    moveX = constrain((int)accumulatedX, -127, 127);
    accumulatedX -= moveX;
  }

  if (abs(accumulatedY) >= 1.0) {
    moveY = constrain((int)accumulatedY, -127, 127);
    accumulatedY -= moveY;
  }

  // Execute mouse movement
  if (moveX != 0 || moveY != 0) {
    Mouse.move(moveX, moveY, 0);
  }

  // Update last progress
  lastProgressX = currentTargetX;
  lastProgressY = currentTargetY;
}
