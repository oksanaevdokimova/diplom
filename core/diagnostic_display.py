"""Технические записи диагностики с кодами APP-/LINK-/PROTO-/…"""

from __future__ import annotations

from dataclasses import dataclass

from core import diagnostic_messages as msg
from core.diagnostic_codes import (
    ACT_001,
    ACT_002,
    ACT_003,
    ACT_004,
    ACT_005,
    ACT_006,
    APP_001,
    APP_002,
    APP_003,
    APP_004,
    APP_005,
    CMD_001,
    CMD_002,
    CMD_003,
    CMD_004,
    CMD_005,
    CTRL_001,
    CTRL_002,
    CTRL_003,
    LINK_001,
    LINK_002,
    LINK_003,
    LINK_004,
    LINK_005,
    LINK_006,
    PROTO_001,
    PROTO_002,
    PROTO_003,
    PROTO_004,
    PROTO_005,
    PROTO_006,
    TEL_001,
    TRN_001,
    TRN_002,
    TRN_003,
    TRN_004,
    TRN_005,
    default_display_code_for_level,
    display_code_from_wire,
)
from protocol.message import AppMessage
from protocol.types import Level, Status


@dataclass(frozen=True)
class DiagnosticRecord:
    level: str
    code: str
    message: str
    source: str


def record_config_rejected(detail: str) -> DiagnosticRecord:
    return DiagnosticRecord("ERR", APP_001, msg.client_config_rejected(detail), "App")


def record_from_parse_detail(detail: str) -> DiagnosticRecord:
    clean = msg.strip_legacy_prefix(detail)
    lowered = clean.lower()
    if "unexpected inbound message_type=command" in lowered:
        return DiagnosticRecord(
            "ERR", PROTO_005, msg.protocol_unexpected_command(), "MessageProcessor",
        )
    if "unknown message_type" in lowered:
        start = clean.rfind("=")
        mt = clean[start + 1 :].strip("'\"") if start >= 0 else clean
        return DiagnosticRecord(
            "ERR", PROTO_006, msg.protocol_unknown_type(mt), "MessageProcessor",
        )
    if "json decode" in lowered or "jsondecode" in lowered:
        return DiagnosticRecord(
            "ERR", PROTO_001, msg.protocol_json_error(clean), "MessageProcessor",
        )
    if "empty protocol line" in lowered:
        return DiagnosticRecord("ERR", PROTO_002, msg.protocol_empty_line(), "MessageProcessor")
    if "not object" in lowered or "json object" in lowered:
        return DiagnosticRecord("ERR", PROTO_003, msg.protocol_not_object(), "MessageProcessor")
    return DiagnosticRecord(
        "ERR", PROTO_004, msg.protocol_validation_error(clean), "MessageProcessor",
    )


def record_link_connecting() -> DiagnosticRecord:
    return DiagnosticRecord("INFO", LINK_001, msg.link_connecting(), "LinkWatchdog")


def record_link_lost(detail: str, *, reason: str = "", source: str = "LinkWatchdog") -> DiagnosticRecord:
    return DiagnosticRecord(
        "ERR",
        LINK_003,
        msg.link_lost(check=reason, detail=detail),
        source,
    )


def record_command_link_failed(detail: str) -> DiagnosticRecord:
    clean = msg.strip_legacy_prefix(detail)
    phase = ""
    if "phase=" in clean:
        start = clean.find("phase=")
        phase = clean[start + 6 :].split(":", 1)[0].strip("'\"")
    text = msg.command_pong_timeout(check_phase=phase) if "no pong" in clean.lower() else clean
    return DiagnosticRecord("ERR", LINK_005, text, "LinkWatchdog")


def record_transport_error(detail: str, source: str) -> DiagnosticRecord:
    clean = msg.strip_legacy_prefix(detail)
    lowered = clean.lower()
    transport = source
    head = clean.split("—", 1)[0].split(":", 1)[0].strip()
    if head.endswith("Transport"):
        transport = head
    if "not connected" in lowered:
        return DiagnosticRecord(
            "ERR", TRN_001, msg.transport_not_connected(transport), source,
        )
    if "missing dependency" in lowered or "missing python module" in lowered:
        module = "unknown"
        for token in clean.split():
            if token.startswith("'") or token.startswith('"'):
                module = token.strip("'\"")
                break
        return DiagnosticRecord(
            "ERR", TRN_002, msg.transport_module_missing(module, transport), source,
        )
    if "invalid socket" in lowered:
        return DiagnosticRecord(
            "ERR", TRN_004, msg.transport_invalid_socket(transport), source,
        )
    if "publish failed" in lowered:
        rc = -1
        if "rc=" in lowered:
            try:
                rc = int(clean.rsplit("rc=", 1)[-1].strip())
            except ValueError:
                pass
        return DiagnosticRecord(
            "ERR", TRN_005, msg.transport_mqtt_publish_failed(rc), source,
        )
    return DiagnosticRecord("ERR", TRN_003, msg.transport_io_error(transport, clean), source)


