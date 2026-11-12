// Ramu Kaka box: ESP32, SCT-013 clip-on current sensor, MPU6050 vibration chip.
// This has NOT been run on a board yet. It is written from the datasheets.
//
// Wiring for one machine:
//   SCT-013 with a burden resistor and a 1.65 V bias circuit -> GPIO34
//   MPU6050: SDA -> GPIO21, SCL -> GPIO22, VCC 3.3 V, GND
//   LED -> GPIO2, buzzer -> GPIO4
//
// Every window it prints one line of numbers over serial:
//   current_rms,current_change,vib_rms,vib_peak
// These are the same four numbers the Python code in this repo uses.
//
// While the machine runs it first learns what normal looks like, then flags a
// window when one number is far from normal in several windows out of the last
// few. The Python code adds an Isolation Forest on top of this same check.
#include <Wire.h>
#include <math.h>

const int CURRENT_PIN = 34, LED_PIN = 2, BUZZER_PIN = 4;
const int MPU_ADDR = 0x68;

const float CURRENT_SCALE = 1.0;   // amps per volt. Set it by clamping a known load.
const float IDLE_BELOW    = 0.5;   // amps. Below this the machine is idle, so we ignore it.
// One window takes about a second, so 2000 windows is only about half an hour.
// For the real baseline use several weeks of normal running, or let the box
// keep learning while it is not flagging.
const int   BASELINE_WINDOWS = 2000;
const float Z_LIMIT = 4.0;         // how many spreads from normal counts as odd
const int   NEED_ODD = 4, OF_LAST = 6;

float meanF[4], m2F[4];            // running mean and spread of each number
long  seen = 0;
bool  recent[OF_LAST];
int   pos = 0;
float lastCur = 0;

// Length of the acceleration vector in g.
float readAccelG() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 6);
  int16_t ax = Wire.read() << 8 | Wire.read();
  int16_t ay = Wire.read() << 8 | Wire.read();
  int16_t az = Wire.read() << 8 | Wire.read();
  float x = ax / 16384.0, y = ay / 16384.0, z = az / 16384.0;
  return sqrt(x * x + y * y + z * z);
}

void readWindow(float f[4]) {
  const int N = 200;
  float cur[N], acc[N];
  for (int i = 0; i < N; i++) {
    cur[i] = analogReadMilliVolts(CURRENT_PIN) / 1000.0;
    acc[i] = readAccelG();
    delayMicroseconds(2500);
  }
  float cm = 0, am = 0;
  for (int i = 0; i < N; i++) { cm += cur[i]; am += acc[i]; }
  cm /= N; am /= N;

  float cv = 0, av = 0, peak = 0;
  for (int i = 0; i < N; i++) {
    float c = cur[i] - cm;         // take away the bias voltage
    float a = acc[i] - am;         // take away gravity
    cv += c * c;
    av += a * a;
    if (fabs(a) > peak) peak = fabs(a);
  }
  f[0] = sqrt(cv / N) * CURRENT_SCALE;   // current_rms
  f[1] = fabs(f[0] - lastCur);           // current_change since the last window
  f[2] = sqrt(av / N);                   // vib_rms
  f[3] = peak;                           // vib_peak
  lastCur = f[0];
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  Wire.begin(21, 22);
  Wire.beginTransmission(MPU_ADDR);   // wake the MPU6050
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission();
  analogReadResolution(12);
}

void loop() {
  float f[4];
  readWindow(f);
  Serial.printf("%.4f,%.4f,%.4f,%.4f\n", f[0], f[1], f[2], f[3]);

  if (f[0] < IDLE_BELOW) {            // machine is off or idle: do not learn or flag
    digitalWrite(LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, LOW);
    return;
  }

  if (seen < BASELINE_WINDOWS) {      // still learning normal
    seen++;
    for (int k = 0; k < 4; k++) {
      float d = f[k] - meanF[k];
      meanF[k] += d / seen;
      m2F[k] += d * (f[k] - meanF[k]);
    }
    return;
  }

  bool odd = false;
  for (int k = 0; k < 4; k++) {
    float spread = sqrt(m2F[k] / seen) + 1e-6;
    if (fabs(f[k] - meanF[k]) / spread > Z_LIMIT) odd = true;
  }
  recent[pos] = odd;
  pos = (pos + 1) % OF_LAST;

  int count = 0;
  for (int i = 0; i < OF_LAST; i++) count += recent[i];
  bool flag = count >= NEED_ODD;      // several odd windows, not one noisy one
  digitalWrite(LED_PIN, flag);
  digitalWrite(BUZZER_PIN, flag);
}
