import { useState } from 'react'
import api from './lib/api'
import { Mail, Lock, HelpCircle, X, Check, ChevronRight, AlertCircle } from 'lucide-react'
import './login.css'

interface LoginProps {
  onLoginSuccess: (email: string) => void
  embedded?: boolean
}

export default function Login({ onLoginSuccess, embedded = false }: LoginProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [provider, setProvider] = useState('163')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showTutorial, setShowTutorial] = useState(false)

  const providers = [
    { id: '163', name: '网易 163', icon: '📧' },
    { id: 'qq', name: 'QQ 邮箱', icon: '🐧' },
    { id: 'gmail', name: 'Gmail', icon: 'G' },
    { id: 'outlook', name: 'Outlook', icon: 'O' },
  ]

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      setError('请输入邮箱和密码')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await api.post('/api/login', {
        email,
        password,
        provider
      })

      if (response.data.success) {
        onLoginSuccess(email)
      }
    } catch (err: any) {
      console.error('Login error:', err)
      setError(err.response?.data?.detail || '登录失败，请检查账号密码或授权码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`login-container ${embedded ? 'embedded' : ''}`}>
      <div className="login-card" style={embedded ? {boxShadow: 'none', padding: '1.5rem', width: '100%'} : {}}>
        <div className="login-header">
          <div className="logo-circle">
            <Mail size={32} />
          </div>
          <h1>欢迎使用 MailAgent</h1>
          <p>您的智能邮件助手</p>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <label>选择邮箱服务商</label>
            <div className="provider-grid">
              {providers.map(p => (
                <div 
                  key={p.id} 
                  className={`provider-item ${provider === p.id ? 'active' : ''}`}
                  onClick={() => setProvider(p.id)}
                >
                  <span className="provider-icon">{p.icon}</span>
                  <span className="provider-name">{p.name}</span>
                  {provider === p.id && <div className="check-mark"><Check size={12} /></div>}
                </div>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>邮箱地址</label>
            <div className="input-with-icon">
              <Mail size={18} className="input-icon" />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="yourname@example.com"
              />
            </div>
          </div>

          <div className="form-group">
            <div className="label-row">
              <label>授权码 / 密码</label>
              <button type="button" className="help-link" onClick={() => setShowTutorial(true)}>
                <HelpCircle size={14} />
                <span>如何获取授权码？</span>
              </button>
            </div>
            <div className="input-with-icon">
              <Lock size={18} className="input-icon" />
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入授权码或密码"
              />
            </div>
            <p className="hint-text">注意：国内邮箱（163/QQ）通常需要使用 SMTP/IMAP 授权码，而非登录密码。</p>
          </div>

          {error && (
            <div className="error-message">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? '正在连接...' : '登 录'}
            {!loading && <ChevronRight size={18} />}
          </button>
        </form>
      </div>

      {showTutorial && (
        <div className="modal-overlay" onClick={() => setShowTutorial(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>如何获取邮箱授权码</h3>
              <button onClick={() => setShowTutorial(false)}><X size={20} /></button>
            </div>
            <div className="modal-body">
              <div className="tutorial-section">
                <h4><span className="step-num">1</span> 网易 163 邮箱</h4>
                <ol>
                  <li>登录网页版 163 邮箱</li>
                  <li>点击顶部“设置” → “POP3/SMTP/IMAP”</li>
                  <li>开启 “IMAP/SMTP服务”</li>
                  <li>点击“新增授权密码”，按提示发送短信</li>
                  <li>复制生成的授权码作为密码登录</li>
                </ol>
              </div>
              
              <div className="tutorial-section">
                <h4><span className="step-num">2</span> QQ 邮箱</h4>
                <ol>
                  <li>登录网页版 QQ 邮箱</li>
                  <li>点击顶部“设置” → “账户”</li>
                  <li>向下滚动找到 “POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务”</li>
                  <li>开启 “IMAP/SMTP服务”</li>
                  <li>点击“生成授权码”，按提示验证</li>
                  <li>复制授权码作为密码登录</li>
                </ol>
              </div>

              <div className="tutorial-section">
                <h4><span className="step-num">3</span> Gmail / Outlook</h4>
                <p>通常使用您的账户密码即可。如果开启了双重验证（2FA），则需要生成“应用专用密码”。</p>
              </div>
            </div>
            <div className="modal-footer">
              <button className="primary-btn" onClick={() => setShowTutorial(false)}>我明白了</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
