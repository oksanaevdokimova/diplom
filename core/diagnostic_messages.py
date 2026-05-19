"""Technical diagnostic message text (English, no level prefixes)."""

from __future__ import annotations

import re

_LEGACY_PREFIXES = (
    "service unavailable:",
    "internal server error:",
    "forbidden:",
    "not found:",
    "warning:",
    "error:",
    "ok:",
)

_FIELD_ISSUE_EN: dict[str, str] = {
    "COM-порт: порт не должен быть пустым": "field=com_port, constraint=must not be empty",
    "Скорость: целое положительное число": "field=baud_rate, constraint=positive integer required",
    "Хост: не должен быть пустым": "field=host, constraint=must not be empty",
    "Порт: целое положительное число": "field=port, constraint=positive integer required",
    "Брокер: не должен быть пустым": "field=broker_host, constraint=must not be empty",
    "Порт брокера: целое положительное число": "field=broker_port, constraint=positive integer required",
    "Топик команд: не должен быть пустым": "field=command_topic, constraint=must not be empty",
    "Топик сообщений: не должен быть пустым": "field=message_topic, constraint=must not be empty",
    "Положение: целое положительное число": "field=position, constraint=positive integer required",
    "Положение: целое положительное число или пусто": (
        "field=position, constraint=positive integer or empty (optional)"
    ),
    "Скорость: целое положительное число или пусто (по умолчанию)": (
        "field=speed, constraint=positive integer or empty (default applied)"
    ),
}

_TELEMETRY_ISSUE_EN: dict[str, str] = {
    "Нет actuator_id — нельзя привязать к механизму": "missing actuator_id, cannot bind to mechanism",
    "Пустой payload": "empty payload object",
    "Нет поля state": "missing required field state",
}

_CONFIG_DETAIL_EN: dict[str, str] = {
    "Укажите COM-порт для USB": "usb.port is empty, specify COM port for USB transport",
}


def strip_legacy_prefix(text: str) -> str:
    result = text.strip()
    while result:
        lowered = result.lower()
        stripped = False
        for prefix in _LEGACY_PREFIXES:
            if lowered.startswith(prefix):
                result = result[len(prefix) :].lstrip()
                stripped = True
                break
        if not stripped:
            break
    return result


def english_field_issue(issue: str) -> str:
    return _FIELD_ISSUE_EN.get(issue.strip(), strip_legacy_prefix(issue))


def english_telemetry_issue(issue: str) -> str:
    if issue in _TELEMETRY_ISSUE_EN:
        return _TELEMETRY_ISSUE_EN[issue]
    match = re.match(r"Недопустимый state: (.+)", issue)
    if match:
        return f"invalid state value: {match.group(1)}"
    return strip_legacy_prefix(issue)


def english_config_detail(detail: str) -> str:
    clean = detail.strip()
    if clean.startswith("Конфигурация:"):
        clean = clean[len("Конфигурация:") :].strip()
    if clean in _CONFIG_DETAIL_EN:
        return _CONFIG_DETAIL_EN[clean]
    if detail.strip() in _CONFIG_DETAIL_EN:
        return _CONFIG_DETAIL_EN[detail.strip()]
    return strip_legacy_prefix(clean)


def english_controller_description(description: str) -> str:
    clean = strip_legacy_prefix(description)
    if clean.startswith("command handled"):
        return clean.replace("command handled", "command handled by controller", 1)
    if clean.startswith("actuator move started"):
        return clean.replace("actuator move started", "controller reports move started", 1)
    if clean.startswith("actuator stop issued"):
        return clean.replace("actuator stop issued", "controller reports stop issued", 1)
    return clean


def link_lost(*, check: str, detail: str) -> str:
    clean = strip_legacy_prefix(detail)
    if check:
        return f"link lost during check phase={check!r}: {clean}"
    return f"link lost: {clean}"


def link_send_unavailable() -> str:
    return "link watchdog cannot send ping: transport send handler is not configured"


def link_command_not_connected() -> str:
    return "command not sent: transport has no active connection"


def command_pong_timeout(*, check_phase: str = "") -> str:
    phase = f", check_phase={check_phase!r}" if check_phase else ""
    return f"command delivery watchdog timeout: no pong received after command was sent{phase}"


def command_response_timeout(command_id: int | str, timeout_ms: int) -> str:
    return (
        f"command response timeout: command_id={command_id}, "
        f"elapsed_limit_ms={timeout_ms}"
    )


def actuators_send_unavailable() -> str:
    return "actuators_list request not sent: transport send handler is not configured"


def actuators_list_timeout() -> str:
    return "actuators_list response timeout: no reply from controller within limit"


def actuators_list_invalid(detail: str) -> str:
    return f"actuators_list payload invalid: {strip_legacy_prefix(detail)}"


def actuators_list_empty() -> str:
    return "actuators_list returned zero mechanisms (empty list)"


