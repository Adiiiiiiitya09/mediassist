import React, { useState, useEffect } from 'react'
import api from '../api/client'

// ── helpers ──────────────────────────────────────────────────
const tierColor = (tier) =>
    ({ High: '#16a34a', Medium: '#d97706', Low: '#dc2626' }[tier] ?? '#6b7280')

const tierBg = (tier) =>
    ({ High: '#d1fae5', Medium: '#fef3c7', Low: '#fee2e2' }[tier] ?? '#f3f4f6')

// ── Profile Editor Modal ──────────────────────────────────────
const inp = {
    width: '100%', padding: '8px 12px', border: '1px solid #e5e7eb',
    borderRadius: 8, fontSize: 14, color: '#111827', background: '#fff',
    boxSizing: 'border-box', marginBottom: 14,
}

const Field = ({ label, k, type = 'text', options, form, set }) => (
    <div>
        <label style={{ display: 'block', fontSize: 12, color: '#6b7280', marginBottom: 4 }}>{label}</label>
        {options
            ? <select value={form[k] ?? ''} onChange={e => set(k, e.target.value)} style={inp}>
                <option value=''>— select —</option>
                {options.map(o => <option key={o}>{o}</option>)}
            </select>
            : <input type={type} value={form[k] ?? ''} onChange={e => set(k, e.target.value)} style={inp} />}
    </div>
)

function ProfileEditor({ profile, onSave, onClose }) {
    const [form, setForm] = useState({ ...profile })
    const [saving, setSaving] = useState(false)
    const [msg, setMsg] = useState('')

    const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

    const save = async () => {
        setSaving(true)
        try {
            await api.put('/doctor/profile', form)
            setMsg('Saved!')
            onSave()
            setTimeout(onClose, 800)
        } catch {
            setMsg('Save failed.')
        } finally {
            setSaving(false)
        }
    }



    return (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ background: '#fff', borderRadius: 16, width: '100%', maxWidth: 580, maxHeight: '90vh', overflow: 'auto', padding: 32, position: 'relative' }}>
                <button onClick={onClose} style={{ position: 'absolute', top: 16, right: 20, background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', color: '#9ca3af' }}>✕</button>
                <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24, color: '#111827' }}>Edit Professional Profile</h2>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 20px' }}>
                    <Field label='Specialization' k='specialization' options={['General Physician', 'Cardiologist', 'Dermatologist', 'Neurologist', 'Orthopedic', 'Pediatrician', 'Psychiatrist', 'Pulmonologist', 'Gastroenterologist', 'ENT Specialist', 'Ophthalmologist', 'Other']} form={form} set={set} />
                    <Field label='Qualification' k='qualification' form={form} set={set} />
                    <Field label='Experience (years)' k='experience_years' type='number' form={form} set={set} />
                    <Field label='License Number' k='license_number' form={form} set={set} />
                    <Field label='Hospital / Clinic' k='hospital' form={form} set={set} />
                    <Field label='Department' k='department' form={form} set={set} />
                    <Field label='Phone' k='phone' form={form} set={set} />
                    <Field label='Consultation Hours' k='consultation_hours' form={form} set={set} />
                    <Field label='Languages Spoken' k='languages' form={form} set={set} />
                </div>

                <div>
                    <label style={{ display: 'block', fontSize: 12, color: '#6b7280', marginBottom: 4 }}>Bio / About</label>
                    <textarea value={form.bio ?? ''} onChange={e => set('bio', e.target.value)}
                        placeholder='Brief professional introduction...' rows={3}
                        style={{ ...inp, resize: 'vertical' }} />
                </div>

                {msg && <p style={{ color: msg === 'Saved!' ? '#16a34a' : '#dc2626', fontSize: 13, marginBottom: 8 }}>{msg}</p>}

                <div style={{ display: 'flex', gap: 12 }}>
                    <button onClick={onClose} style={{ flex: 1, padding: '10px 0', background: '#f3f4f6', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer', color: '#374151' }}>Cancel</button>
                    <button onClick={save} disabled={saving} style={{ flex: 2, padding: '10px 0', background: '#1d4ed8', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer', color: '#fff' }}>
                        {saving ? 'Saving…' : 'Save Profile'}
                    </button>
                </div>
            </div>
        </div>
    )
}

// ── Patient Profile Panel (shown inside consultation detail) ──
function PatientProfilePanel({ profile }) {
    if (!profile) return (
        <div style={{ background: '#f9fafb', borderRadius: 10, padding: '14px 18px', marginBottom: 16 }}>
            <p style={{ fontSize: 13, color: '#9ca3af', fontStyle: 'italic' }}>Patient has not filled their medical profile yet.</p>
        </div>
    )

    const bmi = profile.height_cm && profile.weight_kg
        ? (profile.weight_kg / Math.pow(profile.height_cm / 100, 2)).toFixed(1) : null

    const Row = ({ label, value }) => value ? (
        <div style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
            <span style={{ fontSize: 12, color: '#9ca3af', minWidth: 130, flexShrink: 0 }}>{label}</span>
            <span style={{ fontSize: 13, color: '#111827', fontWeight: 500 }}>{value}</span>
        </div>
    ) : null

    return (
        <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 10, padding: '16px 18px', marginBottom: 16 }}>
            <p style={{ fontSize: 11, fontWeight: 700, color: '#1d4ed8', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 12 }}>Patient Medical Background</p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 24px' }}>
                <div>
                    <Row label='Age / Gender' value={[profile.age ? `${profile.age} yrs` : null, profile.gender].filter(Boolean).join(', ')} />
                    <Row label='Blood Group' value={profile.blood_group} />
                    <Row label='BMI' value={bmi ? `${bmi} (${profile.height_cm}cm / ${profile.weight_kg}kg)` : null} />
                    <Row label='Smoking' value={profile.smoking} />
                    <Row label='Alcohol' value={profile.alcohol} />
                    <Row label='Exercise' value={profile.exercise} />
                </div>
                <div>
                    <Row label='Chronic Conditions' value={profile.chronic_conditions} />
                    <Row label='Past Surgeries' value={profile.past_surgeries} />
                    <Row label='Current Medications' value={profile.current_medications} />
                    <Row label='Known Allergies' value={profile.known_allergies} />
                    <Row label='Family History' value={profile.family_history} />
                </div>
            </div>

            {(profile.emergency_contact_name || profile.emergency_contact_phone) && (
                <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid #bfdbfe' }}>
                    <Row label='Emergency Contact' value={[profile.emergency_contact_name, profile.emergency_contact_phone].filter(Boolean).join(' · ')} />
                </div>
            )}
        </div>
    )
}

