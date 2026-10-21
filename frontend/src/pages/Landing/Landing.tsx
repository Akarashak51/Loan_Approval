import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity, ArrowDownRight, ArrowRight, BadgeCheck, BarChart3,
  Check, ChevronRight, CircleHelp, ClipboardCheck, ClipboardList,
  FilePlus2, Fingerprint, LockKeyhole, ShieldCheck, Sparkles, WalletCards,
  XCircle,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { analyticsApi, type DashboardStats } from '../../services/api';
import { formatINR } from '../../utils/featureConfig';
import { StatusBadge } from '../../components/common/StatusBadge';

const features = [
  {
    icon: Fingerprint,
    title: 'Your documents, handled with care',
    description: 'Upload identity and income documents through a clear, guided review flow.',
  },
  {
    icon: Activity,
    title: 'Understand the assessment',
    description: 'See the factors that shaped a result and how they relate to your application.',
  },
  {
    icon: ShieldCheck,
    title: 'Keep every step in view',
    description: 'Follow application status, review notes, and next steps from one place.',
  },
];

function AssessmentPreview() {
  return (
    <div className="landing-preview" aria-label="Illustrative credit assessment preview">
      <div className="landing-preview-orb landing-preview-orb-one" />
      <div className="landing-preview-orb landing-preview-orb-two" />
      <div className="preview-window">
        <div className="preview-window-top">
          <div className="preview-brand"><span className="preview-brand-mark"><Sparkles size={14} /></span> GlassBox <span className="preview-example">EXAMPLE</span></div>
          <span className="preview-live"><span /> Assessment view</span>
        </div>
        <div className="preview-overview">
          <div>
            <p className="preview-label">CREDIT ASSESSMENT</p>
            <h2>Know what shaped<br />the result.</h2>
          </div>
          <div className="preview-score" aria-hidden="true"><span>72</span><small>illustrative</small></div>
        </div>
        <div className="preview-chart" aria-hidden="true">
          {[30, 46, 38, 64, 50, 76, 61, 88, 68, 96, 75, 84, 62, 92, 70, 100].map((height, index) => (
            <i key={index} style={{ height: `${height}%`, opacity: 0.34 + index / 28 }} />
          ))}
          <span className="preview-chart-line" />
        </div>
        <div className="preview-drivers">
          <div className="preview-driver"><span className="preview-driver-icon"><WalletCards size={15} /></span><span><strong>Payment history</strong><small>Positive contribution</small></span><ArrowDownRight size={15} /></div>
          <div className="preview-driver"><span className="preview-driver-icon preview-driver-icon-soft"><BarChart3 size={15} /></span><span><strong>Debt-to-income</strong><small>Room to improve</small></span><ChevronRight size={15} /></div>
        </div>
        <p className="preview-footnote"><LockKeyhole size={12} /> Your information stays private</p>
      </div>
      <div className="preview-float-card"><span><BadgeCheck size={17} /></span><div><strong>Clear explanations</strong><small>Every step, in plain language</small></div><Check size={15} /></div>
    </div>
  );
}

