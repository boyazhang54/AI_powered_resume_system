import { useEffect, useMemo, useState } from 'react';
import { getHistory, getMe, login, matchResume, parseResume, register } from './api';
import { RadarChart } from './components/RadarChart';
import type { HistoryItem, MatchResult, ResumeParseResult, User } from './types';

const sampleJd =
  '招聘 Python 后端工程师，要求熟悉 FastAPI、Redis、MySQL，具备 Serverless 或云服务部署经验，了解 AI API 调用、文本处理和前后端协作，有项目落地经验优先。';

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  const [file, setFile] = useState<File | null>(null);
  const [resume, setResume] = useState<ResumeParseResult | null>(null);
  const [jd, setJd] = useState('');
  const [match, setMatch] = useState<MatchResult | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [activeView, setActiveView] = useState<'analyze' | 'history'>('analyze');
  const [loadingParse, setLoadingParse] = useState(false);
  const [loadingMatch, setLoadingMatch] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState('');
  const [showText, setShowText] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('resume_ai_token');
    if (!token) return;
    getMe()
      .then(setUser)
      .catch(() => localStorage.removeItem('resume_ai_token'));
  }, []);

  useEffect(() => {
    if (user && activeView === 'history') {
      loadHistory();
    }
  }, [user, activeView]);

  const scoreClass = useMemo(() => {
    if (!match) return 'score-neutral';
    if (match.score >= 80) return 'score-high';
    if (match.score >= 60) return 'score-mid';
    return 'score-low';
  }, [match]);

  async function handleAuth() {
    if (!username.trim() || !password.trim()) {
      setError('请输入用户名和密码。');
      return;
    }
    setAuthLoading(true);
    setError('');
    try {
      const result = authMode === 'login'
        ? await login(username.trim(), password)
        : await register(username.trim(), password);
      localStorage.setItem('resume_ai_token', result.access_token);
      setUser(result.user);
      setUsername('');
      setPassword('');
    } catch (err: any) {
      setError(err?.response?.data?.detail || '认证失败，请检查用户名和密码。');
    } finally {
      setAuthLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem('resume_ai_token');
    setUser(null);
    setHistory([]);
    resetAll();
  }

  async function handleParse() {
    if (!file) {
      setError('请先选择一份 PDF 简历。');
      return;
    }
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setError('当前仅支持 PDF 文件。');
      return;
    }
    setError('');
    setMatch(null);
    setLoadingParse(true);
    try {
      const result = await parseResume(file);
      setResume(result);
    } catch (err: any) {
      setError(err?.response?.data?.detail || '简历解析失败，请检查后端服务是否已启动。');
    } finally {
      setLoadingParse(false);
    }
  }

  async function handleMatch() {
    if (!resume) {
      setError('请先完成简历解析。');
      return;
    }
    if (!jd.trim()) {
      setError('请粘贴岗位 JD 后再开始匹配。');
      return;
    }
    setError('');
    setLoadingMatch(true);
    try {
      const result = await matchResume(resume.resume_id, jd);
      setMatch(result);
      await loadHistory(false);
    } catch (err: any) {
      setError(err?.response?.data?.detail || '匹配分析失败，请稍后重试。');
    } finally {
      setLoadingMatch(false);
    }
  }

  async function loadHistory(showLoading = true) {
    if (showLoading) setLoadingHistory(true);
    try {
      setHistory(await getHistory());
    } catch (err: any) {
      setError(err?.response?.data?.detail || '历史记录加载失败。');
    } finally {
      if (showLoading) setLoadingHistory(false);
    }
  }

  function resetAll() {
    setFile(null);
    setResume(null);
    setJd('');
    setMatch(null);
    setError('');
    setShowText(false);
  }

  if (!user) {
    return (
      <main className="auth-shell">
        <section className="auth-panel">
          <p className="eyebrow">AI Resume Analyzer</p>
          <h1>智能简历分析系统</h1>
          <div className="auth-tabs">
            <button className={authMode === 'login' ? 'tab active' : 'tab'} onClick={() => setAuthMode('login')}>登录</button>
            <button className={authMode === 'register' ? 'tab active' : 'tab'} onClick={() => setAuthMode('register')}>注册</button>
          </div>
          {error && <div className="alert">{error}</div>}
          <label className="field">
            <span>用户名</span>
            <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="至少 3 位" />
          </label>
          <label className="field">
            <span>密码</span>
            <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="至少 6 位" />
          </label>
          <button className="primary-button" onClick={handleAuth} disabled={authLoading}>
            {authLoading ? '处理中...' : authMode === 'login' ? '登录' : '注册并登录'}
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">AI Resume Analyzer</p>
          <h1>AI 赋能的智能简历分析系统</h1>
        </div>
        <div className="top-actions">
          <span className="user-pill">{user.username}</span>
          <button className={activeView === 'analyze' ? 'tab active' : 'tab'} onClick={() => setActiveView('analyze')}>分析</button>
          <button className={activeView === 'history' ? 'tab active' : 'tab'} onClick={() => setActiveView('history')}>历史记录</button>
          <button className="ghost-button" onClick={resetAll}>清空</button>
          <button className="ghost-button" onClick={logout}>退出</button>
        </div>
      </section>

      {error && <div className="alert">{error}</div>}

      {activeView === 'history' ? (
        <HistoryView history={history} loading={loadingHistory} onRefresh={() => loadHistory()} />
      ) : (
        <>
          <section className="workspace">
            <div className="panel">
              <div className="panel-head">
                <span className="step">1</span>
                <h2>上传简历</h2>
              </div>
              <label className="upload-box">
                <input
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />
                <span>{file ? file.name : '选择 PDF 简历文件'}</span>
              </label>
              <button className="primary-button" onClick={handleParse} disabled={loadingParse}>
                {loadingParse ? '解析中...' : '解析简历'}
              </button>

              {resume && (
                <div className="result-block">
                  <div className="meta-row">
                    <span>Resume ID</span>
                    <strong>{resume.resume_id}</strong>
                  </div>
                  <InfoGrid items={[
                    ['姓名', resume.profile.name],
                    ['电话', resume.profile.phone],
                    ['邮箱', resume.profile.email],
                    ['地址', resume.profile.address],
                    ['求职意向', resume.profile.job_intention],
                    ['期望薪资', resume.profile.expected_salary],
                    ['工作年限', resume.profile.years_of_experience],
                  ]} />
                  <TagGroup title="技能关键词" items={resume.profile.skills} empty="暂未识别到技能关键词" />
                  <button className="text-button" onClick={() => setShowText((value) => !value)}>
                    {showText ? '收起简历文本' : '展开简历文本'}
                  </button>
                  {showText && <pre className="resume-text">{resume.cleaned_text}</pre>}
                </div>
              )}
            </div>

            <div className="panel">
              <div className="panel-head">
                <span className="step">2</span>
                <h2>岗位 JD</h2>
              </div>
              <div className="source-tabs">
                <button className="tab active">JD 文本</button>
                <button className="tab disabled" title="后续可接网页抓取与正文抽取">JD 链接</button>
              </div>
              <textarea
                value={jd}
                onChange={(event) => setJd(event.target.value)}
                placeholder="粘贴岗位描述、职责、任职要求等文本..."
              />
              <div className="actions">
                <button className="secondary-button" onClick={() => setJd(sampleJd)}>填入示例 JD</button>
                <button className="primary-button" onClick={handleMatch} disabled={loadingMatch}>
                  {loadingMatch ? '分析中...' : '开始匹配'}
                </button>
              </div>
            </div>
          </section>

          {match && <MatchAnalysis match={match} scoreClass={scoreClass} />}
        </>
      )}
    </main>
  );
}

