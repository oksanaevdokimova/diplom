/*
 * Контроллер исполнительных механизмов — прошивка под протокол операторского ПО (diplom).
 *
 * Два шаговых двигателя через драйверы STEP/DIR (A4988, DRV8825, TMC2209 в режиме STEP/DIR).
 * Механизм 0 — «Поворот», механизм 1 — «Захват».
 *
 * Обмен: USB-COM (Serial), 115200 бод, JSON-строка + '\n'.
 * Библиотеки: ArduinoJson 7.x, AccelStepper.
 *
 * Поле position в команде — целевая позиция в шагах (абсолютная).
 * Поле speed — скорость в шагах/с (если не задано — DEFAULT_SPEED_STEPS_S).
 * direction (forward/backward) задаёт знак при относительном move без position (редко).
 */

#include <Arduino.h>
#include <ArduinoJson.h>
#include <AccelStepper.h>

// --- UART и механизмы ---
static const uint32_t SERIAL_BAUD = 115200;
static const size_t LINE_BUFFER_SIZE = 768;
static const uint8_t ACTUATOR_COUNT = 2;

static const char* ACTUATOR_NAMES[ACTUATOR_COUNT] = {"Поворот", "Захват"};

// --- Пины STEP/DIR/ENABLE (ESP32; при необходимости измените под вашу плату) ---
// Механизм 0 — Поворот
static const uint8_t STEP_PIN_0 = 25;
static const uint8_t DIR_PIN_0 = 26;
static const uint8_t EN_PIN_0 = 27;
// Механизм 1 — Захват
static const uint8_t STEP_PIN_1 = 32;
static const uint8_t DIR_PIN_1 = 33;
static const uint8_t EN_PIN_1 = 14;

// ENABLE: LOW = драйверы включены (типично для A4988/DRV8825)
static const bool ENABLE_ACTIVE_LOW = true;

static const float DEFAULT_SPEED_STEPS_S = 800.0f;
static const float DEFAULT_ACCEL_STEPS_S2 = 1600.0f;
static const float MIN_SPEED_STEPS_S = 50.0f;
static const float MAX_SPEED_STEPS_S = 4000.0f;

// --- Состояние ---
enum class MotionState : uint8_t { Ready, Moving, Stopped };

struct ActuatorState {
  MotionState motionState = MotionState::Ready;
  long position = 0;
  int speed = 10;
  const char* direction = "forward";
  bool hasDirection = false;
  bool hasPosition = false;
  bool hasSpeed = false;
};

static ActuatorState g_actuators[ACTUATOR_COUNT];
static AccelStepper g_steppers[ACTUATOR_COUNT] = {
    AccelStepper(AccelStepper::DRIVER, STEP_PIN_0, DIR_PIN_0),
    AccelStepper(AccelStepper::DRIVER, STEP_PIN_1, DIR_PIN_1),
};

static uint32_t g_nextMessageId = 1;
static char g_lineBuffer[LINE_BUFFER_SIZE];
static size_t g_lineLength = 0;

static uint32_t allocMessageId() { return g_nextMessageId++; }

static void formatTimestamp(char* out, size_t outSize) {
  const unsigned long totalSec = millis() / 1000UL;
  const unsigned h = (totalSec / 3600UL) % 24UL;
  const unsigned m = (totalSec / 60UL) % 60UL;
  const unsigned s = totalSec % 60UL;
  snprintf(out, outSize, "2020-01-01T%02u:%02u:%02uZ", h, m, s);
}

static void sendJsonDocument(const JsonDocument& doc) {
  serializeJson(doc, Serial);
  Serial.write('\n');
}

static void sendLine(const char* jsonLine) {
  Serial.print(jsonLine);
  Serial.write('\n');
}

static bool isValidActuatorId(int id) {
  return id >= 0 && id < static_cast<int>(ACTUATOR_COUNT);
}

static float speedToStepsPerSecond(int speed) {
  if (speed <= 0) {
    return DEFAULT_SPEED_STEPS_S;
  }
  const float stepsPerSec = static_cast<float>(speed) * 80.0f;
  if (stepsPerSec < MIN_SPEED_STEPS_S) return MIN_SPEED_STEPS_S;
  if (stepsPerSec > MAX_SPEED_STEPS_S) return MAX_SPEED_STEPS_S;
  return stepsPerSec;
}

static void setDriverEnabled(bool enabled) {
  const uint8_t level = (ENABLE_ACTIVE_LOW ? (enabled ? LOW : HIGH) : (enabled ? HIGH : LOW));
  digitalWrite(EN_PIN_0, level);
  digitalWrite(EN_PIN_1, level);
}

static void syncActuatorPositionFromStepper(uint8_t index) {
  g_actuators[index].position = g_steppers[index].currentPosition();
  g_actuators[index].hasPosition = true;
}

static void configureStepper(uint8_t index, int speed) {
  AccelStepper& motor = g_steppers[index];
  motor.setMaxSpeed(speedToStepsPerSecond(speed));
  motor.setAcceleration(DEFAULT_ACCEL_STEPS_S2);
}

