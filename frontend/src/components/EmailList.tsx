import { Search, MoreHorizontal, Plus, Loader2 } from 'lucide-react'

interface Email {
  id: string | number
  sender: string
  subject: string
  preview: string
  time: string
  tags?: string[]
  read: boolean
}

interface EmailListProps {
  emails: Email[]
  loading: boolean
  onCompose: () => void
  readFilter: 'all' | 'read' | 'unread'
  onReadFilterChange: (filter: 'all' | 'read' | 'unread') => void
  activeTab: string
}

export default function EmailList({ emails, loading, onCompose, readFilter, onReadFilterChange, activeTab }: EmailListProps) {
  // Filter emails based on read status
  const filteredEmails = emails.filter(email => {
    if (readFilter === 'read') return email.read
    if (readFilter === 'unread') return !email.read
    return true
  })
  return (
    <main className="main-content">
      <header className="top-bar">
        <div className="tabs">
          <button className="tab active">重要 <span className="tab-badge">2</span></button>
          <button className="tab">更新 <span className="tab-badge">3</span></button>
          <button className="tab">推广 <span className="tab-badge">35</span></button>
          <button className="tab">账单 <span className="tab-badge">14</span></button>
        </div>
        <div className="actions">
          <button className="icon-btn"><Search size={18} /></button>
          <button className="icon-btn"><MoreHorizontal size={18} /></button>
          <button className="primary-btn" onClick={onCompose}>
            <Plus size={18} />
            <span>写邮件</span>
          </button>
        </div>
      </header>

      <div className="email-list">
        <div className="list-header">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
            <span>
              {loading ? '正在同步邮件...' : 
                activeTab === 'inbox' ? '收件箱' :
                activeTab === 'all' ? '所有邮件' :
                activeTab === 'starred' ? '星标邮件' :
                activeTab === 'sent' ? '已发送' : '邮件'}
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                onClick={() => onReadFilterChange('all')}
                style={{
                  padding: '4px 12px',
                  fontSize: '12px',
                  borderRadius: '4px',
                  border: '1px solid #e5e7eb',
                  background: readFilter === 'all' ? '#4f46e5' : 'white',
                  color: readFilter === 'all' ? 'white' : '#6b7280',
                  cursor: 'pointer',
                  fontWeight: readFilter === 'all' ? 600 : 400
                }}
              >
                全部
              </button>
              <button 
                onClick={() => onReadFilterChange('unread')}
                style={{
                  padding: '4px 12px',
                  fontSize: '12px',
                  borderRadius: '4px',
                  border: '1px solid #e5e7eb',
                  background: readFilter === 'unread' ? '#4f46e5' : 'white',
                  color: readFilter === 'unread' ? 'white' : '#6b7280',
                  cursor: 'pointer',
                  fontWeight: readFilter === 'unread' ? 600 : 400
                }}
              >
                未读
              </button>
              <button 
                onClick={() => onReadFilterChange('read')}
                style={{
                  padding: '4px 12px',
                  fontSize: '12px',
                  borderRadius: '4px',
                  border: '1px solid #e5e7eb',
                  background: readFilter === 'read' ? '#4f46e5' : 'white',
                  color: readFilter === 'read' ? 'white' : '#6b7280',
                  cursor: 'pointer',
                  fontWeight: readFilter === 'read' ? 600 : 400
                }}
              >
                已读
              </button>
            </div>
          </div>
          {!loading && filteredEmails.length === 0 && emails.length > 0 && <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>该筛选条件下暂无邮件</div>}
          {!loading && emails.length === 0 && <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>暂无邮件</div>}
        </div>
        {loading && (
          <div style={{display: 'flex', justifyContent: 'center', padding: '2rem'}}>
            <Loader2 className="spin" size={24} />
          </div>
        )}
        {!loading && filteredEmails.map(email => {
          // Get color style for avatar based on sender
          const colors = [
            { bg: '#e0e7ff', text: '#4338ca' },  // Indigo
            { bg: '#dbeafe', text: '#1e40af' },  // Blue
            { bg: '#ccfbf1', text: '#0f766e' },  // Teal
            { bg: '#d1fae5', text: '#047857' },  // Green
            { bg: '#fef3c7', text: '#b45309' },  // Amber
            { bg: '#fecaca', text: '#b91c1c' },  // Red
            { bg: '#e9d5ff', text: '#7c3aed' },  // Purple
            { bg: '#fbcfe8', text: '#be185d' },  // Pink
          ]
          
          let avatarStyle
          if (email.read) {
            avatarStyle = { backgroundColor: '#e5e7eb', color: '#6b7280' }
          } else {
            // Generate consistent color based on sender
            let hash = 0
            for (let i = 0; i < email.sender.length; i++) {
              hash = email.sender.charCodeAt(i) + ((hash << 5) - hash)
            }
            const color = colors[Math.abs(hash) % colors.length]
            avatarStyle = { backgroundColor: color.bg, color: color.text }
          }
          
          return (
            <div key={email.id} className={`email-item ${!email.read ? 'unread' : ''}`}>
              <div className="sender-avatar" style={avatarStyle}>
                {email.sender ? email.sender[0] : '?'}
              </div>
              <div className="email-content">
                <div className="email-header">
                  <span className="sender-name">{email.sender}</span>
                  <span className="email-time">{email.time}</span>
                </div>
                <div className="email-subject">{email.subject}</div>
                <div className="email-preview">
                  {email.preview}
                  {email.tags?.map(tag => (
                    <span key={tag} className={`email-tag ${tag.toLowerCase()}`}>{tag}</span>
                  ))}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </main>
  )
}
