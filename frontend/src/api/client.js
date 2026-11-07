/**
 * Central API client. The service origin comes only from VITE_API_BASE_URL.
 */

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function baseUrl() {
  const value = import.meta.env.VITE_API_BASE_URL;
  if (!value || typeof value !== "string") {
    throw new ApiError(
      "VITE_API_BASE_URL is not set. Add it to the frontend environment before starting the app."
    );
  }
  return value.replace(/\/+$/, "");
}

function formatDetail(detail, fallback) {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (typeof item?.msg === "string" ? item.msg : ""))
      .filter(Boolean);
    if (messages.length) {
      return messages.join(" ");
    }
  }
  return fallback;
}

async function parseError(response) {
  const fallback = `Request failed (${response.status}).`;
  try {
    const body = await response.json();
    return formatDetail(body?.detail, fallback);
  } catch {
    return fallback;
  }
}

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${baseUrl()}${path}`, options);
  } catch {
    throw new ApiError(
      "Network error: the LUMINA API is unreachable. Check that the backend is running and that VITE_API_BASE_URL points at it."
    );
  }
  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }
  return response.json();
}

export function getHealth() {
  return request("/api/health");
}

export function getInfo() {
  return request("/api/info");
}

export function uploadImage(file) {
  const body = new FormData();
  body.append("file", file, file.name);
  return request("/api/upload", { method: "POST", body });
}

export function enhanceImage(file, method) {
  const body = new FormData();
  body.append("file", file, file.name);
  body.append("method", method);
  return request("/api/enhance", { method: "POST", body });
}

export function downloadEncodedImage({ imageBase64, mediaType, filename }) {
  const binary = atob(imageBase64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  const url = URL.createObjectURL(new Blob([bytes], { type: mediaType }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