// ── Confidence Meter ──────────────────────────────────────────
function ConfidenceMeter({ score, tier }) {
    if (!score) return null
    return (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: '14px 18px', marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>AI Data Quality Score</span>
                <span style={{ fontSize: 15, fontWeight: 700, color: tierColor(tier) }}>{score}% — {tier}</span>
            </div>
            <div style={{ height: 8, background: '#f3f4f6', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${score}%`, background: tierColor(tier), borderRadius: 4, transition: 'width 0.4s' }} />
            </div>
            <p style={{ fontSize: 11, color: '#9ca3af', marginTop: 8 }}>
                ⚠ This is a data quality indicator, not a diagnostic certainty score.
            </p>
        </div>
    )
}

// ── Disease Card ──────────────────────────────────────────────
function DiseaseCard({ disease, probability, description, precautions }) {
    const [open, setOpen] = useState(false)
    return (
        <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, marginBottom: 8, overflow: 'hidden' }}>
            <div onClick={() => setOpen(o => !o)} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', cursor: 'pointer', background: open ? '#f9fafb' : '#fff' }}>
                <span style={{ fontWeight: 600, fontSize: 14, color: '#111827' }}>{disease}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: '#2563eb' }}>{probability}%</span>
                    <span style={{ color: '#9ca3af', fontSize: 16 }}>{open ? '▲' : '▼'}</span>
                </div>
            </div>
            {open && (
                <div style={{ padding: '10px 14px', borderTop: '1px solid #f3f4f6', background: '#fafafa' }}>
                    {description && <p style={{ fontSize: 13, color: '#374151', marginBottom: 8, lineHeight: 1.6 }}>{description}</p>}
                    {precautions?.length > 0 && (
                        <>
                            <p style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Precautions</p>
                            {precautions.map((p, i) => <p key={i} style={{ fontSize: 12, color: '#6b7280', marginBottom: 3 }}>• {p}</p>)}
                        </>
                    )}
                </div>
            )}
        </div>
    )
}

// ── MAIN DASHBOARD ────────────────────────────────────────────
export default function DoctorDashboard() {
    const [consultations, setConsultations] = useState([])
    const [selectedConsult, setSelectedConsult] = useState(null)
    const [notes, setNotes] = useState('')
    const [prescription, setPrescription] = useState('')
    const [loading, setLoading] = useState(true)
    const [profile, setProfile] = useState(null)
    const [showProfileEditor, setShowProfileEditor] = useState(false)
    const [activeTab, setActiveTab] = useState('summary')
    const [actionDone, setActionDone] = useState(false)

    useEffect(() => {
        fetchPending()
        fetchProfile()
    }, [])

    const fetchProfile = async () => {
        try {
            const res = await api.get('/doctor/profile')
            setProfile(res.data)
        } catch (e) {
            console.error(e)
        }
    }

    const fetchPending = async () => {
        try {
            const res = await api.get('/doctor/pending')
            setConsultations(res.data)
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    const loadDetail = async (id) => {
        try {
            const res = await api.get(`/doctor/consultation/${id}`)
            setSelectedConsult(res.data)
            setNotes('')
            setPrescription('')
            setActiveTab('summary')
            setActionDone(false)
        } catch (e) {
            console.error(e)
        }
    }

    const handleApprove = async () => {
        if (!notes.trim()) { alert('Please add doctor notes before approving.'); return }
        try {
            await api.post(`/doctor/approve/${selectedConsult.consultation_id}`, { notes, prescription })
            setActionDone(true)
            fetchPending()
        } catch (e) { console.error(e) }
    }

    const handleReject = async () => {
        if (!notes.trim()) { alert('Please add a reason before rejecting.'); return }
        try {
            await api.post(`/doctor/reject/${selectedConsult.consultation_id}`, { notes })
            setActionDone(true)
            fetchPending()
        } catch (e) { console.error(e) }
    }

    const tabs = ['summary', 'patient bg', 'predictions', 'transcript', 'decision']

    return (
        <div style={{ minHeight: '100vh', background: '#f9fafb', fontFamily: "'Segoe UI', system-ui, sans-serif" }}>

            {/* Top nav */}
            <div style={{ background: '#1d4ed8', padding: '0 28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 58 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 20 }}>🏥</span>
                    <a href="/" onClick={() => localStorage.removeItem("token")} style={{ fontWeight: 700, fontSize: 17, color: '#fff', textDecoration: 'none' }}>MediAssist</a>
                    <span style={{ color: '#93c5fd', marginLeft: 8, fontSize: 14 }}>Doctor Portal</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    {profile?.specialization && (
                        <span style={{ fontSize: 13, color: '#bfdbfe' }}>{profile.specialization}</span>
                    )}
                    <div style={{ width: 34, height: 34, borderRadius: '50%', background: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 14, color: '#fff' }}>
                        {profile?.name?.charAt(0).toUpperCase() ?? 'D'}
                    </div>
                    <span style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>{profile?.name ?? 'Doctor'}</span>
                    <button onClick={() => setShowProfileEditor(true)}
                        style={{ padding: '6px 14px', background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.3)', borderRadius: 6, color: '#fff', fontSize: 12, cursor: 'pointer', fontWeight: 600 }}>
                        Edit Profile
                    </button>
                    <button onClick={() => { localStorage.removeItem("token"); window.location.href = "/doctor-login"; }}
                        style={{ padding: '6px 14px', background: '#dc2626', border: 'none', borderRadius: 6, color: '#fff', fontSize: 12, cursor: 'pointer', fontWeight: 600 }}>
                        Logout
                    </button>
                </div>
            </div>

            <div style={{ display: 'flex', height: 'calc(100vh - 58px)' }}>

                {/* ── LEFT PANEL — consultation list + doctor profile ── */}
                <div style={{ width: 300, borderRight: '1px solid #e5e7eb', background: '#fff', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

                    {/* Doctor profile mini card */}
                    <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid #f3f4f6' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                            <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#dbeafe', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 20, color: '#1d4ed8', flexShrink: 0 }}>
                                {profile?.name?.charAt(0).toUpperCase() ?? 'D'}
                            </div>
                            <div style={{ minWidth: 0 }}>
                                <p style={{ fontWeight: 700, fontSize: 14, color: '#111827', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{profile?.name ?? '—'}</p>
                                <p style={{ fontSize: 12, color: '#6b7280' }}>{profile?.specialization ?? 'Specialization not set'}</p>
                                <p style={{ fontSize: 11, color: '#9ca3af' }}>{profile?.qualification ?? ''}</p>
                            </div>
                        </div>

                        {profile?.hospital && (
                            <p style={{ fontSize: 12, color: '#374151', marginBottom: 4 }}>🏥 {profile.hospital}</p>
                        )}
                        {profile?.experience_years && (
                            <p style={{ fontSize: 12, color: '#374151', marginBottom: 4 }}>🩺 {profile.experience_years} years experience</p>
                        )}
                        {profile?.consultation_hours && (
                            <p style={{ fontSize: 12, color: '#374151', marginBottom: 4 }}>🕐 {profile.consultation_hours}</p>
                        )}
                        {!profile?.specialization && (
                            <button onClick={() => setShowProfileEditor(true)}
                                style={{ width: '100%', padding: '7px 0', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 7, color: '#1d4ed8', fontWeight: 600, fontSize: 12, cursor: 'pointer', marginTop: 4 }}>
                                Complete your profile →
                            </button>
                        )}
                    </div>

                    {/* Pending list */}
                    <div style={{ flex: 1, overflow: 'auto', padding: '16px 16px 0' }}>
                        <p style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 12 }}>
                            Pending ({consultations.length})
                        </p>

                        {loading ? (
                            <p style={{ fontSize: 13, color: '#9ca3af', padding: '8px 0' }}>Loading…</p>
                        ) : consultations.length === 0 ? (
                            <div style={{ textAlign: 'center', padding: '30px 0', color: '#9ca3af' }}>
                                <p style={{ fontSize: 28, marginBottom: 8 }}>✓</p>
                                <p style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>All caught up!</p>
                                <p style={{ fontSize: 12 }}>No pending consultations</p>
                            </div>
                        ) : (
                            consultations.map(c => (
                                <div key={c.consultation_id} onClick={() => loadDetail(c.consultation_id)}
                                    style={{ padding: '12px 14px', borderRadius: 10, border: `1px solid ${selectedConsult?.id === c.consultation_id ? '#93c5fd' : '#e5e7eb'}`, background: selectedConsult?.id === c.consultation_id ? '#eff6ff' : '#fff', marginBottom: 8, cursor: 'pointer', transition: 'all 0.15s' }}
                                    onMouseEnter={e => { if (selectedConsult?.id !== c.consultation_id) e.currentTarget.style.background = '#f9fafb' }}
                                    onMouseLeave={e => { if (selectedConsult?.id !== c.consultation_id) e.currentTarget.style.background = '#fff' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                                        <p style={{ fontWeight: 600, fontSize: 13, color: '#111827' }}>{c.patient_name}</p>
                                        <span style={{ fontSize: 11, fontWeight: 700, color: tierColor(c.confidence_tier), background: tierBg(c.confidence_tier), padding: '2px 8px', borderRadius: 20 }}>
                                            {c.confidence_tier}
                                        </span>
                                    </div>
                                    <p style={{ fontSize: 11, color: '#9ca3af' }}>
                                        {c.created_at ? new Date(c.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Invalid Date'}
                                    </p>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* ── RIGHT PANEL — detail ── */}
                <div style={{ flex: 1, overflow: 'auto', padding: 28 }}>
                    {!selectedConsult ? (
                        <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', flexDirection: 'column', gap: 12 }}>
                            <p style={{ fontSize: 40 }}>👈</p>
                            <p style={{ fontWeight: 600, color: '#374151' }}>Select a consultation to review</p>
                        </div>
                    ) : (
                        <div style={{ maxWidth: 860 }}>

                            {/* Header */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
                                <div>
                                    <p style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Case #{selectedConsult.id} · {selectedConsult.patient_email}</p>
                                    <h2 style={{ fontSize: 22, fontWeight: 700, color: '#111827' }}>{selectedConsult.patient_name}</h2>
                                </div>
                                {actionDone && (
                                    <div style={{ background: '#d1fae5', border: '1px solid #6ee7b7', borderRadius: 8, padding: '8px 16px' }}>
                                        <p style={{ fontSize: 13, fontWeight: 600, color: '#065f46' }}>✓ Decision submitted</p>
                                    </div>
                                )}
                            </div>

                            {/* Confidence meter */}
                            <ConfidenceMeter score={selectedConsult.confidence_score} tier={selectedConsult.confidence_tier} />

                            {/* Tabs */}
                            <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: '#f3f4f6', padding: 4, borderRadius: 10, width: 'fit-content' }}>
                                {tabs.map(t => (
                                    <button key={t} onClick={() => setActiveTab(t)}
                                        style={{
                                            padding: '7px 16px', borderRadius: 7, border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 12, textTransform: 'capitalize',
                                            background: activeTab === t ? '#fff' : 'transparent',
                                            color: activeTab === t ? '#111827' : '#6b7280',
                                            boxShadow: activeTab === t ? '0 1px 3px rgba(0,0,0,0.1)' : 'none'
                                        }}>
                                        {t}
                                    </button>
                                ))}
                            </div>

                            <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e5e7eb', padding: '22px 26px' }}>

                                {/* SUMMARY TAB */}
                                {activeTab === 'summary' && (
                                    <div>
                                        <p style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 8 }}>Chief Complaint</p>
                                        <p style={{ fontSize: 16, fontWeight: 600, color: '#111827', marginBottom: 18 }}>{selectedConsult.structured_data?.chief_complaint}</p>

                                        {selectedConsult.structured_data?.vital_flags?.length > 0 && (
                                            <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '10px 14px', marginBottom: 16 }}>
                                                <p style={{ fontSize: 12, fontWeight: 700, color: '#dc2626', marginBottom: 4 }}>⚠ Vital Flags</p>
                                                {selectedConsult.structured_data.vital_flags.map((f, i) => (
                                                    <p key={i} style={{ fontSize: 13, color: '#7f1d1d' }}>• {f}</p>
                                                ))}
                                            </div>
                                        )}

                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                                            {[
                                                { label: 'Medications', items: selectedConsult.structured_data?.current_medications },
                                                { label: 'Allergies', items: selectedConsult.structured_data?.allergies },
                                                { label: 'Medical History', items: selectedConsult.structured_data?.medical_history },
                                                { label: 'Associated Symptoms', items: selectedConsult.structured_data?.associated_symptoms },
                                            ].map(({ label, items }) => (
                                                <div key={label}>
                                                    <p style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>{label}</p>
                                                    {items?.length
                                                        ? items.map((x, i) => <p key={i} style={{ fontSize: 13, color: '#374151', marginBottom: 3 }}>• {x}</p>)
                                                        : <p style={{ fontSize: 13, color: '#9ca3af' }}>None reported</p>}
                                                </div>
                                            ))}
                                        </div>

                                        {/* Primary symptoms */}
                                        {selectedConsult.structured_data?.symptoms?.length > 0 && (
                                            <div style={{ marginTop: 20 }}>
                                                <p style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Symptom Detail</p>
                                                {selectedConsult.structured_data.symptoms.map((s, i) => (
                                                    <div key={i} style={{ background: '#f9fafb', borderRadius: 8, padding: '10px 14px', marginBottom: 8 }}>
                                                        <p style={{ fontWeight: 600, fontSize: 13, color: '#111827', marginBottom: 4 }}>{s.name}</p>
                                                        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                                                            {s.severity && <span style={{ fontSize: 12, color: '#6b7280' }}>Severity: <strong>{s.severity}/10</strong></span>}
                                                            {s.duration && <span style={{ fontSize: 12, color: '#6b7280' }}>Duration: <strong>{s.duration}</strong></span>}
                                                            {s.type && <span style={{ fontSize: 12, color: '#6b7280' }}>Type: <strong>{s.type}</strong></span>}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* PATIENT BACKGROUND TAB */}
                                {activeTab === 'patient bg' && (
                                    <div>
                                        <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 16, lineHeight: 1.6 }}>
                                            The patient's medical background profile is shared to help you make better clinical decisions.
                                        </p>
                                        <PatientProfilePanel profile={selectedConsult.patient_profile} />
                                    </div>
                                )}

                                {/* PREDICTIONS TAB */}
                                {activeTab === 'predictions' && (
                                    <div>
                                        <div style={{ background: '#fef3c7', border: '1px solid #fde68a', borderRadius: 8, padding: '10px 14px', marginBottom: 16 }}>
                                            <p style={{ fontSize: 12, color: '#92400e', fontWeight: 600 }}>AI suggestions only — final diagnosis is your clinical decision.</p>
                                        </div>
                                        {selectedConsult.prediction?.top5?.map((d, i) => (
                                            <DiseaseCard key={i} disease={d.disease} probability={d.probability} description={d.description} precautions={d.precautions} />
                                        ))}
                                    </div>
                                )}

                                {/* TRANSCRIPT TAB */}
                                {activeTab === 'transcript' && (
                                    <div style={{ maxHeight: 500, overflowY: 'auto' }}>
                                        {selectedConsult.transcript?.map((m, i) => (
                                            <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: 10 }}>
                                                <div style={{
                                                    maxWidth: '75%', padding: '9px 13px', borderRadius: m.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                                                    background: m.role === 'user' ? '#dbeafe' : '#f3f4f6', fontSize: 13, lineHeight: 1.5,
                                                    color: m.role === 'user' ? '#1e3a8a' : '#111827'
                                                }}>
                                                    <p style={{ fontSize: 10, fontWeight: 700, color: m.role === 'user' ? '#3b82f6' : '#9ca3af', marginBottom: 3 }}>
                                                        {m.role === 'user' ? 'PATIENT' : 'AI ASSISTANT'}
                                                    </p>
                                                    {m.content}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* DECISION TAB */}
                                {activeTab === 'decision' && (
                                    <div>
                                        {actionDone ? (
                                            <div style={{ textAlign: 'center', padding: '40px 0' }}>
                                                <p style={{ fontSize: 40, marginBottom: 12 }}>✅</p>
                                                <p style={{ fontWeight: 700, fontSize: 16, color: '#111827' }}>Decision submitted successfully</p>
                                                <p style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>The patient will be notified. Select another consultation from the left panel.</p>
                                            </div>
                                        ) : (
                                            <>
                                                <div style={{ marginBottom: 16 }}>
                                                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#374151', marginBottom: 6 }}>Doctor Notes <span style={{ color: '#dc2626' }}>*</span></label>
                                                    <textarea placeholder='Write your clinical assessment and notes here...'
                                                        value={notes} onChange={e => setNotes(e.target.value)} rows={4}
                                                        style={{ width: '100%', padding: '10px 14px', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 14, resize: 'vertical', boxSizing: 'border-box', color: '#111827' }} />
                                                </div>
                                                <div style={{ marginBottom: 24 }}>
                                                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#374151', marginBottom: 6 }}>Prescription</label>
                                                    <textarea placeholder='List medications, dosages, and instructions...'
                                                        value={prescription} onChange={e => setPrescription(e.target.value)} rows={4}
                                                        style={{ width: '100%', padding: '10px 14px', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 14, resize: 'vertical', boxSizing: 'border-box', color: '#111827' }} />
                                                </div>
                                                <div style={{ display: 'flex', gap: 12 }}>
                                                    <button onClick={handleApprove}
                                                        style={{ flex: 1, padding: '12px 0', background: '#16a34a', border: 'none', borderRadius: 8, color: '#fff', fontWeight: 700, fontSize: 14, cursor: 'pointer' }}>
                                                        ✓ Approve Consultation
                                                    </button>
                                                    <button onClick={handleReject}
                                                        style={{ flex: 1, padding: '12px 0', background: '#dc2626', border: 'none', borderRadius: 8, color: '#fff', fontWeight: 700, fontSize: 14, cursor: 'pointer' }}>
                                                        ✕ Reject Consultation
                                                    </button>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                )}

                            </div>
                        </div>
                    )}
                </div>
            </div>

            {showProfileEditor && profile && (
                <ProfileEditor profile={profile} onSave={fetchProfile} onClose={() => setShowProfileEditor(false)} />
            )}
        </div>
    )
}