function MatchAnalysis({ match, scoreClass }: { match: MatchResult; scoreClass: string }) {
  return (
    <section className="analysis">
      <div className={`score-card ${scoreClass}`}>
        <span>综合匹配度</span>
        <strong>{match.score}</strong>
        <small>
          {match.analysis_mode === 'ai_enhanced' ? 'AI 语义增强' : '规则兜底'} · 关键词匹配率 {(match.keyword_match_rate * 100).toFixed(0)}%
        </small>
      </div>

      <div className="analysis-grid">
        <div className="panel">
          <div className="panel-head">
            <span className="step">3</span>
            <h2>多维度评估</h2>
          </div>
          <RadarChart data={match.radar_scores} />
        </div>

        <div className="panel">
          <div className="panel-head">
            <span className="step">4</span>
            <h2>缺失技能</h2>
          </div>
          <TagGroup title="已匹配关键词" items={match.matched_keywords} empty="暂无匹配关键词" />
          <TagGroup title="缺失技能 / 关键词" items={match.missing_keywords} empty="暂无明显缺失项" variant="missing" />
          {match.missing_skill_details?.length > 0 && (
            <div className="detail-list">
              {match.missing_skill_details.slice(0, 5).map((item) => (
                <div className="detail-item missing-detail" key={`${item.skill}-${item.reason}`}>
                  <strong>{item.normalized_skill || item.skill}</strong>
                  <span>{importanceText(item.importance)}</span>
                  {item.reason && <p>{item.reason}</p>}
                </div>
              ))}
            </div>
          )}
          <div className="summary-box">{match.ai_summary}</div>
        </div>
      </div>

      {match.semantic_matches?.length > 0 && (
        <div className="panel semantic-panel">
          <div className="panel-head">
            <span className="step">5</span>
            <h2>语义匹配证据</h2>
          </div>
          <div className="detail-list">
            {match.semantic_matches.slice(0, 8).map((item) => (
              <div className="detail-item" key={`${item.requirement}-${item.score}`}>
                <div className="detail-title">
                  <strong>{item.requirement}</strong>
                  <span className={`match-badge ${item.match_level}`}>{matchLevelText(item.match_level)} · {item.score}</span>
                </div>
                {item.normalized_skill && <small>标准能力项：{item.normalized_skill}</small>}
                {item.evidence && <p>证据：{item.evidence}</p>}
                {item.reason && <p>判断：{item.reason}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function HistoryView({ history, loading, onRefresh }: { history: HistoryItem[]; loading: boolean; onRefresh: () => void }) {
  return (
    <section className="panel">
      <div className="panel-head split-head">
        <div className="panel-title-row">
          <span className="step">H</span>
          <h2>匹配历史记录</h2>
        </div>
        <button className="secondary-button" onClick={onRefresh} disabled={loading}>{loading ? '刷新中...' : '刷新'}</button>
      </div>
      <div className="history-table">
        <div className="history-row history-head">
          <span>姓名</span>
          <span>联系方式</span>
          <span>岗位</span>
          <span>分数</span>
          <span>时间</span>
        </div>
        {history.length ? history.map((item) => (
          <div className="history-row" key={item.id}>
            <strong>{item.candidate_name}</strong>
            <span>{item.contact}</span>
            <span>{item.job_title}</span>
            <span className={item.score >= 80 ? 'score-text high' : item.score >= 60 ? 'score-text mid' : 'score-text low'}>{item.score}</span>
            <span>{new Date(item.created_at).toLocaleString()}</span>
          </div>
        )) : <div className="empty-history">暂无历史记录</div>}
      </div>
    </section>
  );
}

function InfoGrid({ items }: { items: Array<[string, string | null | undefined]> }) {
  return (
    <div className="info-grid">
      {items.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{value || '未识别'}</strong>
        </div>
      ))}
    </div>
  );
}

function TagGroup({
  title,
  items,
  empty,
  variant = 'normal',
}: {
  title: string;
  items: string[];
  empty: string;
  variant?: 'normal' | 'missing';
}) {
  return (
    <div className="tag-section">
      <h3>{title}</h3>
      <div className="tags">
        {items.length ? items.map((item) => <span className={`tag ${variant}`} key={item}>{item}</span>) : <span className="empty">{empty}</span>}
      </div>
    </div>
  );
}

function matchLevelText(level: string) {
  const map: Record<string, string> = {
    strong: '强匹配',
    partial: '部分匹配',
    weak: '弱匹配',
    none: '未匹配',
  };
  return map[level] || '待判断';
}

function importanceText(level: string) {
  const map: Record<string, string> = {
    high: '高重要性',
    medium: '中重要性',
    low: '低重要性',
  };
  return map[level] || '中重要性';
}

export default App;