function WelcomeDashboard({ name, stats }: { name: string; stats: DashboardStats | null }) {
  const cards = [
    { label: 'Applications', value: stats?.total ?? '—', icon: ClipboardList, tone: 'dashboard-icon-blue', hint: 'Your full application history' },
    { label: 'Approved', value: stats?.approved ?? '—', icon: BadgeCheck, tone: 'dashboard-icon-green', hint: 'Applications approved' },
    { label: 'Declined', value: stats?.rejected ?? '—', icon: XCircle, tone: 'dashboard-icon-rose', hint: 'Applications declined' },
    { label: 'Approval rate', value: stats?.approval_rate == null ? '—' : `${stats.approval_rate}%`, icon: BarChart3, tone: 'dashboard-icon-gold', hint: 'Across your applications' },
  ];
  const risks = [
    { label: 'Lower risk', value: stats?.risk_distribution.low ?? 0, tone: 'risk-fill-green' },
    { label: 'Moderate risk', value: stats?.risk_distribution.medium ?? 0, tone: 'risk-fill-gold' },
    { label: 'Higher risk', value: stats?.risk_distribution.high ?? 0, tone: 'risk-fill-rose' },
  ];

  return (
    <div className="dashboard-shell">
      <section className="dashboard-welcome">
        <div className="dashboard-welcome-copy">
          <span className="dashboard-eyebrow"><Sparkles size={14} /> YOUR GLASSBOX</span>
          <h1>Welcome back, <span>{name}</span></h1>
          <p>Your applications and next steps, all in one clear view.</p>
        </div>
        <Link to="/apply" className="dashboard-primary-action"><FilePlus2 size={17} /> Start an application <ArrowRight size={16} /></Link>
        <div className="dashboard-welcome-art" aria-hidden="true"><span /><span /><span /><span /></div>
      </section>

      <section className="dashboard-stats" aria-label="Application summary">
        {cards.map(({ label, value, icon: Icon, tone, hint }) => (
          <article key={label} className="dashboard-stat-card">
            <div className={`dashboard-stat-icon ${tone}`}><Icon size={19} /></div>
            <p>{label}</p><strong>{value}</strong><small>{hint}</small>
          </article>
        ))}
      </section>

      <div className="dashboard-grid">
        <section className="dashboard-panel dashboard-applications">
          <div className="dashboard-panel-heading"><div><span className="dashboard-eyebrow">YOUR ACTIVITY</span><h2>Recent applications</h2></div><Link to="/history" className="dashboard-text-link">View history <ArrowRight size={14} /></Link></div>
          {stats?.recent_applications.length ? (
            <div className="dashboard-table-wrap"><table className="dashboard-table"><thead><tr><th>Application</th><th>Loan amount</th><th>Decision</th><th>Risk</th></tr></thead><tbody>
              {stats.recent_applications.map(application => <tr key={application.id}><td><span className="dashboard-app-id"><span><ClipboardCheck size={14} /></span>{application.application_id}</span></td><td>{formatINR(application.features.credit_amount)}</td><td><StatusBadge value={application.prediction?.decision ?? 'Under Review'} /></td><td>{application.prediction ? <StatusBadge value={application.prediction.risk_level} /> : <span className="dashboard-pending">In progress</span>}</td></tr>)}
            </tbody></table></div>
          ) : <div className="dashboard-empty"><span><ClipboardList size={20} /></span><strong>No applications yet</strong><p>Your application activity will appear here.</p><Link to="/apply">Create your first application <ArrowRight size={14} /></Link></div>}
        </section>

        <section className="dashboard-panel dashboard-risk-panel">
          <div className="dashboard-panel-heading"><div><span className="dashboard-eyebrow">AT A GLANCE</span><h2>Risk distribution</h2></div><span className="dashboard-panel-icon"><Activity size={17} /></span></div>
          <p className="dashboard-panel-subtitle">Risk levels across assessed applications</p>
          <div className="dashboard-risk-list">{risks.map(({ label, value, tone }) => <div className="dashboard-risk-row" key={label}><div><span>{label}</span><strong>{value}</strong></div><div className="dashboard-risk-track"><span className={tone} style={{ width: `${stats?.total ? Math.min(100, Number(value) / stats.total * 100) : 0}%` }} /></div></div>)}</div>
          <p className="dashboard-disclaimer"><CircleHelp size={15} /> Model risk indicators support review; they aren’t an official credit score or a bank decision.</p>
        </section>
      </div>
    </div>
  );
}

export default function Landing() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  useEffect(() => {
    if (!user) return;
    let active = true;
    analyticsApi.dashboard().then(value => { if (active) setStats(value); }).catch(() => { if (active) setStats(null); });
    return () => { active = false; };
  }, [user]);

  if (user) return <WelcomeDashboard name={user.full_name.split(' ')[0]} stats={stats} />;

  return (
    <div className="landing-shell">
      <section className="landing-hero">
        <div className="landing-copy">
          <div className="landing-kicker"><span><Sparkles size={14} /></span> CREDIT, MADE CLEARER</div>
          <h1>Make your next<br /><span>move with clarity.</span></h1>
          <p className="landing-intro">A more transparent way to explore credit. Follow your application, understand the assessment, and see what comes next.</p>
          <div className="landing-actions">
            <Link to="/register" className="landing-cta">Get started <ArrowRight size={17} /></Link>
            <Link to="/login" className="landing-login">Sign in <ChevronRight size={16} /></Link>
          </div>
          <div className="landing-trust"><span><ShieldCheck size={15} /></span><p><strong>Built around transparency</strong><small>Clear steps. Explainable results. Human review where needed.</small></p></div>
        </div>
        <AssessmentPreview />
        <div className="landing-hero-grain" aria-hidden="true" />
      </section>

      <section className="landing-features" id="features">
        <div className="landing-section-heading"><div><span className="landing-section-kicker">A BETTER WAY TO APPLY</span><h2>Clarity at every step.</h2></div><p>Credit decisions are important. The experience around them should feel clear, considered, and easy to follow.</p></div>
        <div className="landing-feature-grid">{features.map(({ icon: Icon, title, description }, index) => <article className="landing-feature-card" key={title}><div className="landing-feature-number">0{index + 1}</div><span className="landing-feature-icon"><Icon size={20} /></span><h3>{title}</h3><p>{description}</p><span className="landing-feature-arrow"><ArrowRight size={16} /></span></article>)}</div>
      </section>

      <section className="landing-bottom-cta"><span className="landing-bottom-icon"><ClipboardCheck size={20} /></span><div><span className="landing-section-kicker">READY WHEN YOU ARE</span><h2>Start with a clearer picture.</h2><p>Create an account to begin your application and keep everything in one place.</p></div><Link to="/register" className="landing-cta landing-cta-compact">Create your account <ArrowRight size={16} /></Link></section>
      <footer className="landing-footer"><span>GLASS<span>BOX</span></span><p>Explainable credit, with people in the loop.</p><Link to="/about">About GlassBox <ArrowRight size={13} /></Link></footer>
    </div>
  );
}
