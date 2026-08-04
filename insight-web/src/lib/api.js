const baseUrl = import.meta.env.VITE_API_URL;

// a request is sent and the parsed json body is returned
async function request(path, options) {
  const res = await fetch(`${baseUrl}${path}`, options);
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return res.json();
}

// the interactions list is fetched
export function getInteractions() {
  return request('/interactions');
}

// a single interaction is fetched by id
export function getInteraction(id) {
  return request(`/interactions/${id}`);
}

// the recorded processing steps for an interaction are fetched
export function getSteps(id) {
  return request(`/interactions/${id}/steps`);
}

// a file is uploaded as multipart form data, with any extra fields appended
export function createInteraction(file, fields = {}) {
  const body = new FormData();
  body.append('file', file);
  Object.entries(fields).forEach(([key, value]) => body.append(key, value));
  return request('/interactions', { method: 'POST', body });
}

// the loaded schemas are fetched (id, version, fields, default flag)
export function getSchemas() {
  return request('/schemas');
}

// value counts for one schema, optionally filtered to one pipeline
export function getSchemaSummary(name, pipeline) {
  const params = new URLSearchParams();
  if (pipeline) params.set('pipeline', pipeline);
  return request(`/schemas/${name}/summary?${params}`);
}
