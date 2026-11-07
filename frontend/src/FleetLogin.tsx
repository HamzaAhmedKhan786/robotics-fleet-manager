import { useState } from "react";
import type { FormEvent } from "react";

export function FleetLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loggedIn, setLoggedIn] = useState(() => Boolean(sessionStorage.getItem("fleetos_access_token")));
  async function login(event: FormEvent) {
    event.preventDefault();
    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) throw new Error("Invalid credentials or identity service unavailable");
      const body = await response.json() as { access_token: string; role: string };
      sessionStorage.setItem("fleetos_access_token", body.access_token);
      sessionStorage.setItem("fleetos_role", body.role);
      setLoggedIn(true); setMessage(`Signed in as ${body.role}`);
      window.dispatchEvent(new Event("fleetos-auth-changed"));
      setPassword("");
    } catch (e) { setMessage(e instanceof Error ? e.message : "Login failed"); }
  }
  function logout() {
    sessionStorage.removeItem("fleetos_access_token");
    sessionStorage.removeItem("fleetos_role");
    setLoggedIn(false); setMessage("Signed out");
    window.dispatchEvent(new Event("fleetos-auth-changed"));
  }
  return <section style={{ padding: 16 }} aria-label="FleetOS login">
    {loggedIn ? <button type="button" onClick={logout}>Sign out</button> :
      <form onSubmit={event => void login(event)}>
        <label>Username <input value={username} autoComplete="username" onChange={e => setUsername(e.target.value)} required /></label>
        <label>Password <input type="password" value={password} autoComplete="current-password" onChange={e => setPassword(e.target.value)} required /></label>
        <button type="submit">Sign in</button>
      </form>}
    <span role="status">{message}</span>
  </section>;
}
