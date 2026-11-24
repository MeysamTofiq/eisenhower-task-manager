const { useState, useEffect, useRef, createContext, useContext } = React;

// ═══════════════════════════════════════════════
//  THEME SYSTEM
// ═══════════════════════════════════════════════

const ThemeContext = createContext();

const THEMES = {
    dark_neon: {
        name: 'دارک نئون',
        bg: '#0a0a1a',
        sidebarBg: '#0d0d20',
        cardBg: 'rgba(255,255,255,0.03)',
        cardBorder: 'rgba(0,255,255,0.08)',
        text: '#e0e0f0',
        textDim: '#64748B',
        primary: '#00FFFF',
        secondary: '#9D4EDD',
        success: '#00FF99',
        danger: '#FF0055',
        warning: '#FFD700',
        inputBg: '#16162a',
        inputBorder: '#303055',
        chatBg: '#0f0f24',
        msgMeBg: 'linear-gradient(135deg, #00FFFF22, #9D4EDD22)',
        msgOtherBg: '#16162a',
    },
    gray_neutral: {
        name: 'خاکستری خنثی',
        bg: '#1e1e1e',
        sidebarBg: '#252525',
        cardBg: 'rgba(255,255,255,0.05)',
        cardBorder: 'rgba(255,255,255,0.1)',
        text: '#e0e0e0',
        textDim: '#888',
        primary: '#64b5f6',
        secondary: '#ab47bc',
        success: '#66bb6a',
        danger: '#ef5350',
        warning: '#ffa726',
        inputBg: '#2a2a2a',
        inputBorder: '#404040',
        chatBg: '#1a1a1a',
        msgMeBg: 'linear-gradient(135deg, #64b5f622, #ab47bc22)',
        msgOtherBg: '#2a2a2a',
    },
    light: {
        name: 'روشن',
        bg: '#f5f5f5',
        sidebarBg: '#ffffff',
        cardBg: '#ffffff',
        cardBorder: '#e0e0e0',
        text: '#333333',
        textDim: '#888888',
        primary: '#1976d2',
        secondary: '#7b1fa2',
        success: '#388e3c',
        danger: '#d32f2f',
        warning: '#f57c00',
        inputBg: '#ffffff',
        inputBorder: '#cccccc',
        chatBg: '#f0f0f0',
        msgMeBg: 'linear-gradient(135deg, #1976d222, #7b1fa222)',
        msgOtherBg: '#ffffff',
    }
};

function ThemeProvider({ children }) {
    const [themeKey, setThemeKey] = useState(() => localStorage.getItem('theme') || 'dark_neon');

    const setTheme = (key) => {
        setThemeKey(key);
        localStorage.setItem('theme', key);
        // ذخیره در سرور
        apiPut('/api/settings', { theme: key });
    };

    const theme = THEMES[themeKey] || THEMES.dark_neon;

    // اعمال CSS متغیرها
    useEffect(() => {
        const root = document.documentElement;
        root.style.setProperty('--bg', theme.bg);
        root.style.setProperty('--sidebar-bg', theme.sidebarBg);
        root.style.setProperty('--card-bg', theme.cardBg);
        root.style.setProperty('--card-border', theme.cardBorder);
        root.style.setProperty('--text', theme.text);
        root.style.setProperty('--text-dim', theme.textDim);
        root.style.setProperty('--primary', theme.primary);
        root.style.setProperty('--secondary', theme.secondary);
        root.style.setProperty('--success', theme.success);
        root.style.setProperty('--danger', theme.danger);
        root.style.setProperty('--warning', theme.warning);
        root.style.setProperty('--input-bg', theme.inputBg);
        root.style.setProperty('--input-border', theme.inputBorder);
        root.style.setProperty('--chat-bg', theme.chatBg);
        root.style.setProperty('--msg-me-bg', theme.msgMeBg);
        root.style.setProperty('--msg-other-bg', theme.msgOtherBg);
        document.body.style.background = theme.bg;
        document.body.style.color = theme.text;
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, themeKey, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

function useTheme() { return useContext(ThemeContext); }

// ═══════════════════════════════════════════════
//  TOKEN MANAGEMENT
// ═══════════════════════════════════════════════

let AUTH_TOKEN = localStorage.getItem('token') || '';

function setToken(t) { AUTH_TOKEN = t; localStorage.setItem('token', t); }
function clearToken() { AUTH_TOKEN = ''; localStorage.removeItem('token'); }

async function apiGet(url) {
    const r = await fetch(url, { headers: { 'Authorization': 'Bearer ' + AUTH_TOKEN } });
    if (r.status === 401) { clearToken(); return null; }
    return r.json();
}

async function apiPost(url, data) {
    const r = await fetch(url, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + AUTH_TOKEN },
        body: JSON.stringify(data)
    });
    if (r.status === 401) { clearToken(); return null; }
    return r.json();
}

async function apiUpload(url, formData) {
    const r = await fetch(url, {
        method: 'POST', headers: { 'Authorization': 'Bearer ' + AUTH_TOKEN }, body: formData
    });
    if (r.status === 401) { clearToken(); return null; }
    return r.json();
}

async function apiPut(url, data) {
    const r = await fetch(url, {
        method: 'PUT', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + AUTH_TOKEN },
        body: JSON.stringify(data)
    });
    if (r.status === 401) { clearToken(); return null; }
    return r.json();
}

// ═══════════════════════════════════════════════
//  LOGIN
// ═══════════════════════════════════════════════

function LoginPage({ onLogin }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async () => {
        setLoading(true); setError('');
        const r = await fetch('/api/login', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await r.json();
        setLoading(false);
        if (data.token) { setToken(data.token); onLogin(data); }
        else setError(data.error || 'خطا در ورود');
    };

    return (
        <div className="login-page">
            <div className="login-box">
                <div style={{fontSize:40}}>⚡</div>
                <h1>مدیریت امور</h1>
                <p>بازرگانی محسنی</p>
                <input className="input" placeholder="نام کاربری" value={username}
                    onChange={e=>setUsername(e.target.value)}
                    onKeyDown={e=>e.key==='Enter'&&handleLogin()} />
                <input className="input" type="password" placeholder="رمز عبور" value={password}
                    onChange={e=>setPassword(e.target.value)}
                    onKeyDown={e=>e.key==='Enter'&&handleLogin()} />
                {error && <div className="error-msg">{error}</div>}
                <button className="btn btn-primary w-full mt-8" onClick={handleLogin} disabled={loading}>
                    {loading ? '⏳' : 'ورود'}
                </button>
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════
//  VOICE RECORDER
// ═══════════════════════════════════════════════

function VoiceRecorder({ onVoiceReady }) {
    const [recording, setRecording] = useState(false);
    const [duration, setDuration] = useState(0);
    const audioCtxRef = useRef(null);
    const streamRef = useRef(null);
    const processorRef = useRef(null);
    const buffersRef = useRef([]);
    const timerRef = useRef(null);
    const startTimeRef = useRef(0);

    function encodeWAV(buffers, sampleRate) {
        const length = buffers.reduce((a, b) => a + b.length, 0);
        const result = new ArrayBuffer(44 + length * 2);
        const view = new DataView(result);
        const writeStr = (off, str) => { for (let i = 0; i < str.length; i++) view.setUint8(off + i, str.charCodeAt(i)); };
        writeStr(0, 'RIFF');
        view.setUint32(4, 36 + length * 2, true);
        writeStr(8, 'WAVE');
        writeStr(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, 1, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true);
        view.setUint16(34, 16, true);
        writeStr(36, 'data');
        view.setUint32(40, length * 2, true);
        let offset = 44;
        for (const buf of buffers) {
            for (let i = 0; i < buf.length; i++) {
                const s = Math.max(-1, Math.min(1, buf[i]));
                view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                offset += 2;
            }
        }
        return new Blob([result], { type: 'audio/wav' });
    }

    const start = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const source = ctx.createMediaStreamSource(stream);
            const processor = ctx.createScriptProcessor(4096, 1, 1);
            buffersRef.current = [];
            processor.onaudioprocess = e => {
                buffersRef.current.push(new Float32Array(e.inputBuffer.getChannelData(0)));
            };
            source.connect(processor);
            processor.connect(ctx.destination);
            audioCtxRef.current = ctx;
            streamRef.current = stream;
            processorRef.current = processor;
            startTimeRef.current = Date.now();
            setRecording(true); setDuration(0);
            timerRef.current = setInterval(() => setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000)), 1000);
        } catch (err) { alert('میکروفون در دسترس نیست'); }
    };

    const stop = () => {
        const sr = audioCtxRef.current?.sampleRate || 44100;
        if (processorRef.current) processorRef.current.disconnect();
        if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
        if (audioCtxRef.current) audioCtxRef.current.close();
        clearInterval(timerRef.current);
        setRecording(false);
        const wavBlob = encodeWAV(buffersRef.current, sr);
        onVoiceReady(wavBlob);
    };

    useEffect(() => () => clearInterval(timerRef.current), []);
    const fmt = s => `${Math.floor(s/60)}:${(s%60).toString().padStart(2,'0')}`;

    return (
        <button className={`btn ${recording ? 'btn-danger recording' : 'btn-ghost'}`}
            onClick={recording ? stop : start}>
            {recording ? `⏹ ${fmt(duration)}` : '🎤 ویس'}
        </button>
    );
}

// ═══════════════════════════════════════════════
//  VOICE TO TASK
// ═══════════════════════════════════════════════

