# AGENTS.md — Plivo tools

Integration-specific context for anyone extending these tools.

## What this is

Five crewAI `BaseTool` subclasses that wrap the Plivo REST APIs through the official `plivo` Python SDK (`RestClient`). They live beside the other third-party provider tools (composio, zapier, firecrawl, brightdata) and follow that same pattern: declare `name`, `description`, `args_schema`, `env_vars`, and `package_dependencies`, then implement `_run(self, **kwargs)`.

## Scope and boundaries

- Outbound SMS is full-featured through `messages.create`.
- Outbound voice is full-featured through `calls.create` with an answer URL that returns Plivo answer XML.
- Inbound SMS and inbound voice are covered only by the read-only record tools (`messages.get`, `calls.get`). crewAI has no inbound server or webhook runtime, so there is no live inbound handler here. A real-time inbound flow belongs in a host that owns an HTTP server.
- Number lookup is read-only through `lookup.get`, which resolves a number's carrier, line type, country, and formatting.
- Real-time bidirectional audio streaming is out of scope because crewAI has no media or websocket transport.

## Contracts to preserve

- Base REST host is `https://api.plivo.com/v1/Account/{AUTH_ID}/`; auth is HTTP Basic with Auth ID and Auth Token. The console is `cx.plivo.com`, never `console.plivo.com`.
- SMS uses the parameter names `src`, `dst`, `text`. Multiple recipients are joined with `<`, not a comma or a list. A send returns HTTP 202 with a `message_uuid` list; success means queued, not delivered.
- Voice uses the parameter names `from_`, `to_`, `answer_url`. A create returns HTTP 201 with a `request_uuid`; success means the call was fired, not answered.
- Record responses expose fields as dynamic attributes, so read them with a default. A message record does not carry the message body.
- Lookup uses a separate host, `https://lookup.plivo.com/v1/Number/{number}?type=carrier`, not `api.plivo.com`. Only `type=carrier` is documented, so the tool relies on the SDK default. Carrier fields are best-effort and can be sparse for unallocated numbers.

## Dependency and packaging notes

- `plivo` is declared as the `plivo` optional extra in `pyproject.toml` and as `package_dependencies` on each tool. The import is lazy inside `_rest_client` so importing `crewai_tools` never requires `plivo` to be installed.
- After adding or changing a tool, regenerate `lib/crewai-tools/tool.specs.json` with the repo's spec generator rather than editing it by hand.

## If inbound is ever added

An inbound SMS webhook is signed under `X-Plivo-Signature-MA-V3` (messaging), not the plain `X-Plivo-Signature-V3` (voice style). Validating only the plain header rejects real inbound POSTs with HTTP 403 and Plivo error code 2403. That work needs a host with an HTTP server and does not belong in these outbound tools.
