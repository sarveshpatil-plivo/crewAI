"""Plivo tools for sending SMS, placing voice calls, and fetching message or call records."""

from __future__ import annotations

import os
from typing import Any

from crewai.tools import BaseTool, EnvVar
from pydantic import BaseModel, Field


DEFAULT_ANSWER_URL = "https://s3.amazonaws.com/static.plivo.com/answer.xml"

MESSAGE_FIELDS = (
    "message_uuid",
    "from_number",
    "to_number",
    "message_direction",
    "message_state",
    "message_time",
    "message_type",
    "total_amount",
    "total_rate",
    "units",
    "carrier_fees",
    "error_code",
)

CALL_FIELDS = (
    "call_uuid",
    "from_number",
    "to_number",
    "call_direction",
    "call_duration",
    "call_state",
    "initiation_time",
    "answer_time",
    "end_time",
    "bill_duration",
    "billed_duration",
    "total_amount",
    "total_rate",
    "hangup_cause_code",
    "hangup_cause_name",
    "hangup_source",
)


def _rest_client(auth_id: str | None, auth_token: str | None) -> Any:
    resolved_id = auth_id or os.getenv("PLIVO_AUTH_ID")
    resolved_token = auth_token or os.getenv("PLIVO_AUTH_TOKEN")
    if not resolved_id or not resolved_token:
        raise ValueError(
            "PLIVO_AUTH_ID and PLIVO_AUTH_TOKEN must be set to use the Plivo tools"
        )
    try:
        from plivo import RestClient
    except ImportError as exc:
        raise ImportError(
            "`plivo` package not found, please run `uv add plivo`"
        ) from exc
    return RestClient(auth_id=resolved_id, auth_token=resolved_token)


def _record_to_dict(record: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: getattr(record, field, None) for field in fields}


class PlivoSendSMSToolSchema(BaseModel):
    """Input for PlivoSendSMSTool."""

    dst: str = Field(
        ...,
        description=(
            "Destination number in E.164 format, for example +14155550123. "
            "Reach several recipients by joining numbers with '<'."
        ),
    )
    text: str = Field(..., description="Body of the text message to send.")


class PlivoSendSMSTool(BaseTool):
    """Send an SMS through the Plivo Messages API."""

    name: str = "Send an SMS with Plivo"
    description: str = (
        "Send a text message (SMS) to one or more phone numbers through Plivo. "
        "Provide the destination number in E.164 format and the message body."
    )
    args_schema: type[BaseModel] = PlivoSendSMSToolSchema
    auth_id: str | None = None
    auth_token: str | None = None
    src: str | None = None
    env_vars: list[EnvVar] = Field(
        default_factory=lambda: [
            EnvVar(name="PLIVO_AUTH_ID", description="Plivo account Auth ID", required=True),
            EnvVar(
                name="PLIVO_AUTH_TOKEN",
                description="Plivo account Auth Token",
                required=True,
            ),
            EnvVar(
                name="PLIVO_SRC_NUMBER",
                description="Default Plivo sender number for outbound SMS",
                required=False,
            ),
        ]
    )
    package_dependencies: list[str] = Field(default_factory=lambda: ["plivo"])

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        dst = kwargs.get("dst")
        text = kwargs.get("text")
        if not dst or not text:
            raise ValueError("Both 'dst' and 'text' are required")

        src = kwargs.get("src") or self.src or os.getenv("PLIVO_SRC_NUMBER")
        if not src:
            raise ValueError(
                "A sender number is required; set 'src' or PLIVO_SRC_NUMBER"
            )

        client = _rest_client(self.auth_id, self.auth_token)
        response = client.messages.create(src=src, dst=dst, text=text)
        return {
            "message": getattr(response, "message", None),
            "message_uuid": getattr(response, "message_uuid", None),
            "api_id": getattr(response, "api_id", None),
        }


class PlivoMakeCallToolSchema(BaseModel):
    """Input for PlivoMakeCallTool."""

    to_: str = Field(
        ...,
        description="Destination number to call, in E.164 format, for example +14155550123.",
    )
    answer_url: str | None = Field(
        None,
        description=(
            "Publicly reachable URL that returns Plivo answer XML describing the call flow. "
            "When omitted, PLIVO_ANSWER_URL or the tool default is used."
        ),
    )


