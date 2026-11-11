// Ramu Kaka box: ESP32 + SCT-013 clip-on current sensor + MPU6050 vibration chip.
// NOT TESTED ON HARDWARE YET. Written from the parts' datasheets.
// Wiring (one machine):
//   SCT-013 (with burden resistor and 1.65 V bias circuit) -> GPIO34
//   MPU6050 SDA -> GPIO21, SCL -> GPIO22, VCC 3.3 V, GND
//   LED -> GPIO2, buzzer -> GPIO4
// Every window it prints one CSV line: current_mean,current_std,vib_rms,vib_peak
// The same four features the Python code in this repo uses.
#include <Wire.h>
#include <math.h>

const int CURRENT_PIN = 34, LED_PIN = 2, BUZZER_PIN = 4;
const int MPU_ADDR = 0x68;
const float CURRENT_SCALE = 1.0;     // amps per ADC volt. Calibrate with a known load.
const int   BASELINE_WINDOWS = 2000; // windows of normal running before it starts flagging
const float Z_LIMIT = 4.0;           // how far from normal counts as odd
const int   NEED_ODD = 4, OF_LAST = 6;

float meanF[4], m2F[4];              // running mean and spread of each feature (Welford)
long  seen = 0;
bool  recent[OF_LAST];
int   pos = 0;

float readAccelG() {                 // length of the acceleration vector in g
  Wire.beginTransmission(MPU_ADDR); Wire.write(0x3B); Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 6);
  int16_t ax = Wire.read() << 8 | Wire.read();
  int16_t ay = Wire.read() << 8 | Wire.read();
  int16_t az = Wire.read() << 8 | Wire.read();
  float x = ax / 16384.0, y = ay / 16384.0, z = az / 16384.0;
  return sqrt(x * x + y * y + z * z);
}

void window(float f[4]) {
  const int N = 200;
  float cur[N], acc[N];
  for (int i = 0; i < N; i++) {      // about 400 samples per second
    cur[i] = analogReadMilliVolts(CURRENT_PIN) / 1000.0;
    acc[i] = readAccelG();
    delayMicroseconds(2500);
  }
  float cm = 0, am = 0;
  for (int i = 0; i < N; i++) { cm += cur[i]; am += acc[i]; }
  cm /= N; am /= N;
  float cv = 0, av = 0, peak = 0;
  for (int i = 0; i < N; i++) {
    float c = cur[i] - cm, a = acc[i] - am;   // remove the DC bias and gravity
    cv += c * c; av += a * a;
    if (fabs(a) > peak) peak = fabs(a);
  }
  f[0] = sqrt(cv / N) * CURRENT_SCALE;        // RMS of the current signal in amps
  f[1] = 0;                                   // spread filled in over windows below
  f[2] = sqrt(av / N);
  f[3] = peak;
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT); pinMode(BUZZER_PIN, OUTPUT);
  Wire.begin(21, 22);
  Wire.beginTransmission(MPU_ADDR); Wire.write(0x6B); Wire.write(0); Wire.endTransmission();
  analogReadResolution(12);
}

float lastCur = 0;
void loop() {
  float f[4];
  window(f);
  f[1] = fabs(f[0] - lastCur); lastCur = f[0];  // change in current between windows

  Serial.printf("%.4f,%.4f,%.4f,%.4f\n", f[0], f[1], f[2], f[3]);

  if (seen < BASELINE_WINDOWS) {                // learning normal
    seen++;
    for (int k = 0; k < 4; k++) {
      float d = f[k] - meanF[k]; meanF[k] += d / seen; m2F[k] += d * (f[k] - meanF[k]);
    }
    return;
  }
  bool odd = false;                             // compare with what normal looked like
  for (int k = 0; k < 4; k++) {
    float sd = sqrt(m2F[k] / seen) + 1e-6;
    if (fabs(f[k] - meanF[k]) / sd > Z_LIMIT) odd = true;
  }
  recent[pos] = odd; pos = (pos + 1) % OF_LAST;
  int count = 0; for (int i = 0; i < OF_LAST; i++) count += recent[i];
  bool flag = count >= NEED_ODD;                // flag only if several windows look odd
  digitalWrite(LED_PIN, flag);
  digitalWrite(BUZZER_PIN, flag);
}
