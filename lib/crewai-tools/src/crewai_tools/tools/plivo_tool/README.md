# Plivo Tools

## Description

These tools give a crewAI agent access to the Plivo communications APIs so a crew can reach people over the phone network. The set covers outbound messaging and voice plus read-only lookups.

- `PlivoSendSMSTool` sends a text message (SMS) to one or more numbers.
- `PlivoMakeCallTool` places an outbound voice call that follows a call flow returned by an answer URL.
- `PlivoMessageDetailsTool` retrieves the record for a message by its message UUID.
- `PlivoCallDetailsTool` retrieves the call detail record for a call by its call UUID.
- `PlivoNumberLookupTool` looks up a number to find its carrier, line type, country, and formatting.

## Installation

Install crewAI tools together with the Plivo SDK:

```shell
pip install 'crewai[tools]' plivo
```

A Plivo account provides the credentials the tools need. Create one and find the Auth ID and Auth Token on the [Plivo console](https://cx.plivo.com/?utm_source=github&utm_medium=oss&utm_campaign=crewai).

## Configuration

The tools read credentials and defaults from the environment:

- `PLIVO_AUTH_ID` and `PLIVO_AUTH_TOKEN` are required for every tool.
- `PLIVO_SRC_NUMBER` is the default sender number for `PlivoSendSMSTool`.
- `PLIVO_FROM_NUMBER` is the default caller number for `PlivoMakeCallTool`.
- `PLIVO_ANSWER_URL` is the default answer XML URL for `PlivoMakeCallTool`. When it is unset the tool uses a hosted default that reads a short message to the callee.

Each value can also be passed directly when constructing a tool.

## Example

```python
from crewai import Agent
from crewai_tools import PlivoSendSMSTool, PlivoMakeCallTool

send_sms = PlivoSendSMSTool(src="+14155550001")
make_call = PlivoMakeCallTool(
    from_="+14155550001",
    answer_url="https://example.com/answer.xml",
)

agent = Agent(
    role="Notifier",
    goal="Reach customers over SMS and voice",
    backstory="Keeps customers informed through Plivo.",
    tools=[send_sms, make_call],
)
```

An SMS is sent by calling the tool with a destination and a message:

```python
send_sms.run(dst="+14155550123", text="Your order has shipped.")
```

A call is placed by calling the tool with a destination. The answer URL controls what the callee hears:

```python
make_call.run(to_="+14155550123")
```

## Notes

Sending an SMS or placing a call returns a queued acknowledgement rather than a final delivery or answer status. Delivery and call outcomes are reported by Plivo through webhooks configured on the account, and the record tools report the state of a message or call once Plivo has processed it. A message record does not include the message body.
