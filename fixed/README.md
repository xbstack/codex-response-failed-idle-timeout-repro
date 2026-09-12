# Fixed-path verification

No official released Codex CLI fix was verified by XBSTACK as of 2026-09-12.

Upstream issue #43140 contains a proposed source patch, but this repository intentionally does not ship or label a patched Codex binary as an official fix.

When OpenAI publishes a new stable Codex CLI release, verify it with the same fixture:

1. `response.failed` followed by immediate EOF must preserve the original error.
2. `response.failed` followed by a still-open socket must also return the original terminal error promptly.
3. The second case must not surface `idle timeout waiting for SSE`.
4. Record the result in `version-matrix.md` before describing the release as fixed.

This directory exists to make the verification boundary explicit rather than implying that the current workaround is an upstream release.