class PlivoMakeCallTool(BaseTool):
    """Place an outbound voice call through the Plivo Voice API."""

    name: str = "Make a phone call with Plivo"
    description: str = (
        "Place an outbound phone call through Plivo. The call connects the sender number to the "
        "destination and follows the call flow returned by the answer URL."
    )
    args_schema: type[BaseModel] = PlivoMakeCallToolSchema
    auth_id: str | None = None
    auth_token: str | None = None
    from_: str | None = None
    answer_url: str | None = None
    env_vars: list[EnvVar] = Field(
        default_factory=lambda: [
            EnvVar(name="PLIVO_AUTH_ID", description="Plivo account Auth ID", required=True),
            EnvVar(
                name="PLIVO_AUTH_TOKEN",
                description="Plivo account Auth Token",
                required=True,
            ),
            EnvVar(
                name="PLIVO_FROM_NUMBER",
                description="Default Plivo caller number for outbound calls",
                required=False,
            ),
            EnvVar(
                name="PLIVO_ANSWER_URL",
                description="Default answer XML URL for outbound calls",
                required=False,
            ),
        ]
    )
    package_dependencies: list[str] = Field(default_factory=lambda: ["plivo"])

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        to_ = kwargs.get("to_")
        if not to_:
            raise ValueError("'to_' is required")

        from_ = kwargs.get("from_") or self.from_ or os.getenv("PLIVO_FROM_NUMBER")
        if not from_:
            raise ValueError(
                "A caller number is required; set 'from_' or PLIVO_FROM_NUMBER"
            )

        answer_url = (
            kwargs.get("answer_url")
            or self.answer_url
            or os.getenv("PLIVO_ANSWER_URL")
            or DEFAULT_ANSWER_URL
        )

        client = _rest_client(self.auth_id, self.auth_token)
        response = client.calls.create(from_=from_, to_=to_, answer_url=answer_url)
        return {
            "message": getattr(response, "message", None),
            "request_uuid": getattr(response, "request_uuid", None),
            "api_id": getattr(response, "api_id", None),
        }


class PlivoMessageDetailsToolSchema(BaseModel):
    """Input for PlivoMessageDetailsTool."""

    message_uuid: str = Field(
        ...,
        description="Identifier of the message to retrieve, returned when the message was sent.",
    )


class PlivoMessageDetailsTool(BaseTool):
    """Retrieve the record for a Plivo message."""

    name: str = "Get Plivo message details"
    description: str = (
        "Retrieve the record for a Plivo message by its message UUID, including direction, "
        "state, and cost. The record does not include the message body."
    )
    args_schema: type[BaseModel] = PlivoMessageDetailsToolSchema
    auth_id: str | None = None
    auth_token: str | None = None
    env_vars: list[EnvVar] = Field(
        default_factory=lambda: [
            EnvVar(name="PLIVO_AUTH_ID", description="Plivo account Auth ID", required=True),
            EnvVar(
                name="PLIVO_AUTH_TOKEN",
                description="Plivo account Auth Token",
                required=True,
            ),
        ]
    )
    package_dependencies: list[str] = Field(default_factory=lambda: ["plivo"])

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        message_uuid = kwargs.get("message_uuid")
        if not message_uuid:
            raise ValueError("'message_uuid' is required")

        client = _rest_client(self.auth_id, self.auth_token)
        record = client.messages.get(message_uuid)
        return _record_to_dict(record, MESSAGE_FIELDS)


class PlivoCallDetailsToolSchema(BaseModel):
    """Input for PlivoCallDetailsTool."""

    call_uuid: str = Field(
        ...,
        description="Identifier of the call to retrieve, found in the Plivo console or a call webhook.",
    )


class PlivoCallDetailsTool(BaseTool):
    """Retrieve the record for a Plivo call."""

    name: str = "Get Plivo call details"
    description: str = (
        "Retrieve the call detail record for a Plivo call by its call UUID, including direction, "
        "state, duration, and cost."
    )
    args_schema: type[BaseModel] = PlivoCallDetailsToolSchema
    auth_id: str | None = None
    auth_token: str | None = None
    env_vars: list[EnvVar] = Field(
        default_factory=lambda: [
            EnvVar(name="PLIVO_AUTH_ID", description="Plivo account Auth ID", required=True),
            EnvVar(
                name="PLIVO_AUTH_TOKEN",
                description="Plivo account Auth Token",
                required=True,
            ),
        ]
    )
    package_dependencies: list[str] = Field(default_factory=lambda: ["plivo"])

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        call_uuid = kwargs.get("call_uuid")
        if not call_uuid:
            raise ValueError("'call_uuid' is required")

        client = _rest_client(self.auth_id, self.auth_token)
        record = client.calls.get(call_uuid)
        return _record_to_dict(record, CALL_FIELDS)
