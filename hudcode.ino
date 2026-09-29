#include <U8g2lib.h>

// =====================================================
// OLED - SH1106 128x64
// SOFTWARE I2C
//
// SCL = GPIO 18
// SDA = GPIO 19
//
// U8G2_MIRROR is used because the acrylic reflection
// creates a mirror image. The OLED itself is mirrored
// so that the reflected image appears normal to the driver.
// =====================================================

U8G2_SH1106_128X64_NONAME_F_SW_I2C u8g2(
  U8G2_MIRROR,
  /* clock = */ 18,
  /* data  = */ 19,
  /* reset = */ U8X8_PIN_NONE
);


// =====================================================
// HC-SR04 CONNECTIONS
// =====================================================

// LEFT SENSOR
#define LEFT_TRIG  5
#define LEFT_ECHO 34

// RIGHT SENSOR
#define RIGHT_TRIG 17
#define RIGHT_ECHO 35


// =====================================================
// DEMO DISTANCE LEVELS
//
// SAFE       > 150 cm
// CAUTION    81-150 cm
// HIGH ALERT 41-80 cm
// STOP       <= 40 cm
//
// These are DEMO thresholds, not real mining safety limits.
// =====================================================

#define CAUTION_DIST     150
#define HIGH_ALERT_DIST   80
#define STOP_DIST         40


// =====================================================
// READ HC-SR04 DISTANCE
// =====================================================

int readDistance(int trigPin, int echoPin)
{
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);

  digitalWrite(trigPin, LOW);

  long duration = pulseIn(
    echoPin,
    HIGH,
    30000
  );

  // No echo
  if (duration == 0)
  {
    return 999;
  }

  int distance = duration * 0.0343 / 2;

  // Invalid reading
  if (distance < 2 || distance > 400)
  {
    return 999;
  }

  return distance;
}


// =====================================================
// PRINT DISTANCE
// =====================================================

void printDistance(int distance)
{
  if (distance == 999)
  {
    u8g2.print(">4.0m");
  }
  else
  {
    u8g2.print(distance / 100.0, 1);
    u8g2.print("m");
  }
}


// =====================================================
// DRAW LEFT / RIGHT DISTANCES
// =====================================================

void drawDistances(int leftDist, int rightDist)
{
  u8g2.setFont(u8g2_font_6x10_tf);

  // LEFT
  u8g2.setCursor(2, 27);
  u8g2.print("L ");
  printDistance(leftDist);

  // RIGHT
  u8g2.setCursor(78, 27);
  u8g2.print("R ");
  printDistance(rightDist);

  // Center separator
  u8g2.drawLine(
    64, 17,
    64, 29
  );
}


// =====================================================
// SAFE PATH SCREEN
// =====================================================

void showSafe(int leftDist, int rightDist)
{
  u8g2.clearBuffer();

  // Header
  u8g2.setFont(u8g2_font_6x10_tf);
  u8g2.drawStr(
    36, 9,
    "HAUL TRUCK"
  );

  // Main message
  u8g2.setFont(u8g2_font_9x15_tf);
  u8g2.drawStr(
    32, 25,
    "SAFE PATH"
  );

  // L / R distances
  drawDistances(
    leftDist,
    rightDist
  );

  // Large forward arrow
  u8g2.drawLine(
    64, 34,
    64, 49
  );

  u8g2.drawLine(
    64, 34,
    58, 42
  );

  u8g2.drawLine(
    64, 34,
    70, 42
  );

  // Bottom status
  u8g2.setFont(u8g2_font_6x10_tf);
  u8g2.drawStr(
    38, 61,
    "PATH CLEAR"
  );

  u8g2.sendBuffer();
}


// =====================================================
// CAUTION SCREEN
// =====================================================

void showCaution(int leftDist, int rightDist)
{
  u8g2.clearBuffer();

  // Header
  u8g2.setFont(u8g2_font_9x15_tf);
  u8g2.drawStr(
    36, 14,
    "CAUTION"
  );

  // Distances
  drawDistances(
    leftDist,
    rightDist
  );

  u8g2.setFont(u8g2_font_6x10_tf);

  // LEFT obstacle
  if (leftDist < rightDist)
  {
    u8g2.drawStr(
      2, 39,
      "<<"
    );

    u8g2.drawStr(
      25, 39,
      "OBSTACLE"
    );

    u8g2.drawStr(
      32, 57,
      "KEEP RIGHT"
    );
  }

  // RIGHT obstacle
  else if (rightDist < leftDist)
  {
    u8g2.drawStr(
      77, 39,
      "OBSTACLE"
    );

    u8g2.drawStr(
      111, 39,
      ">>"
    );

    u8g2.drawStr(
      31, 57,
      "KEEP LEFT"
    );
  }

  // Both similar
  else
  {
    u8g2.drawStr(
      28, 39,
      "<< OBSTACLE >>"
    );

    u8g2.drawStr(
      39, 57,
      "CHECK PATH"
    );
  }

  u8g2.sendBuffer();
}


// =====================================================
// HIGH ALERT SCREEN
// =====================================================