static void emitTelemetry(uint8_t actuatorId, const char* stateStr) {
  syncActuatorPositionFromStepper(actuatorId);
  const ActuatorState& a = g_actuators[actuatorId];
  StaticJsonDocument<384> doc;
  doc["message_type"] = "telemetry";
  doc["message_id"] = allocMessageId();
  char ts[32];
  formatTimestamp(ts, sizeof(ts));
  doc["timestamp"] = ts;
  doc["actuator_id"] = actuatorId;
  JsonObject payload = doc["payload"].to<JsonObject>();
  payload["state"] = stateStr;
  if (a.hasPosition) payload["position"] = a.position;
  if (a.hasSpeed) payload["speed"] = a.speed;
  if (a.hasDirection) payload["direction"] = a.direction;
  sendJsonDocument(doc);
}

static void emitDiagnostic(uint8_t actuatorId, const char* text) {
  StaticJsonDocument<320> doc;
  doc["message_type"] = "diagnostic";
  doc["message_id"] = allocMessageId();
  char ts[32];
  formatTimestamp(ts, sizeof(ts));
  doc["timestamp"] = ts;
  doc["actuator_id"] = actuatorId;
  JsonObject payload = doc["payload"].to<JsonObject>();
  payload["level"] = "info";
  payload["error_code"] = 7001;
  payload["text"] = text;
  sendJsonDocument(doc);
}

static void emitResponseAccepted(uint32_t commandId, uint8_t actuatorId) {
  StaticJsonDocument<256> doc;
  doc["message_type"] = "response";
  doc["message_id"] = allocMessageId();
  char ts[32];
  formatTimestamp(ts, sizeof(ts));
  doc["timestamp"] = ts;
  doc["command_id"] = commandId;
  doc["actuator_id"] = actuatorId;
  JsonObject payload = doc["payload"].to<JsonObject>();
  payload["status"] = "accepted";
  payload["error_code"] = 3003;
  payload["text"] = "command accepted";
  sendJsonDocument(doc);
}

static void emitPong(uint32_t pingMessageId) {
  StaticJsonDocument<192> doc;
  doc["message_type"] = "service";
  doc["message_id"] = allocMessageId();
  char ts[32];
  formatTimestamp(ts, sizeof(ts));
  doc["timestamp"] = ts;
  doc["command_id"] = pingMessageId;
  JsonObject payload = doc["payload"].to<JsonObject>();
  payload["service_type"] = "pong";
  sendJsonDocument(doc);
}

static void emitActuatorsList(uint32_t requestCommandId) {
  StaticJsonDocument<384> doc;
  doc["message_type"] = "service";
  doc["message_id"] = allocMessageId();
  char ts[32];
  formatTimestamp(ts, sizeof(ts));
  doc["timestamp"] = ts;
  doc["command_id"] = requestCommandId;
  JsonObject payload = doc["payload"].to<JsonObject>();
  payload["service_type"] = "actuators_list";
  JsonArray actuators = payload["actuators"].to<JsonArray>();
  for (uint8_t i = 0; i < ACTUATOR_COUNT; ++i) {
    actuators.add(ACTUATOR_NAMES[i]);
  }
  sendJsonDocument(doc);
  for (uint8_t i = 0; i < ACTUATOR_COUNT; ++i) {
    g_actuators[i].motionState = MotionState::Ready;
    emitTelemetry(i, "ready");
  }
}

static long resolveTargetSteps(uint8_t actuatorId, JsonObject payload) {
  AccelStepper& motor = g_steppers[actuatorId];
  const long current = motor.currentPosition();
  if (payload["position"].is<long>() || payload["position"].is<int>()) {
    return payload["position"].as<long>();
  }
  // Относительный сдвиг, если position не указан (шаги по модулю speed)
  const int speed = payload["speed"].is<int>() ? payload["speed"].as<int>() : 10;
  long delta = static_cast<long>(speed) * 50L;
  const char* direction = payload["direction"] | "forward";
  if (strcmp(direction, "backward") == 0) {
    delta = -delta;
  }
  return current + delta;
}

static void handleMove(uint8_t actuatorId, JsonObject payload) {
  ActuatorState& a = g_actuators[actuatorId];
  AccelStepper& motor = g_steppers[actuatorId];

  if (payload["speed"].is<int>()) {
    a.speed = payload["speed"].as<int>();
    a.hasSpeed = true;
  }
  if (payload["direction"].is<const char*>()) {
    a.direction = payload["direction"].as<const char*>();
    a.hasDirection = true;
  }

  configureStepper(actuatorId, a.hasSpeed ? a.speed : 10);
  const long target = resolveTargetSteps(actuatorId, payload);
  a.position = target;
  a.hasPosition = true;

  motor.moveTo(target);
  a.motionState = MotionState::Moving;
  emitTelemetry(actuatorId, "moving");
}

