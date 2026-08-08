import React, { FormEvent, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { api, login, session } from "./api";
import "./styles.css";

type Summary = { total_submissions: number; by_widget: { widget_id: string; title: string; count: number }[]; by_country: { country: string; count: number }[] };

function LoginPage() {
  const [email, setEmail] = useState("alice@acme.test");
  const [password, setPassword] = useState("DemoPass123!");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { const result = await login(email, password); session.set(result.access_token); navigate("/dashboard"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Sign-in failed."); }
    finally { setBusy(false); }
  }
  return <main className="login-shell"><section className="login-card" aria-labelledby="login-title">
    <div className="wordmark">WidgetForge</div><h1 id="login-title">Welcome back</h1>
    <p>Manage the forms you embed and the leads they collect.</p>
    <form onSubmit={submit} noValidate><label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" /></label>
      <label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} required autoComplete="current-password" /></label>
      {error && <p className="form-error" role="alert">{error}</p>}<button className="button primary" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
    </form><p className="demo-note">Local demo credentials are prefilled.</p>
  </section></main>;
}

function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null); const [error, setError] = useState("");
  React.useEffect(() => { api<Summary>("/api/v1/dashboard/summary").then(setSummary).catch(e => setError(e.message)); }, []);
  if (error) return <section className="page"><h1>Dashboard</h1><p className="form-error">{error}</p></section>;
  if (!summary) return <section className="page"><p className="muted">Loading dashboard…</p></section>;
  const topCountry = summary.by_country[0]?.country ?? "No data";
  return <section className="page"><div className="page-heading"><div><p className="eyebrow">Overview</p><h1>Good morning</h1><p>Here is what your embedded forms have captured.</p></div><NavLink className="button primary" to="/widgets/new">Create widget</NavLink></div>
    <div className="metrics"><Metric label="Total submissions" value={summary.total_submissions} /><Metric label="Configured widgets" value={summary.by_widget.length} /><Metric label="Top country" value={topCountry} /></div>
    <section className="panel"><div className="panel-heading"><h2>Widget performance</h2><NavLink to="/widgets">View all widgets</NavLink></div>
      {summary.by_widget.length ? <table><thead><tr><th>Widget</th><th>Leads</th></tr></thead><tbody>{summary.by_widget.map(item => <tr key={item.widget_id}><td>{item.title}</td><td>{item.count}</td></tr>)}</tbody></table> : <p className="empty">Create a widget to start collecting leads.</p>}</section>
  </section>;
}
function Metric({ label, value }: { label: string; value: string | number }) { return <article className="metric"><p>{label}</p><strong>{value}</strong></article>; }
function Shell() { const navigate = useNavigate(); function logout() { session.clear(); navigate("/login"); }
  return <div className="app-shell"><aside><div className="wordmark">WidgetForge</div><nav><NavLink to="/dashboard">Overview</NavLink><NavLink to="/widgets">Widgets</NavLink><NavLink to="/submissions">Submissions</NavLink></nav><button className="logout" onClick={logout}>Sign out</button></aside><main className="content"><Routes><Route path="/dashboard" element={<Dashboard />} /><Route path="*" element={<section className="page"><h1>Coming next</h1><p>This screen is planned for UI Phase 2.</p></section>} /></Routes></main></div>; }
function Protected() { return session.get() ? <Shell /> : <Navigate to="/login" replace />; }
function App() { return <Routes><Route path="/login" element={session.get() ? <Navigate to="/dashboard" replace /> : <LoginPage />} /><Route path="/*" element={<Protected />} /></Routes>; }
createRoot(document.getElementById("root")!).render(<React.StrictMode><BrowserRouter><App /></BrowserRouter></React.StrictMode>);