def protocol_json_error(detail: str) -> str:
    clean = strip_legacy_prefix(detail)
    if clean.lower().startswith("json decode failed"):
        return clean
    return f"JSON decode failed on protocol line: {clean}"


def protocol_empty_line() -> str:
    return "protocol line is empty after framing"


def protocol_not_object() -> str:
    return "protocol message root must be a JSON object"


def protocol_validation_error(detail: str) -> str:
    return f"protocol message validation failed: {strip_legacy_prefix(detail)}"


def protocol_unexpected_command() -> str:
    return "inbound message rejected: message_type=command is not expected from controller"


def protocol_unknown_type(message_type: str) -> str:
    return f"inbound message rejected: unknown message_type={message_type!r}"


def client_config_rejected(detail: str) -> str:
    return f"connection config rejected before connect: {english_config_detail(detail)}"


def client_command_build_failed() -> str:
    return (
        "command build failed: invalid mechanism selection, action, position, or speed"
    )


def client_command_blocked_no_link() -> str:
    return "command blocked: link to controller is not established"


def field_value_invalid(field_issue: str) -> str:
    return f"connection panel field validation failed: {english_field_issue(field_issue)}"


def connection_failed(field_issues: str) -> str:
    en = "; ".join(
        english_field_issue(part.strip())
        for part in field_issues.split(";")
        if part.strip()
    )
    return f"connect aborted after field validation errors: {en}"


def client_input_field_invalid(detail: str) -> str:
    return f"control panel field validation failed: {english_field_issue(detail)}"


def link_disconnected_from_controller(*, user_initiated: bool = False) -> str:
    if user_initiated:
        return "session ended: operator requested disconnect from controller"
    return "session ended: link to controller lost (transport closed or watchdog timeout)"


def link_connecting() -> str:
    return "link handshake: connection requested, awaiting transport link and pong from controller"


def link_ready() -> str:
    return "link established: pong received, controller channel is ready"


def actuators_loaded(count: int) -> str:
    return f"actuators_list received: mechanism_count={count}"


def transport_not_connected(transport: str) -> str:
    return f"{transport}: operation refused, transport is not connected"


def transport_module_missing(module: str, transport: str) -> str:
    return f"{transport}: missing Python module dependency {module!r}"


def transport_io_error_detail(detail: str) -> str:
    """Bare I/O detail without repeated transport prefix."""
    clean = strip_legacy_prefix(detail)
    marker = ": I/O error — "
    while marker in clean:
        clean = clean.split(marker, 1)[1].strip()
    return clean


def transport_io_error(transport: str, detail: str) -> str:
    return f"{transport}: I/O error — {transport_io_error_detail(detail)}"


def transport_tcp_connect_error(
    *,
    channel: str,
    host: str,
    port: int,
    raw_detail: str,
    timeout_seconds: float,
) -> str:
    """Human-readable TCP connect failure (Wi-Fi, GSM TCP)."""
    detail = transport_io_error_detail(raw_detail).lower()
    target = f"{host}:{port}"
    limit = int(timeout_seconds)
    if "timed out" in detail or "errno 60" in detail:
        return (
            f"{channel} connection timed out after {limit}s while connecting to {target}. "
            "Check controller IP address, TCP port in configuration, Wi-Fi network, firewall, "
            "and that the controller is powered on and listening."
        )
    if "connection refused" in detail or "errno 61" in detail:
        return (
            f"{channel} connection refused at {target}. "
            "The host is reachable but nothing accepts TCP on this port — "
            "verify the controller service port in configuration."
        )
    if (
        "network is unreachable" in detail
        or "no route to host" in detail
        or "errno 51" in detail
        or "errno 65" in detail
    ):
        return (
            f"{channel} network unreachable for {target}. "
            "Check that this computer and the controller are on the same network "
            "and the IP address is correct."
        )
    if "errno 8" in detail or "nodename nor servname" in detail:
        return (
            f"{channel} cannot resolve host name {host!r}. "
            "Use a numeric IP address or fix DNS / hostname spelling."
        )
    bare = transport_io_error_detail(raw_detail)
    return f"{channel} connection to {target} failed: {bare}"


def transport_invalid_socket(transport: str) -> str:
    return f"{transport}: invalid socket type for send/receive"


def transport_mqtt_publish_failed(rc: int) -> str:
    return f"MqttTransport: MQTT publish failed, broker_return_code={rc}"


def orphan_response(command_id: int | str | None) -> str:
    return f"orphan response ignored: no pending command for command_id={command_id}"


def telemetry_validation_failed(
    actuator_id: int | str,
    issues: list[str],
    *,
    message_id: int | None = None,
) -> str:
    en_issues = "; ".join(english_telemetry_issue(i) for i in issues)
    parts = [f"telemetry validation failed: actuator_id={actuator_id}"]
    if message_id is not None:
        parts.append(f"message_id={message_id}")
    parts.append(f"issues=[{en_issues}]")
    return ", ".join(parts)