def record_orphan_response(message: AppMessage) -> DiagnosticRecord:
    return DiagnosticRecord(
        "WARN",
        CMD_002,
        msg.orphan_response(message.command_id),
        "CommandManager",
    )


def record_actuators_empty() -> DiagnosticRecord:
    return DiagnosticRecord("WARN", ACT_003, msg.actuators_list_empty(), "ActuatorManager")


def record_telemetry_validation(issues: list[str], message: AppMessage) -> DiagnosticRecord:
    aid = message.actuator_id if message.actuator_id is not None else "?"
    return DiagnosticRecord(
        "WARN",
        TEL_001,
        msg.telemetry_validation_failed(
            aid,
            issues,
            message_id=message.message_id,
        ),
        "TelemetryValidator",
    )


def record_command_build_failed() -> DiagnosticRecord:
    return DiagnosticRecord(
        "ERR", APP_003, msg.client_command_build_failed(), "CommandBuilder",
    )


def record_field_value_warning(field_issue: str, *, source: str = "ConnectionPanel") -> DiagnosticRecord:
    return DiagnosticRecord("WARN", APP_005, msg.field_value_invalid(field_issue), source)


def record_connection_failed(detail: str) -> DiagnosticRecord:
    return DiagnosticRecord(
        "ERR", APP_004, msg.connection_failed(detail), "ConnectionPanel",
    )


def record_input_field_invalid(detail: str) -> DiagnosticRecord:
    return DiagnosticRecord(
        "WARN", APP_005, msg.client_input_field_invalid(detail), "ControlPanel",
    )


def record_disconnected_from_controller(*, user_initiated: bool = False) -> DiagnosticRecord:
    level = "INFO" if user_initiated else "WARN"
    return DiagnosticRecord(
        level,
        LINK_006,
        msg.link_disconnected_from_controller(user_initiated=user_initiated),
        "LinkManager",
    )


def record_command_blocked_no_link() -> DiagnosticRecord:
    return DiagnosticRecord(
        "ERR", APP_002, msg.client_command_blocked_no_link(), "App",
    )


def record_from_controller_diagnostic(message: AppMessage) -> DiagnosticRecord:
    level = _level_from_message(message)
    default = default_display_code_for_level(level)
    code = display_code_from_wire(message.error_code, default=default)
    raw = (message.text or "").strip()
    text = msg.english_controller_description(raw) if raw else _format_diagnostic_detail(message)
    return DiagnosticRecord(level, code, text, "Controller")


def record_from_response(message: AppMessage) -> DiagnosticRecord:
    status = message.status
    if status in (Status.ACCEPTED, Status.COMPLETED):
        code = display_code_from_wire(message.error_code, default=CMD_003)
        return DiagnosticRecord("INFO", code, _format_response_detail(message), "Controller")
    if status == Status.REJECTED:
        code = display_code_from_wire(message.error_code, default=CMD_004)
        return DiagnosticRecord("ERR", code, _format_response_detail(message), "Controller")
    code = display_code_from_wire(message.error_code, default=CMD_005)
    return DiagnosticRecord("ERR", code, _format_response_detail(message), "Controller")


def record_link_ready() -> DiagnosticRecord:
    return DiagnosticRecord("INFO", LINK_002, msg.link_ready(), "LinkWatchdog")


def record_actuators_loaded(count: int) -> DiagnosticRecord:
    return DiagnosticRecord(
        "INFO",
        ACT_001,
        msg.actuators_loaded(count),
        "ActuatorManager",
    )


