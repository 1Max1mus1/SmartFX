const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8010/api";

const DEMO_EMAIL = "demo@smartfx.ai";
const DEMO_PASSWORD = "smartfxdemo";
const TOKEN_KEY = "smartfx_demo_token";
const USER_KEY = "smartfx_demo_user";
const EXPIRY_BUFFER_SECONDS = 60;

type AuthResponse = {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    plan: string;
    created_at: string;
  };
};

async function postAuth(path: "login" | "register") {
  const response = await fetch(`${API_BASE}/auth/${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: DEMO_EMAIL,
      password: DEMO_PASSWORD,
      plan: "pro",
    }),
  });

  if (!response.ok) {
    throw new Error(`auth request failed: ${response.status}`);
  }

  return (await response.json()) as AuthResponse;
}

function clearStoredDemoAuth() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

function decodeTokenPayload(token: string): { exp?: number } | null {
  try {
    const [payloadToken] = token.split(".", 1);
    if (!payloadToken) {
      return null;
    }

    const padded = payloadToken + "=".repeat((4 - (payloadToken.length % 4)) % 4);
    const normalized = padded.replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(window.atob(normalized)) as { exp?: number };
  } catch {
    return null;
  }
}

function isTokenUsable(token: string) {
  const payload = decodeTokenPayload(token);
  if (!payload?.exp) {
    return false;
  }

  const now = Math.floor(Date.now() / 1000);
  return payload.exp - now > EXPIRY_BUFFER_SECONDS;
}

function persistAuth(payload: AuthResponse) {
  window.localStorage.setItem(TOKEN_KEY, payload.access_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
}

export async function ensureDemoAuth(forceRefresh = false) {
  if (typeof window === "undefined") {
    throw new Error("demo auth is only available in the browser");
  }

  if (!forceRefresh) {
    const cachedToken = window.localStorage.getItem(TOKEN_KEY);
    const cachedUser = window.localStorage.getItem(USER_KEY);
    if (cachedToken && cachedUser && isTokenUsable(cachedToken)) {
      return {
        token: cachedToken,
        user: JSON.parse(cachedUser) as AuthResponse["user"],
      };
    }
  }

  clearStoredDemoAuth();

  let payload: AuthResponse;
  try {
    payload = await postAuth("login");
  } catch {
    payload = await postAuth("register");
  }

  persistAuth(payload);

  return {
    token: payload.access_token,
    user: payload.user,
  };
}

export async function authorizedDemoFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const buildInit = (token: string): RequestInit => {
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${token}`);
    return {
      ...init,
      headers,
    };
  };

  let { token } = await ensureDemoAuth();
  let response = await fetch(input, buildInit(token));

  if (response.status !== 401) {
    return response;
  }

  ({ token } = await ensureDemoAuth(true));
  response = await fetch(input, buildInit(token));
  return response;
}

export function getStoredDemoAuth() {
  if (typeof window === "undefined") {
    return null;
  }

  const token = window.localStorage.getItem(TOKEN_KEY);
  const user = window.localStorage.getItem(USER_KEY);
  if (!token || !user || !isTokenUsable(token)) {
    clearStoredDemoAuth();
    return null;
  }

  return {
    token,
    user: JSON.parse(user) as AuthResponse["user"],
  };
}
