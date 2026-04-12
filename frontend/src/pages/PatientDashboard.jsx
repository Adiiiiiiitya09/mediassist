import { useState, useEffect } from "react";

const API = "http://localhost:8000";

const token = () => localStorage.getItem("token");

const api = async (path, opts = {}) => {
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: { Authorization: `Bearer ${token()}`, "Content-Type": "application/json", ...opts.headers },
  });
  if (!res.ok) throw await res.json();
  return res.json();
};

// ── colour helpers ──────────────────────────────────────────
const tierColor = (tier) =>
  ({ High: "#16a34a", Medium: "#d97706", Low: "#dc2626" }[tier] ?? "#6b7280");

const statusBadge = (status) => {
  const map = {
    pending: { bg: "#fef3c7", color: "#92400e", label: "Awaiting Doctor" },
    approved: { bg: "#d1fae5", color: "#065f46", label: "Approved" },
    rejected: { bg: "#fee2e2", color: "#991b1b", label: "Rejected" },
  };
  return map[status] ?? { bg: "#f3f4f6", color: "#374151", label: status };
};

// ── tiny components ─────────────────────────────────────────
const Badge = ({ status }) => {
  const s = statusBadge(status);
  return (
    <span style={{ background: s.bg, color: s.color, padding: "2px 10px", borderRadius: 20, fontSize: 12, fontWeight: 600 }}>
      {s.label}
    </span>
  );
};

const Pill = ({ label, value }) =>
  value ? (
    <div style={{ display: "flex", gap: 8, alignItems: "flex-start", marginBottom: 8 }}>
      <span style={{ color: "#6b7280", fontSize: 13, minWidth: 140, flexShrink: 0 }}>{label}</span>
      <span style={{ color: "#111827", fontSize: 13, fontWeight: 500 }}>{value}</span>
    </div>
  ) : null;

const Section = ({ title, children }) => (
  <div style={{ marginBottom: 24 }}>
    <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: "#9ca3af", textTransform: "uppercase", marginBottom: 10 }}>
      {title}
    </p>
    {children}
  </div>
);

