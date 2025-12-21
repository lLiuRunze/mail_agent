import { 
  Inbox, FileText, Mail, Star, Archive, Trash2, Settings, Plus, LogOut, User, Send, FilePenLine
} from 'lucide-react'
import { useState } from 'react'

interface SidebarProps {
  currentAccount: string
  accounts: string[]
  activeTab: string
  setActiveTab: (tab: string) => void
  onAccountChange: (account: string) => void
  onAddAccount: () => void
  onLogout: (email: string) => void
}

export default function Sidebar({ 
  currentAccount, 
  accounts, 
  activeTab, 
  setActiveTab, 
  onAccountChange, 
  onAddAccount,
  onLogout 
}: SidebarProps) {
  const [showAccountMenu, setShowAccountMenu] = useState(false)

  return (
    <aside className="sidebar">
      <div 
        className="user-profile" 
        onMouseEnter={() => setShowAccountMenu(true)}
        onMouseLeave={() => setShowAccountMenu(false)}
        style={{position: 'relative', cursor: 'pointer'}}
      >
        <div className="avatar-circle" style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <User size={20} />
        </div>
        <div className="user-info">
          <div className="name">User</div>
          <div className="email">{currentAccount}</div>
        </div>
        
        {showAccountMenu && (
          <div className="account-menu" style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            width: '100%',
            background: 'white',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            borderRadius: '8px',
            padding: '8px',
            zIndex: 100
          }}>
            {accounts.map(acc => (
              <div 
                key={acc} 
                className="account-item"
                onClick={() => onAccountChange(acc)}
                style={{
                  padding: '8px',
                  borderRadius: '4px',
                  background: currentAccount === acc ? '#f3f4f6' : 'transparent',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '4px'
                }}
              >
                <div className="avatar-circle" style={{width: '24px', height: '24px', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                  <User size={12} />
                </div>
                <span style={{fontSize: '12px', overflow: 'hidden', textOverflow: 'ellipsis'}}>{acc}</span>
              </div>
            ))}
            <div 
              className="add-account-btn"
              onClick={onAddAccount}
              style={{
                padding: '8px',
                borderTop: '1px solid #eee',
                marginTop: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                color: '#4f46e5'
              }}
            >
              <Plus size={16} />
              <span style={{fontSize: '12px'}}>添加账号</span>
            </div>
            <div 
              className="logout-btn"
              onClick={() => onLogout(currentAccount)}
              style={{
                padding: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                color: '#dc2626'
              }}
            >
              <LogOut size={16} />
              <span style={{fontSize: '12px'}}>退出登录</span>
            </div>
          </div>
        )}
      </div>

      <nav className="nav-menu">
        <div className={`nav-item ${activeTab === 'inbox' ? 'active' : ''}`} onClick={() => setActiveTab('inbox')}>
          <Inbox size={18} />
          <span>收件箱</span>
        </div>
        <div className={`nav-item ${activeTab === 'all' ? 'active' : ''}`} onClick={() => setActiveTab('all')}>
          <Mail size={18} />
          <span>所有邮件</span>
        </div>
        <div className={`nav-item ${activeTab === 'starred' ? 'active' : ''}`} onClick={() => setActiveTab('starred')}>
          <Star size={18} />
          <span>星标邮件</span>
        </div>
        <div className={`nav-item ${activeTab === 'sent' ? 'active' : ''}`} onClick={() => setActiveTab('sent')}>
          <Send size={18} />
          <span>已发送</span>
        </div>
        <div className={`nav-item ${activeTab === 'drafts' ? 'active' : ''}`} onClick={() => setActiveTab('drafts')}>
          <FilePenLine size={18} />
          <span>草稿箱</span>
        </div>
        
        <div className="nav-divider"></div>
        
        <div className="nav-item">
          <FileText size={18} />
          <span>待办事项</span>
        </div>
        <div className={`nav-item ${activeTab === 'archive' ? 'active' : ''}`} onClick={() => setActiveTab('archive')}>
          <Archive size={18} />
          <span>归档</span>
        </div>
        <div className={`nav-item ${activeTab === 'trash' ? 'active' : ''}`} onClick={() => setActiveTab('trash')}>
          <Trash2 size={18} />
          <span>垃圾箱</span>
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="nav-item">
          <Settings size={18} />
          <span>设置</span>
        </div>
      </div>
    </aside>
  )
}
