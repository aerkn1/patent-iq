import { getApiBaseUrl } from "@/lib/config";

export type ApiErrorPayload = {
  error?: {
    code?: string;
    message?: string;
  };
};

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  if (init?.body != null && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    if (isJson) {
      const payload = (await response.json()) as ApiErrorPayload;
      const detail = payload.error?.message ?? payload.error?.code;
      if (detail) {
        message = `${message}: ${detail}`;
      }
    }
    throw new Error(message);
  }

  if (!isJson) {
    throw new Error(`Expected JSON response for ${path}`);
  }

  return (await response.json()) as T;
}