void showHighAlert(
  int leftDist,
  int rightDist
)
{
  u8g2.clearBuffer();

  // Header
  u8g2.setFont(u8g2_font_9x15_tf);
  u8g2.drawStr(
    22, 14,
    "HIGH ALERT"
  );

  // Distances
  drawDistances(
    leftDist,
    rightDist
  );

  u8g2.setFont(u8g2_font_6x10_tf);

  bool leftClose =
    leftDist <= HIGH_ALERT_DIST;

  bool rightClose =
    rightDist <= HIGH_ALERT_DIST;

  // BOTH SIDES
  if (leftClose && rightClose)
  {
    u8g2.drawStr(
      2, 40,
      "<<"
    );

    u8g2.drawStr(
      31, 40,
      "OBSTACLE"
    );

    u8g2.drawStr(
      108, 40,
      ">>"
    );

    u8g2.drawStr(
      32, 58,
      "REDUCE SPEED"
    );
  }

  // LEFT
  else if (leftClose)
  {
    u8g2.drawStr(
      2, 40,
      "<<<<"
    );

    u8g2.drawStr(
      42, 40,
      "LEFT HAZARD"
    );

    u8g2.drawStr(
      33, 58,
      "KEEP RIGHT"
    );
  }

  // RIGHT
  else if (rightClose)
  {
    u8g2.drawStr(
      68, 40,
      "RIGHT HAZARD"
    );

    u8g2.drawStr(
      106, 40,
      ">>>>"
    );

    u8g2.drawStr(
      33, 58,
      "KEEP LEFT"
    );
  }

  u8g2.sendBuffer();
}


// =====================================================
// STOP SCREEN
// =====================================================

void showStop(
  int leftDist,
  int rightDist
)
{
  u8g2.clearBuffer();

  // White background
  u8g2.drawBox(
    0, 0,
    128, 64
  );

  // Black text
  u8g2.setDrawColor(0);

  // STOP
  u8g2.setFont(
    u8g2_font_9x15_tf
  );

  u8g2.drawStr(
    30, 14,
    "!! STOP !!"
  );

  // Distances
  u8g2.setFont(
    u8g2_font_6x10_tf
  );

  u8g2.setCursor(3, 28);
  u8g2.print("L ");
  printDistance(leftDist);

  u8g2.setCursor(76, 28);
  u8g2.print("R ");
  printDistance(rightDist);

  // Divider
  u8g2.drawLine(
    0, 34,
    127, 34
  );

  // Main command
  u8g2.setFont(
    u8g2_font_9x15_tf
  );

  u8g2.drawStr(
    22, 49,
    "STOP VEHICLE"
  );

  // Bottom message
  u8g2.setFont(
    u8g2_font_6x10_tf
  );

  u8g2.drawStr(
    28, 61,
    "OBSTACLE CLOSE"
  );

  // Restore white drawing
  u8g2.setDrawColor(1);

  u8g2.sendBuffer();
}


// =====================================================
// SETUP
// =====================================================

void setup()
{
  Serial.begin(115200);

  // -------------------------------
  // OLED
  // -------------------------------

  u8g2.begin();

  // -------------------------------
  // LEFT HC-SR04
  // -------------------------------

  pinMode(
    LEFT_TRIG,
    OUTPUT
  );

  pinMode(
    LEFT_ECHO,
    INPUT
  );

  // -------------------------------
  // RIGHT HC-SR04
  // -------------------------------

  pinMode(
    RIGHT_TRIG,
    OUTPUT
  );

  pinMode(
    RIGHT_ECHO,
    INPUT
  );

  // -------------------------------
  // START SCREEN
  // -------------------------------

  u8g2.clearBuffer();

  u8g2.setFont(
    u8g2_font_9x15_tf
  );

  u8g2.drawStr(
    20, 22,
    "MINING HUD"
  );

  u8g2.setFont(
    u8g2_font_6x10_tf
  );

  u8g2.drawStr(
    30, 42,
    "SYSTEM READY"
  );

  u8g2.drawStr(
    25, 58,
    "DUAL SENSOR"
  );

  u8g2.sendBuffer();

  delay(1500);

  Serial.println(
    "MINING HUD READY"
  );
}


// =====================================================
// MAIN LOOP
// =====================================================

void loop()
{
  // -----------------------------------------
  // READ LEFT SENSOR
  // -----------------------------------------

  int leftDist =
    readDistance(
      LEFT_TRIG,
      LEFT_ECHO
    );

  // Give ultrasonic pulse time to die out
  delay(50);

  // -----------------------------------------
  // READ RIGHT SENSOR
  // -----------------------------------------

  int rightDist =
    readDistance(
      RIGHT_TRIG,
      RIGHT_ECHO
    );

  // -----------------------------------------
  // DISPLAY LOGIC
  // -----------------------------------------

  // PRIORITY 1
  // CRITICAL
  if (
    leftDist <= STOP_DIST ||
    rightDist <= STOP_DIST
  )
  {
    showStop(
      leftDist,
      rightDist
    );
  }

  // PRIORITY 2
  // HIGH ALERT
  else if (
    leftDist <= HIGH_ALERT_DIST ||
    rightDist <= HIGH_ALERT_DIST
  )
  {
    showHighAlert(
      leftDist,
      rightDist
    );
  }

  // PRIORITY 3
  // CAUTION
  else if (
    leftDist <= CAUTION_DIST ||
    rightDist <= CAUTION_DIST
  )
  {
    showCaution(
      leftDist,
      rightDist
    );
  }

  // PRIORITY 4
  // SAFE
  else
  {
    showSafe(
      leftDist,
      rightDist
    );
  }

  // -----------------------------------------
  // SERIAL MONITOR
  // -----------------------------------------

  Serial.print("LEFT: ");
  Serial.print(leftDist);

  Serial.print(" cm | RIGHT: ");
  Serial.print(rightDist);

  Serial.println(" cm");

  // Approx. 10 Hz HUD update
  delay(50);
}