// ── PROFILE EDITOR ───────────────────────────────────────────
function ProfileEditor({ profile, onSave, onClose }) {
  const [form, setForm] = useState({ ...profile });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const save = async () => {
    setSaving(true);
    try {
      await api("/patient/profile", { method: "PUT", body: JSON.stringify(form) });
      setMsg("Saved!");
      onSave();
      setTimeout(onClose, 800);
    } catch {
      setMsg("Save failed.");
    } finally {
      setSaving(false);
    }
  };

  const Field = ({ label, k, type = "text", options }) => (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: "block", fontSize: 12, color: "#6b7280", marginBottom: 4 }}>{label}</label>
      {options ? (
        <select value={form[k] ?? ""} onChange={(e) => set(k, e.target.value)} style={inputStyle}>
          <option value="">— select —</option>
          {options.map((o) => <option key={o}>{o}</option>)}
        </select>
      ) : (
        <input type={type} value={form[k] ?? ""} onChange={(e) => set(k, e.target.value)} style={inputStyle} />
      )}
    </div>
  );

  const inputStyle = {
    width: "100%", padding: "8px 12px", border: "1px solid #e5e7eb",
    borderRadius: 8, fontSize: 14, color: "#111827", background: "#fff", boxSizing: "border-box",
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ background: "#fff", borderRadius: 16, width: "100%", maxWidth: 600, maxHeight: "90vh", overflow: "auto", padding: 32, position: "relative" }}>
        <button onClick={onClose} style={{ position: "absolute", top: 16, right: 20, background: "none", border: "none", fontSize: 22, cursor: "pointer", color: "#9ca3af" }}>✕</button>
        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24, color: "#111827" }}>Edit Medical Profile</h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
          <Field label="Age" k="age" type="number" />
          <Field label="Gender" k="gender" options={["male", "female", "other"]} />
          <Field label="Blood Group" k="blood_group" options={["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]} />
          <Field label="Height (cm)" k="height_cm" type="number" />
          <Field label="Weight (kg)" k="weight_kg" type="number" />
          <Field label="Smoking" k="smoking" options={["never", "former", "current"]} />
          <Field label="Alcohol" k="alcohol" options={["never", "occasional", "regular"]} />
          <Field label="Exercise" k="exercise" options={["sedentary", "moderate", "active"]} />
        </div>

        <div style={{ marginBottom: 14 }}>
          <label style={{ display: "block", fontSize: 12, color: "#6b7280", marginBottom: 4 }}>Chronic Conditions</label>
          <textarea value={form.chronic_conditions ?? ""} onChange={(e) => set("chronic_conditions", e.target.value)}
            placeholder="e.g. Diabetes Type 2, Hypertension" rows={2}
            style={{ ...inputStyle, resize: "vertical" }} />
        </div>
        <div style={{ marginBottom: 14 }}>
          <label style={{ display: "block", fontSize: 12, color: "#6b7280", marginBottom: 4 }}>Past Surgeries</label>
          <textarea value={form.past_surgeries ?? ""} onChange={(e) => set("past_surgeries", e.target.value)}
            placeholder="e.g. Appendectomy 2018" rows={2}
            style={{ ...inputStyle, resize: "vertical" }} />
        </div>
        <div style={{ marginBottom: 14 }}>
          <label style={{ display: "block", fontSize: 12, color: "#6b7280", marginBottom: 4 }}>Current Medications</label>
          <textarea value={form.current_medications ?? ""} onChange={(e) => set("current_medications", e.target.value)}
            placeholder="e.g. Metformin 500mg" rows={2}
            style={{ ...inputStyle, resize: "vertical" }} />
        </div>
        <div style={{ marginBottom: 14 }}>
          <label style={{ display: "block", fontSize: 12, color: "#6b7280", marginBottom: 4 }}>Known Allergies</label>
          <input value={form.known_allergies ?? ""} onChange={(e) => set("known_allergies", e.target.value)}
            placeholder="e.g. Penicillin, Dust" style={inputStyle} />
        </div>
        <div style={{ marginBottom: 14 }}>
          <label style={{ display: "block", fontSize: 12, color: "#6b7280", marginBottom: 4 }}>Family History</label>
          <textarea value={form.family_history ?? ""} onChange={(e) => set("family_history", e.target.value)}
            placeholder="e.g. Father - Heart disease, Mother - Diabetes" rows={2}
            style={{ ...inputStyle, resize: "vertical" }} />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
          <Field label="Emergency Contact Name" k="emergency_contact_name" />
          <Field label="Emergency Contact Phone" k="emergency_contact_phone" />
        </div>

        {msg && <p style={{ color: msg === "Saved!" ? "#16a34a" : "#dc2626", fontSize: 13, marginTop: 8 }}>{msg}</p>}

        <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
          <button onClick={onClose} style={{ flex: 1, padding: "10px 0", background: "#f3f4f6", border: "none", borderRadius: 8, fontWeight: 600, cursor: "pointer", color: "#374151" }}>Cancel</button>
          <button onClick={save} disabled={saving} style={{ flex: 2, padding: "10px 0", background: "#2563eb", border: "none", borderRadius: 8, fontWeight: 600, cursor: "pointer", color: "#fff" }}>
            {saving ? "Saving…" : "Save Profile"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── CASE DETAIL VIEW ─────────────────────────────────────────
function CaseDetail({ consultationId, onBack }) {
  const [data, setData] = useState(null);
  const [tab, setTab] = useState("summary");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api(`/consultation/report/${consultationId}`)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [consultationId]);

  if (loading) return <div style={{ padding: 40, textAlign: "center", color: "#9ca3af" }}>Loading case…</div>;
  if (!data) return <div style={{ padding: 40, textAlign: "center", color: "#dc2626" }}>Could not load report.</div>;

  const tabs = ["summary", "symptoms", "transcript", "doctor"];

  return (
    <div>
      {/* Back */}
      <button onClick={onBack} style={{ background: "none", border: "none", color: "#2563eb", cursor: "pointer", fontSize: 14, fontWeight: 600, marginBottom: 20, padding: 0 }}>
        ← Back to dashboard
      </button>

      {/* Header card */}
      <div style={{ background: "#fff", borderRadius: 16, border: "1px solid #e5e7eb", padding: "24px 28px", marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
          <div>
            <p style={{ fontSize: 12, color: "#9ca3af", marginBottom: 4 }}>Case #{data.consultation_id} · {new Date(data.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}</p>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: "#111827", marginBottom: 8 }}>{data.chief_complaint || "Consultation"}</h2>
            <Badge status={data.status} />
          </div>
          {data.confidence_tier && (
            <div style={{ textAlign: "right" }}>
              <p style={{ fontSize: 12, color: "#9ca3af", marginBottom: 2 }}>ML Confidence</p>
              <p style={{ fontSize: 28, fontWeight: 800, color: tierColor(data.confidence_tier) }}>{data.confidence_score}%</p>
              <p style={{ fontSize: 12, color: tierColor(data.confidence_tier), fontWeight: 600 }}>{data.confidence_tier} confidence</p>
            </div>
          )}
        </div>

        {data.vital_flags?.length > 0 && (
          <div style={{ marginTop: 16, padding: "10px 14px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8 }}>
            <p style={{ fontSize: 12, fontWeight: 700, color: "#dc2626", marginBottom: 4 }}>⚠ Vital Flags</p>
            {data.vital_flags.map((f, i) => <p key={i} style={{ fontSize: 13, color: "#7f1d1d" }}>{f}</p>)}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 20, background: "#f3f4f6", padding: 4, borderRadius: 10, width: "fit-content" }}>
        {tabs.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            style={{
              padding: "7px 18px", borderRadius: 7, border: "none", cursor: "pointer", fontWeight: 600, fontSize: 13,
              background: tab === t ? "#fff" : "transparent", color: tab === t ? "#111827" : "#6b7280",
              boxShadow: tab === t ? "0 1px 3px rgba(0,0,0,0.1)" : "none"
            }}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
            {t === "doctor" && data.doctor_notes && " ✓"}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{ background: "#fff", borderRadius: 16, border: "1px solid #e5e7eb", padding: "24px 28px" }}>

        {tab === "summary" && (
          <div>
            <Section title="Medical History">
              {data.medical_history?.length ? data.medical_history.map((h, i) => <p key={i} style={{ fontSize: 13, color: "#374151", marginBottom: 4 }}>• {h}</p>) : <p style={{ fontSize: 13, color: "#9ca3af" }}>None reported</p>}
            </Section>
            <Section title="Current Medications">
              {data.current_medications?.length ? data.current_medications.map((m, i) => <p key={i} style={{ fontSize: 13, color: "#374151", marginBottom: 4 }}>• {m}</p>) : <p style={{ fontSize: 13, color: "#9ca3af" }}>None reported</p>}
            </Section>
            <Section title="Allergies">
              {data.allergies?.length ? data.allergies.map((a, i) => <p key={i} style={{ fontSize: 13, color: "#374151", marginBottom: 4 }}>• {a}</p>) : <p style={{ fontSize: 13, color: "#9ca3af" }}>None reported</p>}
            </Section>
          </div>
        )}

        {tab === "symptoms" && (
          <div>
            <Section title="Primary Symptoms">
              {data.symptoms?.length ? data.symptoms.map((s, i) => (
                <div key={i} style={{ background: "#f9fafb", borderRadius: 10, padding: "12px 16px", marginBottom: 10 }}>
                  <p style={{ fontWeight: 700, fontSize: 14, color: "#111827", marginBottom: 6 }}>{s.name}</p>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
                    <Pill label="Severity" value={s.severity ? `${s.severity}/10` : null} />
                    <Pill label="Duration" value={s.duration} />
                    <Pill label="Type" value={s.type} />
                    {s.triggers?.length > 0 && <Pill label="Triggers" value={s.triggers.join(", ")} />}
                    {s.relieving_factors?.length > 0 && <Pill label="Relief" value={s.relieving_factors.join(", ")} />}
                  </div>
                </div>
              )) : <p style={{ fontSize: 13, color: "#9ca3af" }}>No symptoms recorded</p>}
            </Section>
            {data.associated_symptoms?.length > 0 && (
              <Section title="Associated Symptoms">
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {data.associated_symptoms.map((s, i) => (
                    <span key={i} style={{ background: "#eff6ff", color: "#1d4ed8", padding: "4px 12px", borderRadius: 20, fontSize: 13, fontWeight: 500 }}>{s}</span>
                  ))}
                </div>
              </Section>
            )}
          </div>
        )}

        {tab === "transcript" && (
          <div style={{ maxHeight: 500, overflowY: "auto" }}>
            {data.transcript?.map((m, i) => (
              <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start", marginBottom: 12 }}>
                <div style={{
                  maxWidth: "75%", padding: "10px 14px", borderRadius: m.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                  background: m.role === "user" ? "#2563eb" : "#f3f4f6",
                  color: m.role === "user" ? "#fff" : "#111827", fontSize: 14, lineHeight: 1.5
                }}>
                  {m.content}
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "doctor" && (
          <div>
            {data.doctor_notes ? (
              <>
                {data.approved_at && (
                  <p style={{ fontSize: 12, color: "#9ca3af", marginBottom: 20 }}>
                    Reviewed on {new Date(data.approved_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}
                  </p>
                )}
                <Section title="Doctor's Notes">
                  <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 10, padding: "14px 18px" }}>
                    <p style={{ fontSize: 14, color: "#14532d", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{data.doctor_notes}</p>
                  </div>
                </Section>
                {data.prescription && (
                  <Section title="Prescription">
                    <div style={{ background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 10, padding: "14px 18px" }}>
                      <p style={{ fontSize: 14, color: "#1e3a8a", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{data.prescription}</p>
                    </div>
                  </Section>
                )}
              </>
            ) : (
              <div style={{ textAlign: "center", padding: "40px 0", color: "#9ca3af" }}>
                <p style={{ fontSize: 32, marginBottom: 12 }}>⏳</p>
                <p style={{ fontWeight: 600, color: "#374151" }}>Awaiting doctor review</p>
                <p style={{ fontSize: 13, marginTop: 4 }}>Your case has been submitted. A doctor will review it shortly.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── MAIN DASHBOARD ────────────────────────────────────────────
export default function PatientDashboard() {
  const [view, setView] = useState("dashboard");  // dashboard | case | editProfile
  const [selectedCase, setSelectedCase] = useState(null);
  const [profile, setProfile] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showProfileEditor, setShowProfileEditor] = useState(false);
  const [actionMenuOpen, setActionMenuOpen] = useState(null); // consultation_id or null

  const load = async () => {
    setLoading(true);
    try {
      const [p, h] = await Promise.all([
        api("/patient/profile"),
        api("/consultation/history"),
      ]);
      setProfile(p);
      setHistory(h);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token()) {
      window.location.href = "/patient-login";
      return;
    }

    load();
  }, []);

  useEffect(() => {
    const handleClickOutside = () => setActionMenuOpen(null);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const openCase = (id) => { setSelectedCase(id); setView("case"); };

  const deleteConsultation = async (consultationId) => {
    if (!confirm("Are you sure you want to delete this consultation? This action cannot be undone.")) return;
    try {
      await api(`/consultation/${consultationId}`, { method: "DELETE" });
      load(); // Reload the history
      setActionMenuOpen(null);
    } catch (e) {
      alert("Failed to delete consultation");
    }
  };

  const generateReport = async (consultationId) => {
    try {
      const report = await api(`/consultation/download-report/${consultationId}`);
      // Create and download the report file
      const blob = new Blob([report.content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = report.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setActionMenuOpen(null);
    } catch (e) {
      alert("Report not available yet or failed to generate");
    }
  };

  const reconsult = async (consultationId) => {
    try {
      const result = await api(`/consultation/reconsult/${consultationId}`, { method: "POST" });
      // Redirect to the new consultation
      window.location.href = `/patient/consultation?continue=${result.consultation_id}`;
      setActionMenuOpen(null);
    } catch (e) {
      alert("Failed to start reconsultation");
    }
  };

  if (loading) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f9fafb" }}>
      <div style={{ textAlign: "center", color: "#9ca3af" }}>
        <div style={{ width: 40, height: 40, border: "3px solid #e5e7eb", borderTopColor: "#2563eb", borderRadius: "50%", margin: "0 auto 16px", animation: "spin 0.8s linear infinite" }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        <p>Loading your dashboard…</p>
      </div>
    </div>
  );

  const stats = {
    total: history.length,
    approved: history.filter((h) => h.status === "approved").length,
    pending: history.filter((h) => h.status === "pending").length,
  };

  // BMI calc
  const bmi = profile?.height_cm && profile?.weight_kg
    ? (profile.weight_kg / Math.pow(profile.height_cm / 100, 2)).toFixed(1)
    : null;

  return (
    <div style={{ minHeight: "100vh", background: "#f9fafb", fontFamily: "'Segoe UI', system-ui, sans-serif" }}>
      {/* Top nav */}
      <div style={{ background: "#fff", borderBottom: "1px solid #e5e7eb", padding: "0 32px", display: "flex", alignItems: "center", justifyContent: "space-between", height: 60 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 20 }}>🏥</span>
          <span style={{ fontWeight: 700, fontSize: 18, color: "#111827" }}>MediAssist</span>
          <span style={{ color: "#d1d5db", marginLeft: 8 }}>|</span>
          <span style={{ fontSize: 14, color: "#6b7280", marginLeft: 8 }}>Patient Portal</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 34, height: 34, borderRadius: "50%", background: "#dbeafe", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 14, color: "#1d4ed8" }}>
            {profile?.name?.charAt(0).toUpperCase() ?? "P"}
          </div>
          <span style={{ fontSize: 14, fontWeight: 600, color: "#374151" }}>{profile?.name}</span>
          <button onClick={() => { localStorage.removeItem("token"); window.location.href = "/patient-login"; }}
            style={{ padding: "6px 12px", background: "#dc2626", color: "#fff", border: "none", borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: "pointer" }}>
            Logout
          </button>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 24px" }}>

        {view === "case" ? (
          <CaseDetail consultationId={selectedCase} onBack={() => setView("dashboard")} />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 24, alignItems: "start" }}>

            {/* ── LEFT: Profile card ─────────────────────────── */}
            <div>
              {/* Profile card */}
              <div style={{ background: "#fff", borderRadius: 16, border: "1px solid #e5e7eb", padding: 24, marginBottom: 16 }}>
                <div style={{ textAlign: "center", marginBottom: 20 }}>
                  <div style={{ width: 64, height: 64, borderRadius: "50%", background: "#dbeafe", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: 26, color: "#1d4ed8", margin: "0 auto 12px" }}>
                    {profile?.name?.charAt(0).toUpperCase() ?? "P"}
                  </div>
                  <p style={{ fontWeight: 700, fontSize: 17, color: "#111827" }}>{profile?.name}</p>
                  <p style={{ fontSize: 13, color: "#9ca3af" }}>{profile?.email}</p>
                  <p style={{ fontSize: 12, color: "#d1d5db", marginTop: 2 }}>Member since {profile?.created_at ? new Date(profile.created_at).getFullYear() : "—"}</p>
                </div>

                <div style={{ borderTop: "1px solid #f3f4f6", paddingTop: 16, marginBottom: 16 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                    {[
                      { label: "Age", value: profile?.age ? `${profile.age} yrs` : null },
                      { label: "Gender", value: profile?.gender },
                      { label: "Blood", value: profile?.blood_group },
                      { label: "BMI", value: bmi },
                    ].map(({ label, value }) => (
                      <div key={label} style={{ background: "#f9fafb", borderRadius: 8, padding: "8px 10px", textAlign: "center" }}>
                        <p style={{ fontSize: 11, color: "#9ca3af", marginBottom: 2 }}>{label}</p>
                        <p style={{ fontSize: 14, fontWeight: 700, color: "#111827" }}>{value ?? "—"}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {profile?.chronic_conditions && (
                  <div style={{ marginBottom: 12 }}>
                    <p style={{ fontSize: 11, color: "#9ca3af", marginBottom: 4, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>Conditions</p>
                    <p style={{ fontSize: 13, color: "#374151" }}>{profile.chronic_conditions}</p>
                  </div>
                )}
                {profile?.known_allergies && (
                  <div style={{ marginBottom: 12 }}>
                    <p style={{ fontSize: 11, color: "#9ca3af", marginBottom: 4, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>Allergies</p>
                    <p style={{ fontSize: 13, color: "#dc2626" }}>{profile.known_allergies}</p>
                  </div>
                )}

                <button onClick={() => setShowProfileEditor(true)}
                  style={{ width: "100%", padding: "9px 0", background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 8, color: "#1d4ed8", fontWeight: 600, fontSize: 13, cursor: "pointer" }}>
                  Edit Medical Profile
                </button>
              </div>

              {/* Stats */}
              <div style={{ background: "#fff", borderRadius: 16, border: "1px solid #e5e7eb", padding: 20 }}>
                <p style={{ fontSize: 12, fontWeight: 700, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>Activity</p>
                {[
                  { label: "Total Cases", value: stats.total, color: "#2563eb" },
                  { label: "Approved", value: stats.approved, color: "#16a34a" },
                  { label: "Pending", value: stats.pending, color: "#d97706" },
                ].map(({ label, value, color }) => (
                  <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                    <span style={{ fontSize: 13, color: "#6b7280" }}>{label}</span>
                    <span style={{ fontSize: 16, fontWeight: 700, color }}>{value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* ── RIGHT: Case history ────────────────────────── */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h1 style={{ fontSize: 22, fontWeight: 700, color: "#111827" }}>My Medical Cases</h1>
                <a href="/patient/consultation" style={{ padding: "9px 20px", background: "#2563eb", color: "#fff", borderRadius: 8, fontWeight: 600, fontSize: 13, textDecoration: "none" }}>
                  + New Consultation
                </a>
              </div>

              {history.length === 0 ? (
                <div style={{ background: "#fff", borderRadius: 16, border: "1px solid #e5e7eb", padding: "60px 40px", textAlign: "center" }}>
                  <p style={{ fontSize: 40, marginBottom: 12 }}>🩺</p>
                  <p style={{ fontWeight: 600, color: "#374151", fontSize: 16 }}>No consultations yet</p>
                  <p style={{ fontSize: 13, color: "#9ca3af", marginTop: 4 }}>Start your first AI-assisted consultation to get medical insights.</p>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {history.map((c) => (
                    <div key={c.consultation_id}
                      style={{ background: "#fff", borderRadius: 14, border: "1px solid #e5e7eb", padding: "18px 22px", position: "relative", transition: "box-shadow 0.15s, border-color 0.15s" }}
                      onMouseEnter={(e) => { e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,0,0,0.08)"; e.currentTarget.style.borderColor = "#93c5fd"; }}
                      onMouseLeave={(e) => { e.currentTarget.style.boxShadow = "none"; e.currentTarget.style.borderColor = "#e5e7eb"; }}>

                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div style={{ flex: 1, cursor: "pointer" }} onClick={() => openCase(c.consultation_id)}>
                          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                            <p style={{ fontWeight: 700, fontSize: 15, color: "#111827" }}>{c.chief_complaint}</p>
                            <Badge status={c.status} />
                            {c.has_doctor_response && (
                              <span style={{ background: "#d1fae5", color: "#065f46", padding: "2px 8px", borderRadius: 20, fontSize: 11, fontWeight: 600 }}>Doctor replied</span>
                            )}
                          </div>
                          <p style={{ fontSize: 12, color: "#9ca3af" }}>
                            Case #{c.consultation_id} · {new Date(c.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                          </p>
                        </div>

                        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                          {c.confidence_score != null && (
                            <div style={{ textAlign: "right" }}>
                              <p style={{ fontSize: 11, color: "#9ca3af" }}>ML Score</p>
                              <p style={{ fontSize: 16, fontWeight: 700, color: tierColor(c.confidence_tier) }}>{c.confidence_score}%</p>
                            </div>
                          )}

                          {/* Action Menu Button */}
                          <div style={{ position: "relative" }}>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setActionMenuOpen(actionMenuOpen === c.consultation_id ? null : c.consultation_id);
                              }}
                              style={{
                                background: "none",
                                border: "none",
                                cursor: "pointer",
                                padding: "4px",
                                borderRadius: 4,
                                color: "#6b7280"
                              }}
                              onMouseEnter={(e) => e.currentTarget.style.background = "#f3f4f6"}
                              onMouseLeave={(e) => e.currentTarget.style.background = "none"}
                            >
                              ⋮
                            </button>

                            {/* Action Menu */}
                            {actionMenuOpen === c.consultation_id && (
                              <div style={{
                                position: "absolute",
                                right: 0,
                                top: "100%",
                                background: "#fff",
                                border: "1px solid #e5e7eb",
                                borderRadius: 8,
                                boxShadow: "0 10px 15px -3px rgba(0,0,0,0.1)",
                                zIndex: 10,
                                minWidth: 140
                              }}>
                                <button
                                  onClick={(e) => { e.stopPropagation(); openCase(c.consultation_id); setActionMenuOpen(null); }}
                                  style={{
                                    width: "100%",
                                    padding: "8px 12px",
                                    background: "none",
                                    border: "none",
                                    textAlign: "left",
                                    cursor: "pointer",
                                    fontSize: 13,
                                    color: "#374151"
                                  }}
                                  onMouseEnter={(e) => e.currentTarget.style.background = "#f9fafb"}
                                  onMouseLeave={(e) => e.currentTarget.style.background = "none"}
                                >
                                  👁 View Details
                                </button>

                                <button
                                  onClick={(e) => { e.stopPropagation(); if (!c.interview_complete) return; generateReport(c.consultation_id); }}
                                  disabled={!c.interview_complete}
                                  style={{
                                    width: "100%",
                                    padding: "8px 12px",
                                    background: "none",
                                    border: "none",
                                    textAlign: "left",
                                    cursor: c.interview_complete ? "pointer" : "not-allowed",
                                    fontSize: 13,
                                    color: c.interview_complete ? "#374151" : "#9ca3af",
                                    opacity: c.interview_complete ? 1 : 0.65
                                  }}
                                  onMouseEnter={(e) => { if (c.interview_complete) e.currentTarget.style.background = "#f9fafb" }}
                                  onMouseLeave={(e) => { if (c.interview_complete) e.currentTarget.style.background = "none" }}
                                >
                                  📄 Generate Report
                                </button>

                                <button
                                  onClick={(e) => { e.stopPropagation(); if (!c.interview_complete) return; reconsult(c.consultation_id); }}
                                  disabled={!c.interview_complete}
                                  style={{
                                    width: "100%",
                                    padding: "8px 12px",
                                    background: "none",
                                    border: "none",
                                    textAlign: "left",
                                    cursor: c.interview_complete ? "pointer" : "not-allowed",
                                    fontSize: 13,
                                    color: c.interview_complete ? "#374151" : "#9ca3af",
                                    opacity: c.interview_complete ? 1 : 0.65
                                  }}
                                  onMouseEnter={(e) => { if (c.interview_complete) e.currentTarget.style.background = "#f9fafb" }}
                                  onMouseLeave={(e) => { if (c.interview_complete) e.currentTarget.style.background = "none" }}
                                >
                                  🔄 Reconsult
                                </button>

                                <div style={{ borderTop: "1px solid #f3f4f6", margin: "4px 0" }}></div>

                                <button
                                  onClick={(e) => { e.stopPropagation(); deleteConsultation(c.consultation_id); }}
                                  style={{
                                    width: "100%",
                                    padding: "8px 12px",
                                    background: "none",
                                    border: "none",
                                    textAlign: "left",
                                    cursor: "pointer",
                                    fontSize: 13,
                                    color: "#dc2626"
                                  }}
                                  onMouseEnter={(e) => e.currentTarget.style.background = "#fef2f2"}
                                  onMouseLeave={(e) => e.currentTarget.style.background = "none"}
                                >
                                  🗑 Delete
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {!c.interview_complete && (
                        <div style={{ marginTop: 10, padding: "6px 12px", background: "#fef3c7", borderRadius: 6, display: "inline-block" }}>
                          <p style={{ fontSize: 12, color: "#92400e", fontWeight: 600 }}>⏸ Interview in progress — continue your consultation</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        )}
      </div>

      {showProfileEditor && profile && (
        <ProfileEditor profile={profile} onSave={load} onClose={() => setShowProfileEditor(false)} />
      )}
    </div>
  );
}