static void handleStop(uint8_t actuatorId, JsonObject payload) {
  ActuatorState& a = g_actuators[actuatorId];
  AccelStepper& motor = g_steppers[actuatorId];

  motor.stop();
  motor.setCurrentPosition(motor.currentPosition());
  syncActuatorPositionFromStepper(actuatorId);

  if (payload["speed"].is<int>()) {
    a.speed = payload["speed"].as<int>();
    a.hasSpeed = true;
  }
  if (payload["direction"].is<const char*>()) {
    a.direction = payload["direction"].as<const char*>();
    a.hasDirection = true;
  }

  a.motionState = MotionState::Stopped;
  emitTelemetry(actuatorId, "stopped");
}

static void handleCommand(JsonDocument& doc) {
  if (!doc["command_id"].is<uint32_t>() && !doc["command_id"].is<int>()) {
    return;
  }
  const uint32_t commandId = doc["command_id"].as<uint32_t>();
  if (!doc["actuator_id"].is<int>()) {
    return;
  }
  const int actuatorId = doc["actuator_id"].as<int>();
  if (!isValidActuatorId(actuatorId)) {
    return;
  }
  JsonObject payload = doc["payload"].as<JsonObject>();
  if (payload.isNull()) {
    return;
  }
  const char* action = payload["action"] | "";
  emitResponseAccepted(commandId, static_cast<uint8_t>(actuatorId));
  if (strcmp(action, "move") == 0) {
    handleMove(static_cast<uint8_t>(actuatorId), payload);
    char desc[80];
    snprintf(
        desc,
        sizeof(desc),
        "actuator move started: target_position=%ld",
        g_actuators[actuatorId].position);
    emitDiagnostic(static_cast<uint8_t>(actuatorId), desc);
  } else if (strcmp(action, "stop") == 0) {
    handleStop(static_cast<uint8_t>(actuatorId), payload);
    char desc[48];
    snprintf(desc, sizeof(desc), "actuator stop issued: actuator_id=%u", actuatorId);
    emitDiagnostic(static_cast<uint8_t>(actuatorId), desc);
  }
}

static void handleService(JsonDocument& doc) {
  JsonObject payload = doc["payload"].as<JsonObject>();
  if (payload.isNull()) {
    return;
  }
  const char* serviceType = payload["service_type"] | "";
  if (strcmp(serviceType, "ping") == 0) {
    if (doc["message_id"].is<uint32_t>() || doc["message_id"].is<int>()) {
      emitPong(doc["message_id"].as<uint32_t>());
    }
    return;
  }
  if (strcmp(serviceType, "get_actuators") == 0) {
    if (doc["command_id"].is<uint32_t>() || doc["command_id"].is<int>()) {
      emitActuatorsList(doc["command_id"].as<uint32_t>());
    }
  }
}

static void processLine(const char* line) {
  StaticJsonDocument<LINE_BUFFER_SIZE> doc;
  const DeserializationError err = deserializeJson(doc, line);
  if (err) {
    return;
  }
  const char* messageType = doc["message_type"] | "";
  if (strcmp(messageType, "service") == 0) {
    handleService(doc);
  } else if (strcmp(messageType, "command") == 0) {
    handleCommand(doc);
  }
}

static void runSteppers() {
  for (uint8_t i = 0; i < ACTUATOR_COUNT; ++i) {
    g_steppers[i].run();
  }
}

static void pollMoveCompletion() {
  for (uint8_t i = 0; i < ACTUATOR_COUNT; ++i) {
    ActuatorState& a = g_actuators[i];
    if (a.motionState != MotionState::Moving) {
      continue;
    }
    if (g_steppers[i].distanceToGo() != 0) {
      continue;
    }
    a.motionState = MotionState::Stopped;
    syncActuatorPositionFromStepper(i);
    emitTelemetry(i, "stopped");
  }
}

static void readSerialLines() {
  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n' || c == '\r') {
      if (g_lineLength > 0) {
        g_lineBuffer[g_lineLength] = '\0';
        processLine(g_lineBuffer);
        g_lineLength = 0;
      }
      continue;
    }
    if (g_lineLength + 1 >= LINE_BUFFER_SIZE) {
      g_lineLength = 0;
      continue;
    }
    g_lineBuffer[g_lineLength++] = c;
  }
}

static void initSteppers() {
  pinMode(EN_PIN_0, OUTPUT);
  pinMode(EN_PIN_1, OUTPUT);
  setDriverEnabled(true);

  for (uint8_t i = 0; i < ACTUATOR_COUNT; ++i) {
    g_steppers[i].setCurrentPosition(0);
    g_steppers[i].setPinsInverted(false, false, ENABLE_ACTIVE_LOW);
    configureStepper(i, 10);
    g_actuators[i] = ActuatorState{};
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  while (!Serial && millis() < 3000) {
    delay(10);
  }
  initSteppers();
  sendLine(
      "{\"message_type\":\"diagnostic\",\"message_id\":1,\"timestamp\":\"2020-01-01T00:00:00Z\","
      "\"payload\":{\"level\":\"info\",\"error_code\":7001,"
      "\"text\":\"Controller ready: 2 stepper actuators (STEP/DIR)\"}}");
}

void loop() {
  readSerialLines();
  runSteppers();
  pollMoveCompletion();
}
