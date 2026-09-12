# Version matrix

Test date: 2026-09-12

| Version | Source | `response.failed` + EOF | `response.failed` + open socket | Result |
|---|---|---|---|---|
| 0.153.4 | `/Applications/ChatGPT.app/Contents/Resources/codex` | original marker preserved | marker replaced by `idle timeout waiting for SSE` | affected |
| 0.154.0 | `@openai/codex@0.154.0` | original marker preserved | marker replaced by `idle timeout waiting for SSE` | affected |

Fixture settings:

- local loopback HTTP server
- HTTP 200 + `Content-Type: text/event-stream`
- terminal `response.failed` event with marker `XBSTACK_LOCAL_TERMINAL_FAILURE`
- `stream_idle_timeout_ms = 800`
- retries disabled
- isolated temporary `CODEX_HOME`
- no model/API credential/external network dependency

Upstream issue #43140 is still open as checked on 2026-09-12. The upstream issue contains a proposed source patch, but XBSTACK does not treat that patch as an official released fix until it is merged/released and independently verified in a published version.
