const DEFAULT_DEV_API_BASE_URL = "http://localhost:8000";
const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

function readBrowserRuntimeApiBaseUrl(): string | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }

  const runtimeConfig = (window as Window & {
    __PATENTIQ_RUNTIME_CONFIG__?: { apiBaseUrl?: unknown };
  }).__PATENTIQ_RUNTIME_CONFIG__;
  const runtimeApiBaseUrl =
    typeof runtimeConfig?.apiBaseUrl === "string" ? runtimeConfig.apiBaseUrl.trim() : "";
  return runtimeApiBaseUrl.length > 0 ? runtimeApiBaseUrl : undefined;
}

function resolveApiBaseUrl(): string {
  const runtimeApiBaseUrl = readBrowserRuntimeApiBaseUrl();
  if (runtimeApiBaseUrl) {
    return runtimeApiBaseUrl;
  }

  if (configuredApiBaseUrl && configuredApiBaseUrl.length > 0) {
    return configuredApiBaseUrl;
  }

  if (process.env.NODE_ENV !== "production") {
    return DEFAULT_DEV_API_BASE_URL;
  }

  throw new Error("NEXT_PUBLIC_API_BASE_URL is required for production builds and runtime.");
}

function rewriteLocalhostForBrowserBridge(value: string): string {
  if (typeof window === "undefined") {
    return value;
  }

  try {
    const currentHost = window.location.hostname;
    const url = new URL(value);
    if (
      currentHost === "host.docker.internal" &&
      (url.hostname === "127.0.0.1" || url.hostname === "localhost")
    ) {
      url.hostname = "host.docker.internal";
      return url.toString();
    }
  } catch {
    return value;
  }

  return value;
}

export function getApiBaseUrl(): string {
  return rewriteLocalhostForBrowserBridge(resolveApiBaseUrl()).replace(/\/$/, "");
}