function VoiceToTask({ onClose }) {
    const [recording, setRecording] = useState(false);
    const [audioBlob, setAudioBlob] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [rawText, setRawText] = useState('');
    const [users, setUsers] = useState([]);
    const [userSearch, setUserSearch] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [showUserSearch, setShowUserSearch] = useState(false);
    const [debugLog, setDebugLog] = useState('');
    const [showLog, setShowLog] = useState(false);
    const audioCtxRef = useRef(null);
    const streamRef = useRef(null);
    const processorRef = useRef(null);
    const buffersRef = useRef([]);

    function encodeWAV(buffers, sampleRate) {
        const length = buffers.reduce((a, b) => a + b.length, 0);
        const result = new ArrayBuffer(44 + length * 2);
        const view = new DataView(result);
        const writeStr = (off, str) => { for (let i = 0; i < str.length; i++) view.setUint8(off + i, str.charCodeAt(i)); };
        writeStr(0, 'RIFF'); view.setUint32(4, 36 + length * 2, true);
        writeStr(8, 'WAVE'); writeStr(12, 'fmt '); view.setUint32(16, 16, true);
        view.setUint16(20, 1, true); view.setUint16(22, 1, true);
        view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true); view.setUint16(34, 16, true);
        writeStr(36, 'data'); view.setUint32(40, length * 2, true);
        let offset = 44;
        for (const buf of buffers) {
            for (let i = 0; i < buf.length; i++) {
                const s = Math.max(-1, Math.min(1, buf[i]));
                view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                offset += 2;
            }
        }
        return new Blob([result], { type: 'audio/wav' });
    }

    const startRec = async () => {
        try {
            setResult(null); setRawText(''); setUserSearch(''); setError('');
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const source = ctx.createMediaStreamSource(stream);
            const processor = ctx.createScriptProcessor(4096, 1, 1);
            buffersRef.current = [];
            processor.onaudioprocess = e => buffersRef.current.push(new Float32Array(e.inputBuffer.getChannelData(0)));
            source.connect(processor); processor.connect(ctx.destination);
            audioCtxRef.current = ctx; streamRef.current = stream; processorRef.current = processor;
            setRecording(true);
        } catch (err) { setError('میکروفون در دسترس نیست'); }
    };

    const stopRec = () => {
        if (processorRef.current) processorRef.current.disconnect();
        if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
        const sr = audioCtxRef.current?.sampleRate || 44100;
        if (audioCtxRef.current) audioCtxRef.current.close();
        setRecording(false);
        setAudioBlob(encodeWAV(buffersRef.current, sr));
    };

    const processVoice = async () => {
        if (!audioBlob) return;
        setLoading(true); setError(''); setResult(null); setUserSearch('');
        const fd = new FormData();
        fd.append('voice', audioBlob, 'recording.wav');
        const r = await fetch('/api/voice-to-task', {
            method: 'POST', headers: { 'Authorization': 'Bearer ' + AUTH_TOKEN }, body: fd
        });
        const data = await r.json();
        setLoading(false);
        if (data.error) setError(data.error);
        else { setResult(data); setRawText(data.raw_text); setUserSearch(data.assigned_to || ''); }
    };

    useEffect(() => {
        apiGet('/api/users').then(r => r && setUsers(r));
    }, []);

    useEffect(() => {
        if (userSearch.length > 0) {
            apiGet(`/api/users/search?q=${encodeURIComponent(userSearch)}`).then(r => {
                if (r) setSearchResults(r);
            });
        } else {
            setSearchResults(users.slice(0, 10));
        }
    }, [userSearch, users]);

    const selectUser = (u) => {
        setResult({...result, assigned_to: u.full_name || u.username});
        setUserSearch(u.full_name || u.username);
        setShowUserSearch(false);
    };

    const saveTask = async () => {
        await apiPost('/api/tasks', {
            title: result.title, notes: result.notes, priority: result.priority,
            urgency: result.urgency || 'غیر فوری', level: result.level || 3,
            deadline: result.deadline || '', assigned_to: result.assigned_to || '',
            time_given: result.time_given || '',
            status: 'در حال انجام'
        });
        onClose();
    };

    const [testText, setTestText] = useState('');
    const processTestText = async () => {
        if (!testText.trim()) return;
        setLoading(true); setError(''); setResult(null); setUserSearch('');
        const r = await fetch('/api/voice-to-text', {
            method: 'POST', headers: {'Content-Type':'application/json', 'Authorization': 'Bearer ' + AUTH_TOKEN},
            body: JSON.stringify({text: testText})
        });
        const data = await r.json();
        setLoading(false);
        if (data.error) setError(data.error);
        else { setResult(data); setRawText(data.raw_text || testText); setUserSearch(data.assigned_to || ''); }
        // دریافت لاگ
        fetchDebugLog();
    };

    const fetchDebugLog = async () => {
        const r = await apiGet('/api/debug/log');
        if (r && r.log) setDebugLog(r.log);
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e=>e.stopPropagation()} style={{width:450}}>
                <h3 className="text-lg font-bold text-primary mb-16">🎤 ایجاد تسک با صدا</h3>
                <div className="flex gap-8 items-center mb-16">
                    <button className={`btn ${recording?'btn-danger recording':'btn-primary'}`}
                        onClick={recording?stopRec:startRec}>
                        {recording?'⏹ توقف':'▶ شروع ضبط'}
                    </button>
                    {audioBlob && !result && (
                        <button className="btn btn-success" onClick={processVoice} disabled={loading}>
                            {loading?'⏳ پردازش...':'🔍 تبدیل به متن'}
                        </button>
                    )}
                </div>
                <div className="flex gap-8 mb-16">
                    <input className="input" placeholder="یا متن تایپ کنید: مثلا آقای نگین لیست بفرست" value={testText} onChange={e=>setTestText(e.target.value)} style={{flex:1}}/>
                    <button className="btn btn-ghost" onClick={processTestText} disabled={loading || !testText.trim()}>تست</button>
                </div>
                {rawText && <div className="glass-card mb-16"><label>متن تشخیص داده شده:</label><p style={{fontSize:13,lineHeight:1.8}}>{rawText}</p></div>}
                {error && <div className="text-danger mb-16">{error}</div>}
                {/* دکمه نمایش لاگ */}
                <div className="flex gap-8 mb-16">
                    <button className="btn btn-ghost" style={{fontSize:11}} onClick={()=>{setShowLog(!showLog);if(!showLog)fetchDebugLog();}}>
                        {showLog?'پنهان کردن لاگ':'نمایش لاگ (دیباگ)'}
                    </button>
                </div>
                {showLog && (
                    <div className="glass-card mb-16" style={{maxHeight:300,overflow:'auto'}}>
                        <div className="flex justify-between items-center mb-8">
                            <label style={{fontSize:12,color:'#00FFFF'}}>لاگ دیباگ:</label>
                            <button className="btn btn-ghost" style={{fontSize:10}} onClick={fetchDebugLog}>بروزرسانی</button>
                        </div>
                        <pre style={{fontSize:10,color:'#a0a0c0',whiteSpace:'pre-wrap',direction:'ltr',textAlign:'left'}}>{debugLog || 'لاگی وجود ندارد'}</pre>
                    </div>
                )}

                {result && (
                    <div>
                        <div className="form-group"><label>عنوان تسک:</label>
                            <input className="input" value={result.title} onChange={e=>setResult({...result,title:e.target.value})} /></div>
                        <div className="form-group"><label>توضیحات:</label>
                            <textarea className="input" value={result.notes} onChange={e=>setResult({...result,notes:e.target.value})} /></div>

                        {/* انتخاب مسئول با جستجو */}
                        <div className="form-group" style={{position:'relative'}}>
                            <label>مسئول انجام:</label>
                            <input className="input" value={userSearch || result.assigned_to||''}
                                onChange={e=>{setUserSearch(e.target.value);setShowUserSearch(true);setResult({...result,assigned_to:e.target.value});}}
                                onFocus={()=>setShowUserSearch(true)}
                                placeholder="جستجوی نام کاربر..."/>
                            {showUserSearch && searchResults.length > 0 && (
                                <div style={{position:'absolute',top:'100%',left:0,right:0,background:'#1a1a2e',border:'1px solid #303055',borderRadius:8,maxHeight:200,overflow:'auto',zIndex:100}}>
                                    {searchResults.map(u=>(
                                        <div key={u.id} onClick={()=>selectUser(u)}
                                            style={{padding:'8px 12px',cursor:'pointer',borderBottom:'1px solid #303055',display:'flex',alignItems:'center',gap:8}}>
                                            <div style={{width:28,height:28,borderRadius:14,background:'rgba(0,255,255,0.2)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:12,color:'#00FFFF'}}>
                                                {(u.full_name||u.username)[0]}
                                            </div>
                                            <div>
                                                <div style={{fontSize:13,color:'#e0e0f0'}}>{u.full_name||u.username}</div>
                                                <div style={{fontSize:10,color:'#64748B'}}>{u.role} | @{u.username}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="flex gap-12">
                            <div className="form-group" style={{flex:1}}>
                                <label>اولویت:</label>
                                <select className="input" value={result.priority} onChange={e=>setResult({...result,priority:e.target.value})}>
                                    <option value="مهم">مهم</option>
                                    <option value="خیلی مهم">خیلی مهم</option>
                                    <option value="غیر مهم">غیر مهم</option>
                                </select>
                            </div>
                            <div className="form-group" style={{flex:1}}>
                                <label>فوریت:</label>
                                <select className="input" value={result.urgency||'غیر فوری'} onChange={e=>setResult({...result,urgency:e.target.value})}>
                                    <option value="غیر فوری">غیر فوری</option>
                                    <option value="فوری">فوری</option>
                                    <option value="ضروری">ضروری</option>
                                </select>
                            </div>
                        </div>

                        <div className="flex gap-12">
                            <div className="form-group" style={{flex:1}}><label>فرصت (روز):</label>
                                <input className="input" placeholder="مثال: 3" value={result.time_given||''} onChange={e=>setResult({...result,time_given:e.target.value})} /></div>
                            <div className="form-group" style={{flex:1}}><label>موعد (شمسی):</label>
                                <input className="input" placeholder="1405/04/10" value={result.deadline||''} onChange={e=>setResult({...result,deadline:e.target.value})} /></div>
                        </div>

                        <button className="btn btn-primary w-full" onClick={saveTask}>ذخیره تسک</button>
                    </div>
                )}
                <div className="mt-16" style={{textAlign:'center'}}><button className="btn btn-ghost" onClick={onClose}>بستن</button></div>
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════
//  DASHBOARD
// ═══════════════════════════════════════════════

function Dashboard() {
    const [tasks, setTasks] = useState([]);
    const [progress, setProgress] = useState(null);
    const [matrix, setMatrix] = useState(null);

    useEffect(() => {
        apiGet('/api/tasks').then(r => r && setTasks(r));
        apiGet('/api/progress/summary').then(r => r && setProgress(r));
        apiGet('/api/tasks/matrix').then(r => r && setMatrix(r));
    }, []);

    const active = tasks.filter(t => !['تکمیل','منتفی'].includes(t.status)).length;
    const completed = tasks.filter(t => t.status === 'تکمیل').length;
    const cancelled = tasks.filter(t => t.status === 'منتفی').length;
    const pctComplete = progress?.pct_complete || (tasks.length > 0 ? Math.round(completed / tasks.length * 100) : 0);
    const avgProgress = progress?.avg_progress || 0;
    const personnel = {};
    tasks.forEach(t => { if (t.assigned_to) personnel[t.assigned_to] = (personnel[t.assigned_to]||0) + 1; });

    const Ring = ({pct, color, size=60}) => {
        const r = (size-8)/2, c = 2*Math.PI*r;
        return (
            <svg width={size} height={size} style={{transform:'rotate(-90deg)'}}>
                <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6"/>
                <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="6"
                    strokeDasharray={c} strokeDashoffset={c*(1-pct/100)} strokeLinecap="round"
                    style={{transition:'stroke-dashoffset 1s ease'}}/>
            </svg>
        );
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-16">
                <div>
                    <h2 className="text-lg font-bold">داشبورد</h2>
                    <div className="text-dim text-sm">نمای کلی وضعیت کارها</div>
                </div>
                <div className="flex items-center gap-8">
                    <div style={{width:8,height:8,borderRadius:4,background:'#00FF99'}}/>
                    <span className="text-sm text-dim">آنلاین</span>
                </div>
            </div>

            <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12,marginBottom:16}}>
                <div className="glass-card" style={{padding:16,height:155,display:'flex',flexDirection:'column',justifyContent:'space-between'}}>
                    <div className="flex justify-between items-center">
                        <span className="text-dim text-sm">کل کارها</span>
                        <div style={{width:28,height:28,borderRadius:7,background:'rgba(0,255,255,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>📋</div>
                    </div>
                    <div className="value" style={{color:'#00FFFF',fontSize:32}}>{tasks.length}</div>
                    <div style={{height:3,background:'rgba(255,255,255,0.06)',borderRadius:2}}>
                        <div style={{height:'100%',width:'100%',background:'#00FFFF',borderRadius:2,transition:'width 1s'}}/>
                    </div>
                </div>
                <div className="glass-card" style={{padding:16,height:155,display:'flex',flexDirection:'column',justifyContent:'space-between'}}>
                    <div className="flex justify-between items-center">
                        <span className="text-dim text-sm">در حال انجام</span>
                        <div style={{width:28,height:28,borderRadius:7,background:'rgba(255,215,0,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>⏳</div>
                    </div>
                    <div className="value" style={{color:'#FFD700',fontSize:32}}>{active}</div>
                    <div style={{height:3,background:'rgba(255,255,255,0.06)',borderRadius:2}}>
                        <div style={{height:'100%',width:`${tasks.length?active/tasks.length*100:0}%`,background:'#FFD700',borderRadius:2,transition:'width 1s'}}/>
                    </div>
                </div>
                <div className="glass-card" style={{padding:16,height:155,display:'flex',flexDirection:'column',justifyContent:'space-between'}}>
                    <div className="flex justify-between items-center">
                        <span className="text-dim text-sm">تکمیل شده</span>
                        <div style={{width:28,height:28,borderRadius:7,background:'rgba(0,255,153,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>✅</div>
                    </div>
                    <div className="flex items-center gap-8">
                        <div className="value" style={{color:'#00FF99',fontSize:32}}>{completed}</div>
                        <Ring pct={pctComplete} color="#00FF99"/>
                    </div>
                    <div style={{height:3,background:'rgba(255,255,255,0.06)',borderRadius:2}}>
                        <div style={{height:'100%',width:`${pctComplete}%`,background:'#00FF99',borderRadius:2,transition:'width 1s'}}/>
                    </div>
                </div>
                <div className="glass-card" style={{padding:16,height:155,display:'flex',flexDirection:'column',justifyContent:'space-between'}}>
                    <div className="flex justify-between items-center">
                        <span className="text-dim text-sm">پیشرفت میانگین</span>
                        <div style={{width:28,height:28,borderRadius:7,background:'rgba(157,78,221,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>📈</div>
                    </div>
                    <div className="value" style={{color:'#9D4EDD',fontSize:32}}>{avgProgress}%</div>
                    <div style={{height:3,background:'rgba(255,255,255,0.06)',borderRadius:2}}>
                        <div style={{height:'100%',width:`${avgProgress}%`,background:'#9D4EDD',borderRadius:2,transition:'width 1s'}}/>
                    </div>
                </div>
            </div>

            {/* ماتریس آیزنهاور در داشبورد */}
            {matrix && (
                <div className="glass-card mb-16">
                    <div className="flex items-center gap-8 mb-16">
                        <div style={{width:28,height:28,borderRadius:7,background:'rgba(255,0,85,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>📊</div>
                        <span className="font-bold text-sm">ماتریس آیزنهاور - اولویت‌بندی خودکار</span>
                    </div>
                    <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
                        {[1,2,3,4].map(level => {
                            const colors = {1:'#FF0055',2:'#FFD700',3:'#00FFFF',4:'#64748B'};
                            const bgColors = {1:'rgba(255,0,85,0.08)',2:'rgba(255,215,0,0.08)',3:'rgba(0,255,255,0.08)',4:'rgba(100,116,139,0.08)'};
                            const count = matrix.matrix[level]?.length || 0;
                            return (
                                <div key={level} style={{background:bgColors[level],border:`1px solid ${colors[level]}33`,borderRadius:12,padding:12}}>
                                    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                                        <span style={{color:colors[level],fontWeight:600,fontSize:11}}>{matrix.labels[level]}</span>
                                        <span style={{background:colors[level]+'22',color:colors[level],padding:'2px 8px',borderRadius:12,fontSize:11,fontWeight:600}}>
                                            {count}
                                        </span>
                                    </div>
                                    {matrix.matrix[level]?.slice(0,2).map(t => (
                                        <div key={t.id} style={{background:'rgba(0,0,0,0.2)',borderRadius:6,padding:6,marginBottom:4,fontSize:10,color:'#e0e0f0'}}>
                                            {t.title?.substring(0,25)}
                                        </div>
                                    ))}
                                    {count > 2 && <div style={{color:'#64748B',fontSize:9,textAlign:'center'}}>و {count-2} مورد دیگر</div>}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12,marginBottom:16}}>
                <div className="glass-card">
                    <div className="flex items-center gap-8 mb-16">
                        <div style={{width:28,height:28,borderRadius:7,background:'rgba(0,255,255,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>📊</div>
                        <span className="font-bold text-sm">توزیع وضعیت</span>
                    </div>
                    <div style={{display:'flex',gap:16,alignItems:'center'}}>
                        <div style={{position:'relative'}}>
                            <Ring pct={100} color="#FFD700" size={100}/>
                            <div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',flexDirection:'column'}}>
                                <span style={{fontSize:20,fontWeight:700,color:'#fff'}}>{pctComplete}%</span>
                                <span style={{fontSize:9,color:'#64748B'}}>تکمیل</span>
                            </div>
                        </div>
                        <div style={{flex:1}}>
                            <div style={{display:'flex',justifyContent:'space-between',marginBottom:8}}>
                                <div className="flex items-center gap-4"><div style={{width:10,height:10,borderRadius:2,background:'#FFD700'}}/><span className="text-sm">در حال انجام ({active})</span></div>
                                <span className="text-sm font-bold" style={{color:'#FFD700'}}>{tasks.length?Math.round(active/tasks.length*100):0}%</span>
                            </div>
                            <div style={{height:6,background:'rgba(255,255,255,0.06)',borderRadius:3,marginBottom:8}}>
                                <div style={{height:'100%',width:`${tasks.length?active/tasks.length*100:0}%`,background:'#FFD700',borderRadius:3}}/>
                            </div>
                            <div style={{display:'flex',justifyContent:'space-between',marginBottom:8}}>
                                <div className="flex items-center gap-4"><div style={{width:10,height:10,borderRadius:2,background:'#00FF99'}}/><span className="text-sm">تکمیل ({completed})</span></div>
                                <span className="text-sm font-bold" style={{color:'#00FF99'}}>{pctComplete}%</span>
                            </div>
                            <div style={{height:6,background:'rgba(255,255,255,0.06)',borderRadius:3,marginBottom:8}}>
                                <div style={{height:'100%',width:`${pctComplete}%`,background:'#00FF99',borderRadius:3}}/>
                            </div>
                            <div style={{display:'flex',justifyContent:'space-between'}}>
                                <div className="flex items-center gap-4"><div style={{width:10,height:10,borderRadius:2,background:'#64748B'}}/><span className="text-sm">منتفی ({cancelled})</span></div>
                                <span className="text-sm font-bold" style={{color:'#64748B'}}>{tasks.length?Math.round(cancelled/tasks.length*100):0}%</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="glass-card">
                    <div className="flex items-center gap-8 mb-16">
                        <div style={{width:28,height:28,borderRadius:7,background:'rgba(157,78,221,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>👥</div>
                        <span className="font-bold text-sm">کارهای پرسنل</span>
                    </div>
                    {Object.entries(personnel).sort((a,b)=>b[1]-a[1]).slice(0,6).map(([name,count])=>(
                        <div key={name} style={{display:'flex',alignItems:'center',gap:8,marginBottom:8}}>
                            <span style={{minWidth:80,fontSize:12,color:'#e0e0f0'}}>{name.substring(0,12)}</span>
                            <div style={{flex:1,height:8,background:'rgba(255,255,255,0.06)',borderRadius:4,overflow:'hidden'}}>
                                <div style={{height:'100%',width:`${Math.min(100,count/Math.max(...Object.values(personnel))*100)}%`,background:'linear-gradient(90deg,#9D4EDD,#00FFFF)',borderRadius:4,transition:'width 1s'}}/>
                            </div>
                            <span style={{fontSize:11,color:'#9D4EDD',fontWeight:600,minWidth:20,textAlign:'left'}}>{count}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="glass-card">
                <div className="flex items-center gap-8 mb-16">
                    <div style={{width:28,height:28,borderRadius:7,background:'rgba(255,0,85,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>📋</div>
                    <span className="font-bold text-sm">آخرین کارها</span>
                </div>
                <table className="table"><thead><tr><th>عنوان</th><th>مسئول</th><th>وضعیت</th><th>پیشرفت</th><th>موعد</th></tr></thead>
                <tbody>{tasks.slice(0,8).map(t=>(
                    <tr key={t.id}>
                        <td className="font-bold">{t.title?.substring(0,40)}</td>
                        <td className="text-primary">{t.assigned_to||'—'}</td>
                        <td><span className="status-badge" style={{background:({'در حال انجام':'#00FFFF22','تکمیل':'#00FF9922','منتفی':'#64748B22','پیگیری مستمر':'#FFD70022'}[t.status]||'#64748B22'),color:{'در حال انجام':'#00FFFF','تکمیل':'#00FF99','منتفی':'#64748B','پیگیری مستمر':'#FFD700'}[t.status]||'#64748B'}}>{t.status}</span></td>
                        <td><div style={{display:'flex',alignItems:'center',gap:6}}>
                            <div style={{width:60,height:4,borderRadius:2,background:'rgba(255,255,255,0.06)',overflow:'hidden'}}>
                                <div style={{width:`${(t.progress||0)*100}%`,height:'100%',background:'#00FF99',borderRadius:2}}/></div>
                            <span className="text-sm">{Math.round((t.progress||0)*100)}%</span></div></td>
                        <td className="text-sm">{t.deadline||'—'}</td>
                    </tr>))}</tbody></table>
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════
//  EISENHOWER MATRIX
// ═══════════════════════════════════════════════

function EisenhowerMatrix() {
    const [matrix, setMatrix] = useState(null);

    useEffect(() => {
        apiGet('/api/tasks/matrix').then(r => r && setMatrix(r));
    }, []);

    if (!matrix) return <div className="glass-card mb-16">در حال بارگذاری...</div>;

    const colors = {1:'#FF0055',2:'#FFD700',3:'#00FFFF',4:'#64748B'};
    const bgColors = {1:'rgba(255,0,85,0.08)',2:'rgba(255,215,0,0.08)',3:'rgba(0,255,255,0.08)',4:'rgba(100,116,139,0.08)'};

    return (
        <div className="glass-card mb-16">
            <div className="flex items-center gap-8 mb-16">
                <div style={{width:28,height:28,borderRadius:7,background:'rgba(255,0,85,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>📊</div>
                <span className="font-bold text-sm">ماتریس آیزنهاور</span>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12}}>
                {[1,2,3,4].map(level => (
                    <div key={level} style={{background:bgColors[level],border:`1px solid ${colors[level]}33`,borderRadius:12,padding:12}}>
                        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                            <span style={{color:colors[level],fontWeight:600,fontSize:12}}>{matrix.labels[level]}</span>
                            <span style={{background:colors[level]+'22',color:colors[level],padding:'2px 8px',borderRadius:12,fontSize:11}}>
                                {matrix.matrix[level]?.length || 0}
                            </span>
                        </div>
                        {matrix.matrix[level]?.slice(0,3).map(t => (
                            <div key={t.id} style={{background:'rgba(0,0,0,0.2)',borderRadius:6,padding:8,marginBottom:6,fontSize:11,color:'#e0e0f0'}}>
                                <div style={{fontWeight:500}}>{t.title?.substring(0,30)}</div>
                                {t.assigned_to && <div style={{color:'#64748B',fontSize:10,marginTop:2}}>مسئول: {t.assigned_to}</div>}
                            </div>
                        ))}
                        {(matrix.matrix[level]?.length || 0) > 3 && (
                            <div style={{color:'#64748B',fontSize:10,textAlign:'center'}}>و {matrix.matrix[level].length - 3} مورد دیگر...</div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════
//  TASKS
// ═══════════════════════════════════════════════

function TasksView({ user }) {
    const [tasks, setTasks] = useState([]);
    const [showForm, setShowForm] = useState(false);
    const [showMatrix, setShowMatrix] = useState(false);
    const [editTask, setEditTask] = useState(null);
    const [form, setForm] = useState({title:'',requester:'',priority:'مهم',urgency:'غیر فوری',level:3,assigned_to:'',status:'در حال انجام',progress:0,deadline:'',notes:'',time_given:''});
    const [users, setUsers] = useState([]);
    const [userSearch, setUserSearch] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [showUserSearch, setShowUserSearch] = useState(false);
    const [reqSearch, setReqSearch] = useState('');
    const [reqResults, setReqResults] = useState([]);
    const [showReqSearch, setShowReqSearch] = useState(false);

    const reload = () => { apiGet('/api/tasks').then(r=>r&&setTasks(r)); };
    useEffect(() => { reload(); apiGet('/api/users').then(r=>r&&setUsers(r)); }, [showForm]);

    // جستجوی کاربر برای مسئول انجام
    useEffect(() => {
        if (userSearch.length > 0) {
            apiGet(`/api/users/search?q=${encodeURIComponent(userSearch)}`).then(r => {
                if (r) setSearchResults(r);
            });
        } else {
            setSearchResults(users.slice(0, 10));
        }
    }, [userSearch, users]);

    // جستجوی کاربر برای مرجع
    useEffect(() => {
        if (reqSearch.length > 0) {
            apiGet(`/api/users/search?q=${encodeURIComponent(reqSearch)}`).then(r => {
                if (r) setReqResults(r);
            });
        } else {
            setReqResults(users.slice(0, 10));
        }
    }, [reqSearch, users]);

    // محاسبه خودکار سطح آیزنهاور
    useEffect(() => {
        const level = calculateLevel(form.priority, form.urgency);
        setForm(prev => ({...prev, level}));
    }, [form.priority, form.urgency]);

    // محاسبه خودکار فرصت وقتی موعد تغییر کنه
    useEffect(() => {
        if (form.deadline) {
            try {
                const parts = form.deadline.split('/');
                if (parts.length === 3) {
                    const jy=parseInt(parts[0]), jm=parseInt(parts[1]), jd=parseInt(parts[2]);
                    let jdn=365*jy+Math.floor((jy+33)/8)*8+Math.floor((jy%33+3)/4)+jd;
                    for(let i=0;i<jm-1;i++) jdn+=[0,31,31,31,31,31,30,30,30,30,30,29][i];
                    const gdn=jdn-79;
                    let gy=1600+Math.floor(400*gdn/146097);gdn%=146097;
                    if(gdn>=36525){gdn--;gy+=Math.floor(100*gdn/36524);gdn%=36524;if(gdn>=365)gdn++;}
                    gy+=Math.floor(4*gdn/1461);gdn%=1461;if(gdn>=366){gdn--;gy+=Math.floor(gdn/365);gdn%=365;}
                    const dm=[31,((gy%4===0&&gy%100!==0)||gy%400===0)?29:28,31,30,31,30,31,31,30,31,30,31];
                    let gm=1,gdd=1;for(let i=0;i<12;i++){if(gdn<dm[i]){gm=i+1;gdd=gdn+1;break;}gdn-=dm[i];}
                    const dl=new Date(gy,gm-1,gdd);const now=new Date();now.setHours(0,0,0,0);
                    const diff=Math.ceil((dl-now)/(1000*60*60*24));
                    setForm(prev => ({...prev, time_given: String(Math.max(diff, 0))}));
                }
            } catch(e) {}
        }
    }, [form.deadline]);

    const calculateLevel = (priority, urgency) => {
        const isImportant = priority === 'مهم' || priority === 'خیلی مهم';
        const isUrgent = urgency === 'فوری' || urgency === 'ضروری';
        if (isImportant && isUrgent) return 1;
        if (isImportant && !isUrgent) return 2;
        if (!isImportant && isUrgent) return 3;
        return 4;
    };

    const getLevelLabel = (level) => {
        const labels = {1:'فوری و مهم',2:'مهم - برنامه‌ریزی',3:'غیرمهم - واگذاری',4:'حذف/حذف'};
        return labels[level] || 'نامشخص';
    };

    const getLevelColor = (level) => {
        return {1:'#FF0055',2:'#FFD700',3:'#00FFFF',4:'#64748B'}[level] || '#64748B';
    };

    const saveTask = async () => {
        if (!form.title.trim()) return;
        if (editTask) {
            await fetch(`/api/tasks/${editTask.id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + AUTH_TOKEN},
                body: JSON.stringify(form)
            });
        } else {
            await apiPost('/api/tasks', form);
        }
        setShowForm(false);
        setEditTask(null);
        reload();
    };

    const editTaskFn = (task) => {
        setEditTask(task);
        setForm({
            title: task.title || '',
            requester: task.requester || '',
            priority: task.priority || 'مهم',
            urgency: task.urgency || 'غیر فوری',
            level: task.level || 3,
            assigned_to: task.assigned_to || '',
            status: task.status || 'در حال انجام',
            progress: task.progress || 0,
            deadline: task.deadline || '',
            notes: task.notes || '',
            time_given: task.time_given || ''
        });
        setUserSearch(task.assigned_to || '');
        setShowForm(true);
    };

    const updateProgress = async (taskId, progress) => {
        await fetch(`/api/tasks/${taskId}/progress`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + AUTH_TOKEN},
            body: JSON.stringify({ progress: progress })
        });
        reload();
    };

    const deleteTask = async (id) => {
        if (!confirm('حذف شود؟')) return;
        await fetch(`/api/tasks/${id}`, { method:'DELETE', headers:{'Authorization':'Bearer '+AUTH_TOKEN} });
        reload();
    };
    const sc = s => ({'در حال انجام':'#00FFFF','تکمیل':'#00FF99','منتفی':'#64748B','پیگیری مستمر':'#FFD700'}[s]||'#64748B');

    const selectUser = (u) => {
        setForm({...form, assigned_to: u.full_name || u.username});
        setUserSearch(u.full_name || u.username);
        setShowUserSearch(false);
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-16">
                <h2 className="text-lg font-bold">کارها ({tasks.length})</h2>
                <div className="flex gap-8">
                    <button className="btn btn-ghost" onClick={()=>setShowMatrix(!showMatrix)}>ماتریس آیزنهاور</button>
                    <button className="btn btn-primary" onClick={()=>{setForm({...form,requester:user?.full_name||''});setShowForm(true);}}>+ کار جدید</button>
                </div>
            </div>

            {/* ماتریس آیزنهاور */}
            {showMatrix && <EisenhowerMatrix />}

            <div className="glass-card" style={{overflowX:'auto'}}>
                <table className="table"><thead><tr><th>عنوان</th><th>مسئول</th><th>مرجع</th><th>وضعیت</th><th>پیشرفت</th><th>فرصت</th><th>موعد</th><th>مانده</th><th>عملیات</th></tr></thead>
                <tbody>{tasks.map(t=>{
                    const tg = t.time_given ? parseInt(t.time_given) : 0;
                    const tgDisplay = tg > 0 ? `${tg} روز` : '—';

                    // مانده از سرور
                    const remaining = t.remaining_days;
                    const daysLeft = (() => {
                        if (remaining !== undefined && remaining !== null) {
                            if (remaining < 0) return <span style={{color:'var(--danger)',fontWeight:600}}>سررسید گذشته</span>;
                            if (remaining === 0) return <span style={{color:'var(--warning)',fontWeight:600}}>امروز</span>;
                            return <span style={{color:remaining<=3?'var(--warning)':'var(--success)',fontWeight:600}}>{remaining} روز</span>;
                        }
                        return '—';
                    })();

                    return (
                    <tr key={t.id}>
                        <td className="font-bold" style={{maxWidth:150,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{t.title?.substring(0,35)}</td>
                        <td className="text-primary" style={{fontSize:11}}>{t.assigned_to||'—'}</td>
                        <td style={{fontSize:11,color:'var(--success)'}}>{t.requester||'—'}</td>
                        <td><span className="status-badge" style={{background:sc(t.status)+'22',color:sc(t.status)}}>{t.status}</span></td>
                        <td>
                            <div style={{display:'flex',alignItems:'center',gap:4}}>
                                <div style={{width:50,height:4,borderRadius:2,background:'var(--input-border,#303055)',overflow:'hidden'}}>
                                    <div style={{width:`${(t.progress||0)*100}%`,height:'100%',background:'var(--success)',borderRadius:2}}/>
                                </div>
                                <input type="range" min="0" max="100" value={Math.round((t.progress||0)*100)}
                                    style={{width:50,height:12,cursor:'pointer',accentColor:'var(--primary)'}}
                                    onChange={(e)=>updateProgress(t.id, e.target.value/100)}/>
                                <span className="text-sm">{Math.round((t.progress||0)*100)}%</span>
                            </div>
                        </td>
                        <td className="text-sm" style={{fontWeight:600,color:tg>0?'var(--primary)':'var(--dim)'}}>{tgDisplay}</td>
                        <td className="text-sm">{t.deadline||'—'}</td>
                        <td className="text-sm">{daysLeft}</td>
                        <td style={{whiteSpace:'nowrap'}}>
                            {t.status !== 'تکمیل' && t.status !== 'منتفی' && (
                                <button className="btn btn-ghost" style={{padding:'4px 8px',fontSize:11,color:'var(--success)'}} onClick={async()=>{await fetch(`/api/tasks/${t.id}`,{method:'PUT',headers:{'Content-Type':'application/json','Authorization':'Bearer '+AUTH_TOKEN},body:JSON.stringify({status:'تکمیل',progress:1})});reload();}}>✅</button>
                            )}
                            <button className="btn btn-ghost" style={{padding:'4px 8px',fontSize:11}} onClick={()=>editTaskFn(t)}>✏️</button>
                            <button className="btn btn-ghost" style={{padding:'4px 8px',fontSize:11}} onClick={()=>deleteTask(t.id)}>🗑</button>
                        </td>
                    </tr>);})}</tbody></table>
            </div>

            {/* فرم کار جدید/ویرایش */}
            {showForm && (
                <div className="modal-overlay" onClick={()=>{setShowForm(false);setEditTask(null);}}>
                    <div className="modal" onClick={e=>e.stopPropagation()} style={{maxWidth:600}}>
                        <h3 className="text-lg font-bold text-primary mb-16">{editTask ? 'ویرایش کار' : 'کار جدید'}</h3>
                        <div className="form-group"><label>عنوان *</label><input className="input" value={form.title} onChange={e=>setForm({...form,title:e.target.value})}/></div>

                        <div className="flex gap-12">
                            <div className="form-group" style={{flex:1,position:'relative'}}>
                                <label>مرجع (فرستنده)</label>
                                <input className="input" value={reqSearch || form.requester}
                                    onChange={e=>{setReqSearch(e.target.value);setShowReqSearch(true);setForm({...form,requester:e.target.value});}}
                                    onFocus={()=>setShowReqSearch(true)}
                                    placeholder="جستجوی نام کاربر..."/>
                                {showReqSearch && reqResults.length > 0 && (
                                    <div style={{position:'absolute',top:'100%',left:0,right:0,background:'var(--input-bg,#1a1a2e)',border:'1px solid var(--input-border,#303055)',borderRadius:8,maxHeight:180,overflow:'auto',zIndex:100}}>
                                        {reqResults.map(u=>(
                                            <div key={u.id} onClick={()=>{setForm({...form,requester:u.full_name||u.username});setReqSearch(u.full_name||u.username);setShowReqSearch(false);}}
                                                style={{padding:'8px 12px',cursor:'pointer',borderBottom:'1px solid var(--input-border,#303055)',display:'flex',alignItems:'center',gap:8,fontSize:12,color:'var(--text,#e0e0f0)'}}>
                                                <span style={{fontWeight:600}}>{u.full_name||u.username}</span>
                                                <span style={{fontSize:10,color:'var(--text-dim,#64748B)'}}>{u.role}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <div className="form-group" style={{flex:1}}><label>موعد (شمسی)</label>
                                <input className="input" placeholder="1405/04/10" value={form.deadline} onChange={e=>setForm({...form,deadline:e.target.value})}/></div>
                            <div className="form-group" style={{flex:1}}><label>فرصت (روز)</label>
                                <input className="input" value={form.time_given||''} readOnly style={{background:'var(--input-bg)',color:'var(--primary)',fontWeight:700}}/></div>
                        </div>

                        {/* انتخاب مسئول با جستجو */}
                        <div className="form-group" style={{position:'relative'}}>
                            <label>مسئول انجام</label>
                            <input className="input" value={userSearch || form.assigned_to}
                                onChange={e=>{setUserSearch(e.target.value);setShowUserSearch(true);setForm({...form,assigned_to:e.target.value});}}
                                onFocus={()=>setShowUserSearch(true)}
                                placeholder="جستجوی نام کاربر..."/>
                            {showUserSearch && searchResults.length > 0 && (
                                <div style={{position:'absolute',top:'100%',left:0,right:0,background:'#1a1a2e',border:'1px solid #303055',borderRadius:8,maxHeight:200,overflow:'auto',zIndex:100}}>
                                    {searchResults.map(u=>(
                                        <div key={u.id} onClick={()=>selectUser(u)}
                                            style={{padding:'8px 12px',cursor:'pointer',borderBottom:'1px solid #303055',display:'flex',alignItems:'center',gap:8}}>
                                            <div style={{width:28,height:28,borderRadius:14,background:'rgba(0,255,255,0.2)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:12,color:'#00FFFF'}}>
                                                {(u.full_name||u.username)[0]}
                                            </div>
                                            <div>
                                                <div style={{fontSize:13,color:'#e0e0f0'}}>{u.full_name||u.username}</div>
                                                <div style={{fontSize:10,color:'#64748B'}}>{u.role} | @{u.username}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="flex gap-12">
                            <div className="form-group" style={{flex:1}}>
                                <label>اولویت (اهمیت)</label>
                                <select className="input" value={form.priority} onChange={e=>setForm({...form,priority:e.target.value})}>
                                    <option value="مهم">مهم</option>
                                    <option value="خیلی مهم">خیلی مهم</option>
                                    <option value="غیر مهم">غیر مهم</option>
                                </select>
                            </div>
                            <div className="form-group" style={{flex:1}}>
                                <label>فوریت</label>
                                <select className="input" value={form.urgency} onChange={e=>setForm({...form,urgency:e.target.value})}>
                                    <option value="غیر فوری">غیر فوری</option>
                                    <option value="فوری">فوری</option>
                                    <option value="ضروری">ضروری</option>
                                </select>
                            </div>
                        </div>

                        {/* نمایش سطح آیزنهاور */}
                        <div className="glass-card" style={{padding:12,marginBottom:12,background:getLevelColor(form.level)+'11',border:`1px solid ${getLevelColor(form.level)}33`}}>
                            <div style={{display:'flex',alignItems:'center',gap:8}}>
                                <span style={{fontSize:12,color:'#64748B'}}>سطح آیزنهاور:</span>
                                <span className="status-badge" style={{background:getLevelColor(form.level)+'22',color:getLevelColor(form.level)}}>
                                    {getLevelLabel(form.level)}
                                </span>
                            </div>
                        </div>

                        <div className="form-group"><label>توضیحات</label><textarea className="input" value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}/></div>
                        <div className="flex gap-8 mt-16" style={{justifyContent:'flex-end'}}>
                            <button className="btn btn-ghost" onClick={()=>{setShowForm(false);setEditTask(null);}}>لغو</button>
                            <button className="btn btn-primary" onClick={saveTask}>{editTask ? 'بروزرسانی' : 'ذخیره'}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// ═══════════════════════════════════════════════
//  CHAT
// ═══════════════════════════════════════════════

function ChatView({ user, socket, dmTarget, setDmTarget, chatMode, setChatMode }) {
    const mode = chatMode;
    const setMode = setChatMode;
    const [sections, setSections] = useState([]);
    const [selSection, setSelSection] = useState(user.section_id);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [file, setFile] = useState(null);
    const [dmMsgs, setDmMsgs] = useState([]);
    const [allUsers, setAllUsers] = useState([]);
    const [dmContacts, setDmContacts] = useState([]);
    const [contextMenu, setContextMenu] = useState(null);
    const [convertingVoice, setConvertingVoice] = useState(null);
    const fileRef = useRef(null);
    const endRef = useRef(null);
    const { theme } = useTheme();

    useEffect(() => {
        apiGet('/api/sections').then(r=>r&&setSections(r));
        apiGet('/api/users').then(r=>r&&setAllUsers(r));
        apiGet('/api/dm/contacts').then(r=>r&&setDmContacts(r));
    }, []);

    useEffect(() => {
        if (mode === 'group' && selSection) {
            apiGet(`/api/chat/${selSection}`).then(r=>r&&setMessages(r));
            socket.emit('join_section', { section_id: selSection });
        }
    }, [mode, selSection]);

    useEffect(() => {
        if (mode === 'dm' && dmTarget) {
            apiGet(`/api/dm/${dmTarget}`).then(r=>r&&setDmMsgs(r));
            socket.emit('join_user', { user_id: user.id });
            // بروزرسانی مخاطبین
            apiGet('/api/dm/contacts').then(r=>r&&setDmContacts(r));
        }
    }, [mode, dmTarget]);

    useEffect(() => {
        socket.on('new_message', msg => { if (msg.section_id === selSection) setMessages(p => [...p, msg]); });
        socket.on('new_dm', msg => {
            if ((msg.sender_id === user.id && msg.receiver_id === dmTarget) ||
                (msg.sender_id === dmTarget && msg.receiver_id === user.id)) {
                setDmMsgs(p => [...p, msg]);
            }
        });
        return () => { socket.off('new_message'); socket.off('new_dm'); };
    }, [selSection, dmTarget]);

    useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, dmMsgs]);

    // بستن منوی راست‌کلیک با کلیک هر جا
    useEffect(() => {
        const handleClick = () => setContextMenu(null);
        document.addEventListener('click', handleClick);
        return () => document.removeEventListener('click', handleClick);
    }, []);

    const send = async (content, type, fd) => {
        if (mode === 'group') {
            if (!fd) fd = new FormData();
            if (content) fd.append('content', content);
            fd.append('msg_type', type || 'text');
            await apiUpload(`/api/chat/${selSection}`, fd);
        } else {
            if (!fd) fd = new FormData();
            if (content) fd.append('content', content);
            fd.append('msg_type', type || 'text');
            await apiUpload(`/api/dm/${dmTarget}`, fd);
        }
    };

    const handleSend = async () => {
        if (!input.trim() && !file) return;
        if (file) {
            const fd = new FormData(); fd.append('file', file); fd.append('content', input);
            await send(input, 'file', fd); setFile(null);
        } else { await send(input, 'text'); }
        setInput('');
    };

    const handleVoice = async (blob) => {
        const fd = new FormData(); fd.append('voice', blob, 'voice.wav'); fd.append('content', '');
        await send('', 'voice', fd);
    };

    // تبدیل پیام صوتی به وظیفه
    const convertVoiceToTask = async (msg) => {
        setConvertingVoice(msg.id);
        setContextMenu(null);

        try {
            // دریافت فایل صوتی
            const voiceUrl = msg.voice_url;
            if (!voiceUrl) {
                alert('فایل صوتی یافت نشد');
                setConvertingVoice(null);
                return;
            }

            const response = await fetch(voiceUrl);
            const blob = await response.blob();

            // مسئول انجام = دریافت‌کننده پیام
            const fd = new FormData();
            fd.append('voice', blob, 'voice.wav');
            const receiverId = (msg.sender_id === user.id) ? dmTarget : user.id;
            fd.append('receiver_id', receiverId);
            // مرجع = صادرکننده پیام
            fd.append('requester_id', msg.sender_id);

            const r = await fetch('/api/ai/voice-to-task-from-chat', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + AUTH_TOKEN },
                body: fd
            });

            const data = await r.json();
            if (data.ok) {
                alert(`وظیفه ایجاد شد!\nعنوان: ${data.title}\nمسئول: ${data.assigned_to || 'ندارد'}\nموعد: ${data.deadline || 'امروز'}`);
            } else {
                alert(data.error || 'خطا در تبدیل صدا به وظیفه');
            }
        } catch (err) {
            alert('خطا: ' + err.message);
        }
        setConvertingVoice(null);
    };

    // تبدیل متن به وظیفه - مرجع = فرستنده پیام، مسئول انجام = دریافت‌کننده پیام
    const convertTextToTask = async (msg) => {
        setContextMenu(null);
        // دریافت‌کننده پیام = مسئول انجام
        const receiverId = (msg.sender_id === user.id) ? dmTarget : user.id;
        // فرستنده پیام = مرجع درخواست
        const requesterId = msg.sender_id;
        const r = await apiPost('/api/ai/create-task-from-chat', { text: msg.content, receiver_id: receiverId, requester_id: requesterId });
        if (r?.ok) {
            alert('وظیفه ایجاد شد!');
        } else {
            alert(r?.error || 'خطا');
        }
    };

    // نمایش منوی راست‌کلیک
    const handleContextMenu = (e, msg) => {
        e.preventDefault();
        setContextMenu({
            x: e.clientX,
            y: e.clientY,
            msg: msg
        });
    };

    const renderMsg = (msg, idx) => {
        const isMe = msg.sender_id === user.id;

        // پیام سیستمی - رندر به صورت کارت
        if (msg.msg_type === 'system' && msg.content) {
            const parts = msg.content.split('|');
            if (parts[0] === '[SYSTEM_PROGRESS]' && parts.length >= 6) {
                const [, taskId, title, pct, updater, assignee, mref] = parts;
                return (
                    <div key={idx} style={{maxWidth:350,margin:'8px auto',padding:12,borderRadius:12,border:`1px solid ${theme.primary}44`,background:theme.cardBg}}>
                        <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:8}}>
                            <span style={{fontSize:16}}>📈</span>
                            <span style={{fontSize:12,fontWeight:700,color:theme.primary}}>بروزرسانی پیشرفت</span>
                            <span style={{fontSize:10,color:theme.textDim}}>{msg.created_at?.substring(0,16)}</span>
                        </div>
                        <div style={{fontSize:13,color:theme.text,marginBottom:6}}>تسک «<b>{title}</b>»</div>
                        <div style={{display:'flex',alignItems:'center',gap:6,marginBottom:6}}>
                            <div style={{flex:1,height:5,borderRadius:3,background:theme.inputBorder,overflow:'hidden'}}>
                                <div style={{width:`${pct}%`,height:'100%',background:parseInt(pct)>=100?theme.success:parseInt(pct)>=50?theme.primary:theme.warning,borderRadius:3}}/>
                            </div>
                            <span style={{fontSize:13,fontWeight:700,color:theme.primary}}>{pct}%</span>
                        </div>
                        <div style={{fontSize:11,color:theme.textDim}}>توسط <span style={{color:theme.secondary,fontWeight:600}}>{updater}</span></div>
                        <div style={{fontSize:10,color:theme.textDim,marginTop:2}}>مسئول: <span style={{color:theme.warning}}>{assignee}</span> | مرجع: <span style={{color:theme.success}}>{mref}</span></div>
                    </div>
                );
            }
            if (parts[0] === '[SYSTEM_COMPLETE]' && parts.length >= 5) {
                const [, taskId, title, assignee, mref] = parts;
                return (
                    <div key={idx} style={{maxWidth:350,margin:'8px auto',padding:12,borderRadius:12,border:`1px solid ${theme.success}44`,background:theme.cardBg}}>
                        <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:8}}>
                            <span style={{fontSize:16}}>✅</span>
                            <span style={{fontSize:12,fontWeight:700,color:theme.success}}>تسک تکمیل شد!</span>
                            <span style={{fontSize:10,color:theme.textDim}}>{msg.created_at?.substring(0,16)}</span>
                        </div>
                        <div style={{fontSize:13,color:theme.text}}>موضوع «<b>{title}</b>» توسط <span style={{color:theme.warning,fontWeight:600}}>{assignee}</span> تکمیل شد</div>
                        <div style={{fontSize:10,color:theme.textDim,marginTop:4}}>مرجع: <span style={{color:theme.success}}>{mref}</span></div>
                    </div>
                );
            }
            return null;
        }

        const isTask = !isMe && msg.content && msg.content.length > 10 &&
            /(بفرست|بده|انجام|تکمیل|آماده|جمع|ارسال|بررسی|تهیه|درست|لیست|حساب|موجودی|گزارش|باید|لازم|فوری|مهم|تا شنبه|تا فردا|تا پس فردا|هفته بعد|برای تیم)/.test(msg.content);

        return (
            <div key={idx} className={`chat-msg ${isMe?'me':'other'}`}
                onContextMenu={(e) => handleContextMenu(e, msg)}>
                {!isMe && <div className="sender">{msg.sender_name}</div>}
                {msg.msg_type === 'voice' && msg.voice_url && (
                    <div className="voice-badge" onClick={()=>new Audio(msg.voice_url).play()}>
                        {convertingVoice === msg.id ? '⏳ در حال تبدیل...' : '▶ پیام صوتی'}
                    </div>)}
                {msg.content && <div>{msg.content}</div>}
                {msg.file_name && <a className="file-badge" href={msg.file_url} target="_blank" download>📎 {msg.file_name}</a>}
                {isTask && <button className="btn btn-ghost" style={{fontSize:10,padding:'2px 8px',marginTop:4}} onClick={()=>convertTextToTask(msg)}>🤖 تبدیل به تسک</button>}
                <div className="time">{msg.created_at?.substring(11,16)}</div>
            </div>
        );
    };

    // رندر کارت‌های تسک و پیشرفت
    const currentMsgs = mode === 'group' ? messages : dmMsgs;
    const members = allUsers.filter(u => u.section_id === selSection && u.id !== user.id);

    return (
        <div className="chat-container">
            <div className="flex gap-8 mb-16">
                <button className={`btn ${mode==='group'?'btn-primary':'btn-ghost'}`} onClick={()=>{setMode('group');setDmTarget(null);}}>چت گروهی</button>
                <button className={`btn ${mode==='dm'?'btn-primary':'btn-ghost'}`} onClick={()=>setMode('dm')}>پیام خصوصی</button>
                {mode==='group' && <select className="input" style={{width:200}} value={selSection||''} onChange={e=>setSelSection(Number(e.target.value))}>
                    {sections.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select>}
                {mode==='dm' && !dmTarget && (
                    <div style={{flex:1}}>
                        <div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}>
                            {dmContacts.length > 0 && dmContacts.map(c=>(
                                <div key={c.id} onClick={()=>setDmTarget(c.id)}
                                    style={{display:'flex',alignItems:'center',gap:8,padding:'8px 14px',background:c.unread_count>0?'rgba(255,0,85,0.15)':'rgba(255,255,255,0.05)',border:'1px solid '+(c.unread_count>0?'#FF0055':'#303055'),borderRadius:12,cursor:'pointer',position:'relative',minWidth:200}}>
                                    <div style={{width:32,height:32,borderRadius:16,background:'rgba(0,255,255,0.2)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:13,color:'#00FFFF',flexShrink:0}}>
                                        {(c.full_name||c.username)[0]}
                                    </div>
                                    <div style={{flex:1,minWidth:0}}>
                                        <div style={{fontSize:12,color:c.unread_count>0?'#fff':'#e0e0f0',fontWeight:c.unread_count>0?700:500}}>{c.full_name||c.username}</div>
                                        <div style={{fontSize:10,color:'#64748B',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:150}}>{c.preview||''}</div>
                                    </div>
                                    {c.unread_count>0 && <span style={{background:'#FF0055',color:'#fff',fontSize:9,padding:'2px 6px',borderRadius:10,flexShrink:0}}>{c.unread_count}</span>}
                                </div>
                            ))}
                            <select className="input" style={{width:200}} onChange={e=>{if(e.target.value)setDmTarget(Number(e.target.value));}}>
                                <option value="">جستجوی کاربر...</option>
                                {allUsers.filter(u=>u.id!==user.id).map(u=><option key={u.id} value={u.id}>{u.full_name||u.username}</option>)}
                            </select>
                        </div>
                    </div>
                )}
            </div>
            {mode==='dm' && dmTarget && (
                <div className="flex gap-8 mb-16 items-center">
                    <button className="btn btn-ghost" onClick={()=>setDmTarget(null)}>برگشت</button>
                    <span className="font-bold">{allUsers.find(u=>u.id===dmTarget)?.full_name}</span>
                </div>)}
            <div className="flex gap-16" style={{flex:1,overflow:'hidden'}}>
                {mode==='group' && <div className="member-list">
                    <div className="text-primary font-bold text-sm mb-16">اعضای بخش</div>
                    {members.map(m=>(<div key={m.id} className="member-item">
                        <div className="member-avatar">{(m.full_name||m.username)[0]}</div>
                        <div><div>{m.full_name||m.username}</div><div className="text-dim" style={{fontSize:10}}>{m.role}</div></div>
                    </div>))}</div>}
                <div style={{flex:1,display:'flex',flexDirection:'column'}}>
                    <div className="chat-messages" style={{flex:1}}>
                        {currentMsgs.map((m,i)=>renderMsg(m,i))}
                        <div ref={endRef}/></div>
                    {file && <div className="p-16 text-primary text-sm">📎 {file.name}</div>}
                    <div className="chat-input">
                        <VoiceRecorder onVoiceReady={handleVoice}/>
                        <button className="btn btn-ghost" onClick={()=>fileRef.current.click()}>📎</button>
                        <input ref={fileRef} type="file" style={{display:'none'}} onChange={e=>e.target.files[0]&&setFile(e.target.files[0])}/>
                        <input className="input" placeholder="پیام..." value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handleSend()}/>
                        <button className="btn btn-primary" onClick={handleSend}>ارسال</button>
                    </div>
                </div>
            </div>

            {/* منوی راست‌کلیک */}
            {contextMenu && (
                <div style={{
                    position: 'fixed',
                    left: contextMenu.x,
                    top: contextMenu.y,
                    background: '#1a1a2e',
                    border: '1px solid #303055',
                    borderRadius: 8,
                    padding: '8px 0',
                    minWidth: 180,
                    zIndex: 1000,
                    boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
                }}>
                    {contextMenu.msg.msg_type === 'voice' && (
                        <div onClick={() => convertVoiceToTask(contextMenu.msg)}
                            style={{padding: '8px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13}}
                            onMouseEnter={(e) => e.target.style.background = '#303055'}
                            onMouseLeave={(e) => e.target.style.background = 'transparent'}>
                            🎤 تبدیل صدا به وظیفه
                        </div>
                    )}
                    {contextMenu.msg.content && (
                        <div onClick={() => convertTextToTask(contextMenu.msg)}
                            style={{padding: '8px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13}}
                            onMouseEnter={(e) => e.target.style.background = '#303055'}
                            onMouseLeave={(e) => e.target.style.background = 'transparent'}>
                            📋 تبدیل متن به وظیفه
                        </div>
                    )}
                    <div onClick={() => {navigator.clipboard.writeText(contextMenu.msg.content || ''); setContextMenu(null);}}
                        style={{padding: '8px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13}}
                        onMouseEnter={(e) => e.target.style.background = '#303055'}
                        onMouseLeave={(e) => e.target.style.background = 'transparent'}>
                        📄 کپی متن
                    </div>
                </div>
            )}
        </div>
    );
}

// ═══════════════════════════════════════════════
//  SECTIONS
// ═══════════════════════════════════════════════

function SectionsView() {
    const [sections, setSections] = useState([]);
    const [showForm, setShowForm] = useState(false);
    const [name, setName] = useState('');
    const [desc, setDesc] = useState('');
    useEffect(() => { apiGet('/api/sections').then(r=>r&&setSections(r)); }, [showForm]);
    const save = async () => { if (!name.trim()) return; await apiPost('/api/sections',{name,description:desc}); setShowForm(false); setName(''); setDesc(''); };
    return (
        <div>
            <div className="flex justify-between items-center mb-16"><h2 className="text-lg font-bold">بخش‌ها</h2>
                <button className="btn btn-primary" onClick={()=>setShowForm(true)}>+ بخش جدید</button></div>
            <div className="flex gap-12" style={{flexWrap:'wrap'}}>
                {sections.map(s=>(<div key={s.id} className="glass-card" style={{width:260}}>
                    <h3 className="font-bold text-primary">{s.name}</h3>
                    <p className="text-dim text-sm mt-8">{s.description||'بدون توضیح'}</p>
                    <div className="mt-16"><span className="status-badge" style={{background:'rgba(0,255,255,0.1)',color:'#00FFFF'}}>{s.member_count||0} عضو</span></div>
                </div>))}
            </div>
            {showForm && <div className="modal-overlay" onClick={()=>setShowForm(false)}>
                <div className="modal" onClick={e=>e.stopPropagation()}>
                    <h3 className="text-lg font-bold text-primary mb-16">بخش جدید</h3>
                    <div className="form-group"><label>نام</label><input className="input" value={name} onChange={e=>setName(e.target.value)}/></div>
                    <div className="form-group"><label>توضیحات</label><textarea className="input" value={desc} onChange={e=>setDesc(e.target.value)}/></div>
                    <div className="flex gap-8 mt-16" style={{justifyContent:'flex-end'}}>
                        <button className="btn btn-ghost" onClick={()=>setShowForm(false)}>لغو</button>
                        <button className="btn btn-primary" onClick={save}>ذخیره</button></div>
                </div></div>}
        </div>
    );
}

// ═══════════════════════════════════════════════
//  EXCEL IMPORT WITH FIELD MAPPING (Admin only)
// ═══════════════════════════════════════════════

function ExcelImportModal({ onClose, onDone }) {
    const { theme } = useTheme();
    const [step, setStep] = useState('upload'); // upload | mapping | importing | done
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [mapping, setMapping] = useState({});
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const fileRef = useRef(null);

    const DB_FIELDS = [
        { value: '', label: '-- بدون نگاشت --' },
        { value: 'full_name', label: 'نام کامل (full_name)' },
        { value: 'username', label: 'نام کاربری / کد پرسنلی (username)' },
        { value: 'password', label: 'رمز عبور (password)' },
        { value: 'section', label: 'دپارتمان / بخش (section)' },
        { value: 'role', label: 'نقش (role)' },
        { value: 'is_active', label: 'فعال/غیرفعال (is_active)' },
    ];

    const AUTO_MAP = {
        'نام': 'full_name',
        'نام کامل': 'full_name',
        'کد پرسنلی': 'username',
        'کد': 'username',
        'رمز': 'password',
        'رمز عبور': 'password',
        'پسورد': 'password',
        'password': 'password',
        'دپارتمان': 'section',
        'بخش': 'section',
        'دپارتمان‌ها': 'section',
        'نقش': 'role',
        'فعال': 'is_active',
        'وضعیت': 'is_active',
    };

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true); setError('');
        const fd = new FormData();
        fd.append('file', file);
        try {
            const r = await fetch('/api/import/excel/preview', {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + AUTH_TOKEN }, body: fd
            });
            const data = await r.json();
            if (data.error) { setError(data.error); setLoading(false); return; }
            setPreview(data);

            // نگاشت خودکار بر اساس نام ستون‌ها (بدون حساسیت به حروف)
            const autoMap = {};
            data.headers.forEach(h => {
                const cleanH = h.trim();
                const lowerH = cleanH.toLowerCase();
                // جستجو در کلیدهای AUTO_MAP (بدون حساسیت)
                for (const [key, val] of Object.entries(AUTO_MAP)) {
                    if (key.toLowerCase() === lowerH) {
                        autoMap[cleanH] = val;
                        break;
                    }
                }
            });
            setMapping(autoMap);
            setStep('mapping');
        } catch (e) {
            setError('خطا در آپلود فایل');
        }
        setLoading(false);
    };

    const handleImport = async () => {
        setLoading(true); setError(''); setStep('importing');
        try {
            const r = await fetch('/api/import/excel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + AUTH_TOKEN },
                body: JSON.stringify({ filename: preview.filename, mapping })
            });
            const data = await r.json();
            if (data.error) { setError(data.error); setStep('mapping'); setLoading(false); return; }
            setResult(data);
            setStep('done');
            if (data.count > 0 && onDone) onDone();
        } catch (e) {
            setError('خطا در ایمپورت'); setStep('mapping');
        }
        setLoading(false);
    };

    const handleFileChange = (e) => {
        const f = e.target.files[0];
        if (f) { setFile(f); setPreview(null); setStep('upload'); }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()} style={{maxWidth: 600, maxHeight: '80vh', overflow: 'auto'}}>
                <div className="flex justify-between items-center mb-16">
                    <h3 className="text-lg font-bold" style={{color: theme.primary}}>ایمپورت کاربران از اکسل</h3>
                    <button className="btn btn-ghost" onClick={onClose} style={{fontSize: 18}}>&times;</button>
                </div>

                {/* Step 1: Upload */}
                {step === 'upload' && (
                    <div>
                        <div style={{border:`2px dashed ${theme.inputBorder}`, borderRadius:12, padding:32, textAlign:'center', cursor:'pointer', background: theme.cardBg}}
                             onClick={() => fileRef.current?.click()}>
                            <div style={{fontSize:32, marginBottom:8}}>📊</div>
                            <div style={{color: theme.text, fontWeight:600, marginBottom:4}}>
                                {file ? file.name : 'فایل اکسل رو اینجا بکشید یا کلیک کنید'}
                            </div>
                            <div style={{color: theme.textDim, fontSize:11}}>
                                فرمت‌های پشتیبانی شده: .xlsx, .xls
                            </div>
                            <input ref={fileRef} type="file" accept=".xlsx,.xls" style={{display:'none'}} onChange={handleFileChange}/>
                        </div>
                        {file && (
                            <div style={{marginTop:16}}>
                                <div style={{display:'flex',gap:8,alignItems:'center',marginBottom:12}}>
                                    <span style={{color:theme.text}}>فایل انتخاب شده:</span>
                                    <span style={{color:theme.primary,fontWeight:600}}>{file.name}</span>
                                </div>
                                <button className="btn btn-primary w-full" onClick={handleUpload} disabled={loading}>
                                    {loading ? 'در حال خواندن فایل...' : 'مرحله بعد: نگاشت فیلدها'}
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* Step 2: Mapping */}
                {step === 'mapping' && preview && (
                    <div>
                        <div className="glass-card mb-16" style={{padding:12}}>
                            <div style={{color:theme.textDim, fontSize:12, marginBottom:8}}>
                                فایل: <strong style={{color:theme.primary}}>{preview.filename}</strong> | تعداد ردیف: <strong style={{color:theme.primary}}>{preview.total_rows}</strong>
                            </div>
                            <div style={{color:theme.text, fontSize:12}}>
                                برای هر ستون اکسل، مشخص کنید کدام فیلد دیتابیس باشد.
                            </div>
                        </div>

                        {/* نمایش نمونه داده */}
                        {preview.sample_rows.length > 0 && (
                            <div style={{overflowX:'auto', marginBottom:16}}>
                                <table style={{width:'100%', borderCollapse:'collapse', fontSize:11}}>
                                    <thead>
                                        <tr>
                                            {preview.headers.map((h, i) => (
                                                <th key={i} style={{padding:'6px 8px', background:theme.inputBg, color:theme.primary, border:`1px solid ${theme.inputBorder}`, textAlign:'right', whiteSpace:'nowrap'}}>
                                                    {h}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {preview.sample_rows.map((row, ri) => (
                                            <tr key={ri}>
                                                {row.map((cell, ci) => (
                                                    <td key={ci} style={{padding:'4px 8px', border:`1px solid ${theme.inputBorder}`, color:theme.text, whiteSpace:'nowrap'}}>
                                                        {cell || <span style={{color:theme.textDim}}>خالی</span>}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}

                        {/* نگاشت فیلدها */}
                        <div style={{color:theme.text, fontWeight:600, marginBottom:8, fontSize:13}}>نگاشت فیلدها:</div>
                        {preview.headers.map((h, i) => (
                            <div key={i} style={{display:'flex', alignItems:'center', gap:8, marginBottom:8, padding:'6px 10px', background:theme.cardBg, borderRadius:8, border:`1px solid ${theme.cardBorder}`}}>
                                <span style={{flex:1, color:theme.text, fontSize:12, fontWeight:600}}>{h}</span>
                                <span style={{color:theme.textDim, fontSize:11}}>&rarr;</span>
                                <select className="input" style={{flex:1, margin:0, padding:'4px 8px', fontSize:12}}
                                    value={mapping[h] || ''} onChange={e => setMapping({...mapping, [h]: e.target.value})}>
                                    {DB_FIELDS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                                </select>
                            </div>
                        ))}

                        <div className="flex gap-8 mt-16" style={{justifyContent:'flex-end'}}>
                            <button className="btn btn-ghost" onClick={() => setStep('upload')}>بازگشت</button>
                            <button className="btn btn-primary" onClick={handleImport} disabled={loading}>
                                شروع ایمپورت ({preview.total_rows} ردیف)
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 3: Importing */}
                {step === 'importing' && (
                    <div style={{textAlign:'center', padding:32}}>
                        <div style={{fontSize:32, marginBottom:12}}>⏳</div>
                        <div style={{color:theme.text}}>در حال ایمپورت...</div>
                    </div>
                )}

                {/* Step 4: Done */}
                {step === 'done' && result && (
                    <div style={{textAlign:'center', padding:24}}>
                        <div style={{fontSize:40, marginBottom:12}}>{result.count > 0 ? '✅' : '⚠️'}</div>
                        <div style={{color:theme.text, fontWeight:600, fontSize:16, marginBottom:8}}>{result.message}</div>
                        {result.errors && result.errors.length > 0 && (
                            <div style={{textAlign:'right', marginTop:16}}>
                                <div style={{color:theme.danger, fontWeight:600, marginBottom:8}}>خطاها:</div>
                                {result.errors.map((e, i) => (
                                    <div key={i} style={{color:theme.textDim, fontSize:11, marginBottom:4}}>{e}</div>
                                ))}
                            </div>
                        )}
                        <button className="btn btn-primary mt-16" onClick={onClose}>بستن</button>
                    </div>
                )}

                {error && <div style={{color:theme.danger, marginTop:12, fontSize:12, textAlign:'center'}}>{error}</div>}
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════
//  USERS
// ═══════════════════════════════════════════════

function UsersView() {
    const [users, setUsers] = useState([]);
    const [showForm, setShowForm] = useState(false);
    const [editUser, setEditUser] = useState(null);
    const [form, setForm] = useState({username:'',password:'',full_name:'',role:'user',section_id:null});
    const [sections, setSections] = useState([]);
    const [showExcelImport, setShowExcelImport] = useState(false);
    const refresh = () => { apiGet('/api/users').then(r=>r&&setUsers(r)); apiGet('/api/sections').then(r=>r&&setSections(r)); };
    useEffect(() => { refresh(); }, [showForm]);
    const rl = r => ({admin:'ادمین',manager:'مدیر',user:'کاربر'}[r]||r);
    const rc = r => ({admin:'#FF0055',manager:'#00FFFF',user:'#00FF99'}[r]||'#64748B');
    const save = async () => {
        if (!form.username.trim()) return;
        if (editUser) {
            await fetch(`/api/users/${editUser.id}`, {method:'PUT',headers:{'Content-Type':'application/json','Authorization':'Bearer '+AUTH_TOKEN},body:JSON.stringify(form)});
        } else {
            await apiPost('/api/users', form);
        }
        setShowForm(false); setEditUser(null);
    };
    const editFn = (u) => {
        setEditUser(u);
        setForm({username:u.username, password:'', full_name:u.full_name||'', role:u.role||'user', section_id:u.section_id});
        setShowForm(true);
    };
    return (
        <div>
            <div className="flex justify-between items-center mb-16"><h2 className="text-lg font-bold">کاربران</h2>
                <div className="flex gap-8">
                    <button className="btn btn-ghost" onClick={()=>setShowExcelImport(true)}>📊 ایمپورت از اکسل</button>
                    <button className="btn btn-primary" onClick={()=>{setEditUser(null);setForm({username:'',password:'',full_name:'',role:'user',section_id:null});setShowForm(true);}}>+ کاربر جدید</button>
                </div>
            </div>
            <div className="flex gap-12" style={{flexWrap:'wrap'}}>
                {users.map(u=>(<div key={u.id} className="glass-card" style={{width:260}}>
                    <div className="flex gap-8 items-center">
                        <div className="member-avatar" style={{background:rc(u.role)}}>{(u.full_name||u.username)[0]}</div>
                        <div><div className="font-bold">{u.full_name||u.username}</div><div className="text-dim text-sm">@{u.username}</div></div>
                    </div>
                    <div className="mt-8">
                        <span className="status-badge" style={{background:rc(u.role)+'22',color:rc(u.role)}}>{rl(u.role)}</span>
                        <span className="text-dim text-sm" style={{marginRight:8}}>{u.section_name||'ندارد'}</span>
                    </div>
                    <div className="mt-8 flex gap-8">
                        <button className="btn btn-ghost" style={{fontSize:11,padding:'4px 12px'}} onClick={()=>editFn(u)}>ویرایش</button>
                        <button className="btn btn-ghost" style={{fontSize:11,padding:'4px 12px',color:'#FF0055'}} onClick={async()=>{if(!confirm('حذف شود؟'))return;await fetch(`/api/users/${u.id}`,{method:'DELETE',headers:{'Authorization':'Bearer '+AUTH_TOKEN}});apiGet('/api/users').then(r=>r&&setUsers(r));}}>حذف</button>
                    </div>
                </div>))}
            </div>
            {showForm && <div className="modal-overlay" onClick={()=>setShowForm(false)}>
                <div className="modal" onClick={e=>e.stopPropagation()}>
                    <h3 className="text-lg font-bold text-primary mb-16">{editUser?'ویرایش کاربر':'کاربر جدید'}</h3>
                    <div className="form-group"><label>نام کاربری *</label><input className="input" value={form.username} onChange={e=>setForm({...form,username:e.target.value})} disabled={!!editUser}/></div>
                    <div className="form-group"><label>{editUser?'رمز جدید (خالی = بدون تغییر)':'رمز'}</label><input className="input" type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} placeholder={editUser?'برای تغییر رمز پر کنید':''}/></div>
                    <div className="form-group"><label>نام کامل</label><input className="input" value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}/></div>
                    <div className="flex gap-12">
                        <div className="form-group" style={{flex:1}}><label>نقش</label>
                            <select className="input" value={form.role} onChange={e=>setForm({...form,role:e.target.value})}>
                                <option value="user">کاربر</option><option value="manager">مدیر</option><option value="admin">ادمین</option></select></div>
                        <div className="form-group" style={{flex:1}}><label>بخش</label>
                            <select className="input" value={form.section_id||''} onChange={e=>setForm({...form,section_id:e.target.value?Number(e.target.value):null})}>
                                <option value="">ندارد</option>{sections.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></div>
                    </div>
                    <div className="flex gap-8 mt-16" style={{justifyContent:'flex-end'}}>
                        <button className="btn btn-ghost" onClick={()=>setShowForm(false)}>لغو</button>
                        <button className="btn btn-primary" onClick={save}>ذخیره</button></div>
                </div></div>}
            {showExcelImport && <ExcelImportModal onClose={()=>setShowExcelImport(false)} onDone={refresh}/>}
        </div>
    );
}

// ═══════════════════════════════════════════════
//  ALARMS
// ═══════════════════════════════════════════════

function AlarmsView() {
    const [alarms, setAlarms] = useState([]);
    useEffect(() => { apiGet('/api/alarms').then(r=>r&&setAlarms(r)); }, []);
    const markAll = async () => { await apiPost('/api/alarms/read'); apiGet('/api/alarms').then(r=>r&&setAlarms(r)); };
    return (
        <div>
            <div className="flex justify-between items-center mb-16"><h2 className="text-lg font-bold">آلارم‌ها</h2>
                <button className="btn btn-ghost" onClick={markAll}>همه خوانده شد</button></div>
            {alarms.map(a=>(
                <div key={a.id} className="glass-card mb-16" style={{borderRight:`3px solid ${a.ack?'#303055':'#FF0055'}`}}>
                    <div className="flex justify-between items-center">
                        <span>{a.message}</span>
                        <span className="text-dim text-sm">{a.alarm_time?.substring(0,16)}</span>
                    </div>
                </div>))}
        </div>
    );
}

// ═══════════════════════════════════════════════
//  SETTINGS
// ═══════════════════════════════════════════════

function SettingsView({ user }) {
    const { theme, themeKey, setTheme } = useTheme();
    const [customColors, setCustomColors] = useState(() => {
        const saved = localStorage.getItem('customColors');
        return saved ? JSON.parse(saved) : {};
    });

    const themes = [
        { key: 'dark_neon', name: 'دارک نئون', icon: '🌙', desc: 'تاریک با رنگ‌های نئون' },
        { key: 'gray_neutral', name: 'خاکستری خنثی', icon: '🔘', desc: 'خاکستری با رنگ‌های ملایم' },
        { key: 'light', name: 'روشن', icon: '☀️', desc: 'روشن و ساده' },
    ];

    const colorFields = [
        { key: 'primary', label: 'رنگ اصلی' },
        { key: 'secondary', label: 'رنگ فرعی' },
        { key: 'success', label: 'رنگ موفقیت' },
        { key: 'danger', label: 'رنگ خطا' },
        { key: 'warning', label: 'رنگ هشدار' },
        { key: 'bg', label: 'رنگ پس‌زمینه' },
        { key: 'sidebarBg', label: 'رنگ سایدبار' },
    ];

    const handleColorChange = (key, value) => {
        const newColors = {...customColors, [key]: value};
        setCustomColors(newColors);
        localStorage.setItem('customColors', JSON.stringify(newColors));
        document.documentElement.style.setProperty(`--${key}`, value);
    };

    const resetColors = () => {
        setCustomColors({});
        localStorage.removeItem('customColors');
        themes.forEach(t => {
            Object.entries(THEMES[t.key]).forEach(([k, v]) => {
                if (!['name'].includes(k)) {
                    document.documentElement.style.setProperty(`--${k}`, v);
                }
            });
        });
    };

    useEffect(() => {
        Object.entries(customColors).forEach(([k, v]) => {
            document.documentElement.style.setProperty(`--${k}`, v);
        });
    }, []);

    return (
        <div>
            <div className="flex justify-between items-center mb-16">
                <h2 className="text-lg font-bold">تنظیمات</h2>
            </div>

            <div className="glass-card mb-16">
                <div className="flex items-center gap-8 mb-16">
                    <div style={{width:28,height:28,borderRadius:7,background:'rgba(0,255,255,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>🎨</div>
                    <span className="font-bold text-sm">انتخاب تم</span>
                </div>
                <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:16}}>
                    {themes.map(t => {
                        const isActive = themeKey === t.key;
                        const tc = THEMES[t.key];
                        return (
                            <div key={t.key} onClick={() => setTheme(t.key)}
                                style={{
                                    padding:20, borderRadius:12, cursor:'pointer',
                                    background: tc.bg,
                                    border: `2px solid ${isActive ? tc.primary : tc.cardBorder}`,
                                    transition: 'all 0.2s ease',
                                    position:'relative', overflow:'hidden'
                                }}>
                                {isActive && <div style={{position:'absolute',top:8,right:8,background:tc.primary,color:tc.bg,padding:'2px 8px',borderRadius:8,fontSize:10,fontWeight:700}}>فعال</div>}
                                <div style={{fontSize:32,marginBottom:8}}>{t.icon}</div>
                                <div style={{color:tc.text,fontWeight:700,fontSize:14,marginBottom:4}}>{t.name}</div>
                                <div style={{color:tc.textDim,fontSize:11}}>{t.desc}</div>
                                <div style={{display:'flex',gap:6,marginTop:12}}>
                                    <div style={{width:20,height:20,borderRadius:4,background:tc.primary}}/>
                                    <div style={{width:20,height:20,borderRadius:4,background:tc.secondary}}/>
                                    <div style={{width:20,height:20,borderRadius:4,background:tc.success}}/>
                                    <div style={{width:20,height:20,borderRadius:4,background:tc.danger}}/>
                                    <div style={{width:20,height:20,borderRadius:4,background:tc.warning}}/>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            <div className="glass-card mb-16">
                <div className="flex items-center gap-8 mb-16">
                    <div style={{width:28,height:28,borderRadius:7,background:'rgba(157,78,221,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>🖌️</div>
                    <span className="font-bold text-sm">شخصی‌سازی رنگ‌ها</span>
                </div>
                <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
                    {colorFields.map(f => (
                        <div key={f.key} style={{display:'flex',flexDirection:'column',alignItems:'center',gap:6,padding:12,background:theme.cardBg,borderRadius:8,border:`1px solid ${theme.cardBorder}`}}>
                            <label style={{fontSize:11,color:theme.textDim}}>{f.label}</label>
                            <input type="color" value={customColors[f.key] || THEMES[themeKey][f.key] || '#000000'}
                                onChange={e => handleColorChange(f.key, e.target.value)}
                                style={{width:40,height:40,border:'none',borderRadius:8,cursor:'pointer',background:'transparent'}}/>
                        </div>
                    ))}
                </div>
                <button className="btn btn-ghost mt-16" style={{fontSize:11}} onClick={resetColors}>بازنشانی رنگ‌ها</button>
            </div>

            <div className="glass-card mb-16">
                <div className="flex items-center gap-8 mb-16">
                    <div style={{width:28,height:28,borderRadius:7,background:'rgba(0,255,255,0.12)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>👤</div>
                    <span className="font-bold text-sm">اطلاعات حساب</span>
                </div>
                <div className="flex gap-16">
                    <div><span className="text-dim text-sm">نام کامل:</span> <span className="font-bold">{user.full_name}</span></div>
                    <div><span className="text-dim text-sm">نام کاربری:</span> <span className="font-bold">@{user.username}</span></div>
                    <div><span className="text-dim text-sm">نقش:</span> <span className="font-bold">{user.role === 'admin' ? 'ادمین' : user.role === 'manager' ? 'مدیر' : 'کاربر'}</span></div>
                </div>
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════
//  MAIN APP
// ═══════════════════════════════════════════════

const APP_VERSION = 'v2.2.4';

function AppInner() {
    const [user, setUser] = useState(null);
    const [view, setView] = useState('dashboard');
    const [socket, setSocket] = useState(null);
    const [now, setNow] = useState(new Date());
    const { theme } = useTheme();

    useEffect(() => {
        const timer = setInterval(() => setNow(new Date()), 60000);
        return () => clearInterval(timer);
    }, []);

    useEffect(() => {
        if (AUTH_TOKEN) {
            apiGet('/api/me').then(r => { if (r?.id) setUser(r); else clearToken(); });
        }
    }, []);

    // تابع پخش صدای نوتیفیکیشن
    const playNotificationSound = () => {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = 800;
            osc.type = 'sine';
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.3);
        } catch (e) {}
    };

    const [inAppNotification, setInAppNotification] = useState(null);
    const [unreadDM, setUnreadDM] = useState(0);
    const [chatDmTarget, setChatDmTarget] = useState(null);
    const [chatMode, setChatMode] = useState('group');

    const showInAppNotification = (title, body, senderId) => {
        setInAppNotification({ title, body, senderId });
        setTimeout(() => setInAppNotification(null), 8000);
    };

    useEffect(() => {
        if (user) {
            // درخواست دسترسی نوتیفیکیشن
            if ('Notification' in window) {
                if (Notification.permission === 'default') {
                    Notification.requestPermission();
                }
            }
            const s = io();
            s.emit('join_user', { user_id: user.id });

            // نوتیفیکیشن پیام جدید گروهی
            s.on('new_message', msg => {
                playNotificationSound();
                if ('Notification' in window && Notification.permission === 'granted') {
                    new Notification('پیام جدید', { body: msg.sender_name + ': ' + (msg.content || 'پیام صوتی') });
                } else {
                    // نوتیفیکیشن داخلی
                    showInAppNotification('پیام جدید', msg.sender_name + ': ' + (msg.content || 'پیام صوتی'));
                }
            });

            // نوتیفیکیشن پیام خصوصی
            s.on('new_dm', msg => {
                playNotificationSound();
                setUnreadDM(prev => prev + 1);
                if ('Notification' in window && Notification.permission === 'granted') {
                    new Notification('پیام خصوصی از ' + msg.sender_name, { body: msg.content || 'پیام صوتی' });
                } else {
                    showInAppNotification('پیام خصوصی از ' + msg.sender_name, msg.content || 'پیام صوتی', msg.sender_id);
                }
            });

            // نوتیفیکیشن آلارم
            s.on('alarm', data => {
                playNotificationSound();
                if ('Notification' in window && Notification.permission === 'granted') {
                    new Notification('آلارم', { body: data.message });
                } else {
                    showInAppNotification('آلارم', data.message);
                }
            });

            setSocket(s);
            return () => s.disconnect();
        }
    }, [user]);

    const handleLogout = () => {
        apiPost('/api/logout'); clearToken(); setUser(null); setSocket(null);
    };

    if (!user) return <LoginPage onLogin={setUser} />;
    if (!socket) return <div style={{textAlign:'center',padding:100}}>در حال اتصال...</div>;

    const nav = [
        {id:'dashboard',icon:'📊',label:'داشبورد'},{id:'tasks',icon:'📋',label:'کارها'},
        {id:'chat',icon:'💬',label:'چت',badge: unreadDM > 0 ? unreadDM : null},
        ...(user.role==='admin' ? [{id:'sections',icon:'🏢',label:'بخش‌ها'},{id:'users',icon:'👥',label:'کاربران'}] : []),
        {id:'alarms',icon:'🔔',label:'آلارم‌ها'},
        {id:'settings',icon:'⚙️',label:'تنظیمات'},
    ];
    const views = {
        dashboard: <Dashboard/>, tasks: <TasksView user={user}/>,
        chat: <ChatView user={user} socket={socket} dmTarget={chatDmTarget} setDmTarget={setChatDmTarget} chatMode={chatMode} setChatMode={setChatMode}/>,
        sections: <SectionsView/>, users: <UsersView/>, alarms: <AlarmsView/>,
        settings: <SettingsView user={user}/>,
    };

    return (
        <div className="app" style={{background:theme.bg,color:theme.text}}>
            {/* نوتیفیکیشن داخلی */}
            {inAppNotification && (
                <div style={{
                    position:'fixed',top:16,right:16,zIndex:9999,
                    background:'linear-gradient(135deg,#1a1a2e,#16213e)',
                    border:'1px solid #00FFFF',
                    borderRadius:12,padding:'12px 20px',
                    boxShadow:'0 4px 20px rgba(0,255,255,0.2)',
                    maxWidth:350,cursor:'pointer',
                    animation:'slideIn 0.3s ease'
                }} onClick={()=>{
                    setInAppNotification(null);
                    if (inAppNotification.senderId) {
                        setView('chat');
                        setChatDmTarget(inAppNotification.senderId);
                        setChatMode('dm');
                    }
                }}>
                    <div style={{color:'#00FFFF',fontWeight:700,fontSize:13,marginBottom:4}}>{inAppNotification.title}</div>
                    <div style={{color:'#e0e0f0',fontSize:12}}>{inAppNotification.body}</div>
                    <div style={{color:'#64748B',fontSize:10,marginTop:4}}>کلیک کنید تا پاسخ دهید</div>
                </div>
            )}
            <div className="sidebar">
                <div className="logo"><div style={{fontSize:30}}>⚡</div><h2>مدیریت امور</h2><p>بازرگانی محسنی</p></div>
                {nav.map(n=>(<div key={n.id} className={`nav-item ${view===n.id?'active':''}`} onClick={()=>{setView(n.id);if(n.id==='chat')setUnreadDM(0);}}>
                    <span className="icon">{n.icon}</span><span>{n.label}</span>
                    {n.badge && <span style={{background:'#FF0055',color:'#fff',fontSize:10,padding:'2px 6px',borderRadius:10,marginRight:8,minWidth:18,textAlign:'center'}}>{n.badge}</span>}
                </div>))}
                <div style={{flex:1}}/>
                <div style={{padding:'12px 16px',borderTop:'1px solid var(--border)'}}>
                    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                        <span style={{fontSize:9,color:'#64748B'}}>{APP_VERSION}</span>
                        <span style={{fontSize:9,color:'#64748B'}}>{now.toLocaleDateString('fa-IR',{weekday:'long',year:'numeric',month:'numeric',day:'numeric'})}</span>
                    </div>
                    <div className="text-primary text-sm font-bold">{user.full_name}</div>
                    <div className="text-dim" style={{fontSize:10}}>{user.role}</div>
                    <button className="btn btn-ghost w-full mt-8" style={{fontSize:11}} onClick={handleLogout}>خروج</button>
                </div>
            </div>
            <div className="main-content">{views[view]}</div>
        </div>
    );
}

function App() {
    return (
        <ThemeProvider>
            <AppInner />
        </ThemeProvider>
    );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
