// frontend/src/api/client.js
// Generic wrappers around the new batch endpoints. Framework-agnostic on
// purpose (no React imports) so it works regardless of what src/ turns out
// to use.

const BASE_URL = "http://localhost:8000";

export async function uploadJson(entity, data) {
  const res = await fetch(`${BASE_URL}/api/upload-json`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entity, data }),
  });
  if (!res.ok) throw new Error(`upload-json failed: HTTP ${res.status}`);
  return res.json();
}

export async function getBatch(batchId) {
  const res = await fetch(`${BASE_URL}/api/batch/${batchId}`);
  if (!res.ok) throw new Error(`get batch failed: HTTP ${res.status}`);
  return res.json();
}

export async function listBatches(entity) {
  const url = entity
    ? `${BASE_URL}/api/batches?entity=${encodeURIComponent(entity)}`
    : `${BASE_URL}/api/batches`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`list batches failed: HTTP ${res.status}`);
  return res.json();
}

// onEvent receives parsed SSE event objects: {type, batch_id, ...}
export async function streamOperation(kind, batchIds, onEvent) {
  const path = kind === "validate" ? "/api/validate" : "/api/load";
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ batch_ids: batchIds }),
  });
  if (!res.ok) throw new Error(`${kind} failed: HTTP ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;
      try {
        onEvent(JSON.parse(trimmed.slice(6)));
      } catch {
        // ignore malformed line, keep streaming
      }
    }
  }
}
