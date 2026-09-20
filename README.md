# Codex CLI `response.failed` → `idle timeout waiting for SSE` reproduction

Independent XBSTACK reproduction of OpenAI Codex CLI issue #43140.

## What this reproduces

When an HTTP SSE server sends a terminal `response.failed` event and then keeps the socket open, Codex CLI can keep waiting for EOF until the configured stream idle timeout fires. The user-visible error then becomes `idle timeout waiting for SSE`, which hides the original server failure.

## Independent results

Tested on macOS with a local loopback HTTP server. No model, OpenAI/Azure API, credential, or external network service is used by the reproducer.

| Codex CLI | Server behavior | Original failure preserved | Idle timeout reported |
|---|---|---:|---:|
| 0.153.4 | close after `response.failed` | yes | no |
| 0.153.4 | keep socket open | no | yes |
| 0.154.0 | close after `response.failed` | yes | no |
| 0.154.0 | keep socket open | no | yes |
| 0.155.0-alpha.9.2 | close after `response.failed` | yes | no |
| 0.155.0-alpha.9.2 | keep socket open | no | yes |

The fixture uses an 800 ms stream idle timeout so the failure can be observed quickly.

## Run

```bash
python3 repro.py \
  --codex /Applications/ChatGPT.app/Contents/Resources/codex \
  --output logs/result-0.153.4.json
```

For another Codex executable:

```bash
python3 repro.py --codex /path/to/codex --output logs/result.json
```

## Expected behavior

Once a valid terminal `response.failed` event is received, the client should report that failure immediately rather than waiting for the underlying SSE socket to close.

## Observed behavior

If the fixture closes immediately after `response.failed`, Codex reports the original marker:

```text
stream disconnected before completion: XBSTACK_LOCAL_TERMINAL_FAILURE
```

If the fixture leaves the connection open, Codex reports:

```text
stream disconnected before completion: idle timeout waiting for SSE
```

and the original marker is no longer present in the user-visible error event.

## Scope

This repository confirms a client-side failure-handling shape. It does **not** claim that every Codex/Azure reconnect, `server_error`, or timeout is caused by this defect. Real upstream capacity, network, provider, and model failures must be diagnosed separately.

## Upstream

- OpenAI Codex issue: https://github.com/openai/codex/issues/43140
- OpenAI Codex releases: https://github.com/openai/codex/releases

## XBSTACK articles

- English: https://www.xbstack.com/en/ai/tools-lab/codex-response-failed-idle-timeout-sse/?utm_source=github&utm_medium=referral&utm_campaign=codex_response_failed_idle_timeout&utm_content=repository_readme&ref=github
- 中文: https://www.xbstack.com/ai/tools-lab/codex-response-failed-idle-timeout-sse/?utm_source=github&utm_medium=referral&utm_campaign=codex_response_failed_idle_timeout&utm_content=repository_readme_zh&ref=github
