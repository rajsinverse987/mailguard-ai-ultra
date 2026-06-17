"use client";

const TOKEN_KEY = "mailguard_token";

/** Tiny localStorage-backed auth helpers. */
export const auth = {
  getToken: () =>
    typeof window === "undefined" ? null : window.localStorage.getItem(TOKEN_KEY),
  setToken: (token: string) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(TOKEN_KEY, token);
    }
  },
  clear: () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(TOKEN_KEY);
    }
  },
  isLoggedIn: () => Boolean(auth.getToken()),
};
