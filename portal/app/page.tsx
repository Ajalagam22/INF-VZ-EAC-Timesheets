const EAC_SYSTEM_URL =
  process.env.NEXT_PUBLIC_EAC_SYSTEM_URL ?? "https://inf-vz-eac-system.vercel.app";
const EAC_TIMESHEETS_URL =
  process.env.NEXT_PUBLIC_EAC_TIMESHEETS_URL ?? "https://inf-vz-eac-timesheets.vercel.app";

const STATS = [
  { value: "2", label: "Programs" },
  { value: "DOCX + Excel", label: "Input Formats" },
  { value: "CapEx & OpEx", label: "Classification" },
  { value: "AI-Powered", label: "Engine" },
];

export default function Portal() {
  return (
    <div className="shell">

      {/* ── Hero ── */}
      <div className="hero-banner">
        <div className="hero-beam" />
        <div className="hero-inner">
          <div className="hero-top">
            <div className="vz-logo">
              <span className="vz-text">verizon</span>
              <svg className="vz-check" viewBox="0 0 24 24" fill="none" width="20" height="20">
                <path d="M5 13l5 5L20 7" stroke="#d71920" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="hero-divider" />
            <span className="hero-product">EAC Platform</span>
            <span className="header-badge">INF-VZ</span>
          </div>
          <div className="hero-tagline">
            <h1>
              Classify every hour.<br />
              <span className="hero-accent">Capitalize what counts.</span>
            </h1>
            <p>AI-powered CapEx / OpEx classification system.</p>
          </div>
        </div>
      </div>

      {/* ── Stats row ── */}
      <div className="stats-row">
        {STATS.map((s, i) => (
          <div key={s.label} className="stats-row-item">
            <strong>{s.value}</strong>
            <span>{s.label}</span>
            {i < STATS.length - 1 && <div className="stats-divider" />}
          </div>
        ))}
      </div>

      {/* ── Tiles ── */}
      <section className="section main-section">
        <div className="tiles">

          <a href={EAC_SYSTEM_URL} target="_blank" rel="noopener noreferrer" className="tile system-tile">
            <div className="tile-header">
              <div className="tile-icon system">⚙</div>
              <div className="tile-header-text">
                <h3>Employee Activity Classification</h3>
                <span>Network Annual Labour Survey</span>
              </div>
            </div>
            <div className="tile-body">
              <p>Classifies network employee activity records from the <strong>Annual Labour Survey</strong> as CapEx or OpEx using a deterministic rule engine backed by Azure OpenAI.</p>
              <ul className="tile-features">
                <li><strong>Input:</strong> DOCX activity forms &amp; Excel workbooks</li>
                <li>Hybrid rule + LLM classification pipeline</li>
                <li>Confidence scoring per record</li>
                <li>Full audit trail &amp; employee review workflow</li>
              </ul>
            </div>
            <div className="tile-footer">
              <div className="tile-btn system">Launch <span className="arrow">→</span></div>
            </div>
          </a>

          <a href={EAC_TIMESHEETS_URL} target="_blank" rel="noopener noreferrer" className="tile timesheets-tile">
            <div className="tile-header">
              <div className="tile-icon timesheets">📋</div>
              <div className="tile-header-text">
                <h3>Employee Activity Classification</h3>
                <span>Weekly Timesheets Pre-Population</span>
              </div>
            </div>
            <div className="tile-body">
              <p>Pre-populates and classifies <strong>weekly timesheets for project coders</strong> as CapEx or OpEx based on activity type and fixed-asset policy. Streams results progressively.</p>
              <ul className="tile-features">
                <li><strong>Input:</strong> DOCX timesheets &amp; Excel workbooks</li>
                <li>Hybrid rule + LLM classification pipeline</li>
                <li>Confidence scoring per record</li>
                <li>Full audit trail &amp; team lead review workflow</li>
              </ul>
            </div>
            <div className="tile-footer">
              <div className="tile-btn timesheets">Launch <span className="arrow">→</span></div>
            </div>
          </a>

        </div>
      </section>

      {/* ── Closing band ── */}
      <div className="closing-band">
        <div className="closing-beam" />
        <div className="closing-inner">
          <div className="vz-logo">
            <span className="vz-text">verizon</span>
            <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
              <path d="M5 13l5 5L20 7" stroke="#d71920" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <p className="closing-text">
            AI-powered CapEx / OpEx classification system.
          </p>
          <span className="closing-copy">© 2025 INF-VZ EAC Platform</span>
        </div>
      </div>

    </div>
  );
}