def record_from_failure_text(text: str, *, default_source: str = "LinkManager") -> DiagnosticRecord:
    clean = msg.strip_legacy_prefix(text)
    lowered = clean.lower()
    if "connect aborted" in lowered or (
        "connection failed" in lowered and "invalid field" not in lowered
    ):
        return DiagnosticRecord("ERR", APP_004, msg.connection_failed(clean), "ConnectionPanel")
    if "connection panel field validation" in lowered or "invalid field value" in lowered:
        issue = clean.split(":", 1)[-1].strip() if ":" in clean else clean
        return DiagnosticRecord("WARN", APP_005, msg.field_value_invalid(issue), "ConnectionPanel")
    if "control panel field validation" in lowered:
        issue = clean.split(":", 1)[-1].strip() if ":" in clean else clean
        return DiagnosticRecord("WARN", APP_005, msg.client_input_field_invalid(issue), "ControlPanel")
    if "disconnected from controller" in lowered or "session ended" in lowered:
        user = "operator" in lowered
        return record_disconnected_from_controller(user_initiated=user)
    if "connection config rejected" in lowered:
        detail = clean.split(":", 1)[-1].strip() if ":" in clean else clean
        return DiagnosticRecord("ERR", APP_001, msg.client_config_rejected(detail), "App")
    if "command build failed" in lowered:
        return DiagnosticRecord("ERR", APP_003, msg.client_command_build_failed(), "CommandBuilder")
    if "command not sent" in lowered and "no active" in lowered:
        return DiagnosticRecord("ERR", LINK_004, msg.link_command_not_connected(), default_source)
    if "command blocked" in lowered:
        return DiagnosticRecord("ERR", APP_002, msg.client_command_blocked_no_link(), "App")
    if "orphan response" in lowered:
        cid = "?"
        if "command_id=" in lowered:
            cid = clean.rsplit("command_id=", 1)[-1].strip()
        return DiagnosticRecord("WARN", CMD_002, msg.orphan_response(cid), "CommandManager")
    if "actuators_list response timeout" in lowered:
        return DiagnosticRecord("ERR", ACT_004, msg.actuators_list_timeout(), "ActuatorManager")
    if "response timeout" in lowered:
        cid: int | str = "?"
        ms = 0
        if "command_id=" in lowered:
            cid = clean.split("command_id=", 1)[1].split(",")[0].strip()
        if "elapsed_limit_ms=" in lowered:
            try:
                ms = int(clean.rsplit("elapsed_limit_ms=", 1)[-1].strip())
            except ValueError:
                pass
        elif "within" in lowered and "ms" in lowered:
            try:
                ms = int(clean.rsplit("within", 1)[-1].strip().replace("ms", "").strip())
            except ValueError:
                pass
        return DiagnosticRecord(
            "ERR", CMD_001, msg.command_response_timeout(cid, ms), "CommandManager",
        )
    if "zero mechanisms" in lowered or "empty list" in lowered:
        return DiagnosticRecord("WARN", ACT_003, msg.actuators_list_empty(), "ActuatorManager")
    if "invalid actuators_list" in lowered:
        return DiagnosticRecord("ERR", ACT_005, msg.actuators_list_invalid(clean), "ActuatorManager")
    if "mechanism_count=" in lowered:
        try:
            count = int(clean.rsplit("mechanism_count=", 1)[-1].strip())
        except ValueError:
            count = 0
        return DiagnosticRecord("INFO", ACT_001, msg.actuators_loaded(count), "ActuatorManager")
    if "json decode" in lowered:
        return DiagnosticRecord("ERR", PROTO_001, msg.protocol_json_error(clean), "MessageProcessor")
    if "empty protocol line" in lowered:
        return DiagnosticRecord("ERR", PROTO_002, msg.protocol_empty_line(), "MessageProcessor")
    if "json object" in lowered:
        return DiagnosticRecord("ERR", PROTO_003, msg.protocol_not_object(), "MessageProcessor")
    if "message_type=command" in lowered and "not expected" in lowered:
        return DiagnosticRecord("ERR", PROTO_005, msg.protocol_unexpected_command(), "MessageProcessor")
    if "unknown message_type" in lowered:
        start = clean.rfind("=")
        mt = clean[start + 1 :].strip("'\"") if start >= 0 else clean
        return DiagnosticRecord("ERR", PROTO_006, msg.protocol_unknown_type(mt), "MessageProcessor")
    if "protocol validation" in lowered or "protocol message validation" in lowered:
        return DiagnosticRecord("ERR", PROTO_004, msg.protocol_validation_error(clean), "MessageProcessor")
    if "telemetry validation" in lowered:
        return DiagnosticRecord("WARN", TEL_001, clean, "TelemetryValidator")
    if "link established" in lowered or "pong received" in lowered:
        return DiagnosticRecord("INFO", LINK_002, msg.link_ready(), "LinkWatchdog")
    if "handshake" in lowered or "awaiting pong" in lowered:
        return DiagnosticRecord("INFO", LINK_001, msg.link_connecting(), "LinkWatchdog")
    if "cannot send ping" in lowered:
        return DiagnosticRecord(
            "ERR", LINK_003, msg.link_send_unavailable(), "LinkWatchdog",
        )
    if "link lost" in lowered or "no pong within" in lowered:
        reason = ""
        detail = clean
        if "phase=" in lowered:
            reason = clean.split("phase=", 1)[1].split(":", 1)[0].strip("'\"")
        return record_link_lost(detail, reason=reason, source=default_source)
    if "no pong after command" in lowered or (
        "command delivery" in lowered and "no pong" in lowered
    ):
        return record_command_link_failed(clean)
    if "status=accepted" in lowered or "status=completed" in lowered:
        return DiagnosticRecord("INFO", CMD_003, _format_response_detail_from_legacy(clean), "Controller")
    if "status=rejected" in lowered:
        return DiagnosticRecord("ERR", CMD_004, _format_response_detail_from_legacy(clean), "Controller")
    if "status=error" in lowered:
        return DiagnosticRecord("ERR", CMD_005, _format_response_detail_from_legacy(clean), "Controller")
    if "not connected" in lowered:
        transport = default_source if default_source.endswith("Transport") else "Transport"
        return DiagnosticRecord(
            "ERR", TRN_001, msg.transport_not_connected(transport), default_source,
        )
    if (
        "connection timed out after" in lowered
        or "connection refused at" in lowered
        or "network unreachable for" in lowered
        or "cannot resolve host name" in lowered
        or "operation timed out" in lowered
        or "errno 60" in lowered
    ):
        transport = "TcpTransport"
        if "mqtt" in lowered:
            transport = "MqttTransport"
        elif "gsm tcp" in lowered:
            transport = "TcpTransport"
        return DiagnosticRecord("ERR", TRN_003, clean, transport)
    if "missing dependency" in lowered or "i/o error" in lowered or "publish failed" in lowered:
        return record_transport_error(clean, default_source)
    if "invalid socket" in lowered:
        return record_transport_error(clean, default_source)
    if "send handler" in lowered and "actuators" in lowered:
        return DiagnosticRecord("ERR", ACT_006, msg.actuators_send_unavailable(), "ActuatorManager")
    if default_source.endswith("Transport"):
        return DiagnosticRecord("ERR", TRN_003, clean, default_source)
    return DiagnosticRecord("ERR", ACT_002, clean, default_source)


