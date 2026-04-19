const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8010/api";

const DEMO_EMAIL = "demo@smartfx.ai";
const DEMO_PASSWORD = "smartfxdemo";
const TOKEN_KEY = "smartfx_demo_token";
const USER_KEY = "smartfx_demo_user";

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
      plan: "free",
    }),
  });

  if (!response.ok) {
    throw new Error(`auth request failed: ${response.status}`);
  }

  return (await response.json()) as AuthResponse;
}

export async function ensureDemoAuth() {
  if (typeof window === "undefined") {
    throw new Error("demo auth is only available in the browser");
  }

  const cachedToken = window.localStorage.getItem(TOKEN_KEY);
  const cachedUser = window.localStorage.getItem(USER_KEY);
  if (cachedToken && cachedUser) {
    return {
      token: cachedToken,
      user: JSON.parse(cachedUser) as AuthResponse["user"],
    };
  }

  let payload: AuthResponse;
  try {
    payload = await postAuth("login");
  } catch {
    payload = await postAuth("register");
  }

  window.localStorage.setItem(TOKEN_KEY, payload.access_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(payload.user));

  return {
    token: payload.access_token,
    user: payload.user,
  };
}

export function getStoredDemoAuth() {
  if (typeof window === "undefined") {
    return null;
  }

  const token = window.localStorage.getItem(TOKEN_KEY);
  const user = window.localStorage.getItem(USER_KEY);
  if (!token || !user) {
    return null;
  }

  return {
    token,
    user: JSON.parse(user) as AuthResponse["user"],
  };
}