def _level_from_message(message: AppMessage) -> str:
    payload = message.payload or {}
    raw = payload.get("level")
    if raw is None:
        return "INFO"
    try:
        parsed = Level(str(raw))
    except ValueError:
        return "INFO"
    if parsed == Level.ERROR:
        return "ERR"
    if parsed == Level.WARNING:
        return "WARN"
    return "INFO"


def _format_response_detail(message: AppMessage) -> str:
    parts = [
        f"controller response status={message.status.value if message.status else '?'}",
    ]
    if message.command_id is not None:
        parts.append(f"command_id={message.command_id}")
    if message.actuator_id is not None:
        parts.append(f"actuator_id={message.actuator_id}")
    if message.message_id is not None:
        parts.append(f"message_id={message.message_id}")
    if message.error_code is not None:
        parts.append(f"wire_error_code={message.error_code}")
    if message.text:
        parts.append(
            f"text={msg.english_controller_description(message.text)!r}",
        )
    return ", ".join(parts)


def _format_response_detail_from_legacy(clean: str) -> str:
    return msg.strip_legacy_prefix(clean)


def _format_diagnostic_detail(message: AppMessage) -> str:
    parts = ["controller diagnostic"]
    if message.actuator_id is not None:
        parts.append(f"actuator_id={message.actuator_id}")
    if message.message_id is not None:
        parts.append(f"message_id={message.message_id}")
    if message.error_code is not None:
        parts.append(f"wire_error_code={message.error_code}")
    payload = message.payload or {}
    if payload.get("level") is not None:
        parts.append(f"level={payload['level']}")
    return ", ".join(parts)
