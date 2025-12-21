import { Search, MoreHorizontal, Plus, Loader2 } from 'lucide-react'

interface Email {
  id: string | number
  sender: string
  subject: string
  preview: string
  time: string
  tags?: string[]
  read: boolean
  category?: string
}

interface EmailListProps {
  emails: Email[]
  loading: boolean
  onCompose: () => void
  onSearch: () => void
  onEmailClick: (emailId: string) => void
  readFilter: 'all' | 'read' | 'unread'
  onReadFilterChange: (filter: 'all' | 'read' | 'unread') => void
  activeTab: string
  categoryFilter: string
  onCategoryChange: (category: string) => void
  classifying: boolean
  onClassify: (category?: string) => void
}

export default function EmailList({ emails, loading, onCompose, onSearch, onEmailClick, readFilter, onReadFilterChange, activeTab, categoryFilter, onCategoryChange, classifying, onClassify }: EmailListProps) {
  // 计算各分类的邮件数量
  const categoryCounts = {
    '工作': emails.filter(e => e.category === '工作').length,
    '通知': emails.filter(e => e.category === '通知').length,
    '营销': emails.filter(e => e.category === '营销').length,
    '账单': emails.filter(e => e.category === '账单').length,
  }

  // Filter emails based on read status and category
  const filteredEmails = emails.filter(email => {
    if (readFilter === 'read' && !email.read) return false
    if (readFilter === 'unread' && email.read) return false
    if (categoryFilter !== 'all' && email.category !== categoryFilter) return false
    return true
  })
  return (
    <main className="main-content">
      <header className="top-bar">
        <div className="tabs">
          <button 
            className={`tab ${categoryFilter === 'all' ? 'active' : ''}`}
            onClick={() => onCategoryChange('all')}
            disabled={classifying}
          >
            全部 <span className="tab-badge">{emails.length}</span>
          </button>
          <button 
            className={`tab ${categoryFilter === '工作' ? 'active' : ''}`}
            onClick={() => {
              if (categoryCounts['工作'] === 0) {
                onClassify('工作')
              } else {
                onCategoryChange('工作')
              }
            }}
            disabled={classifying}
          >
            工作 <span className="tab-badge">{categoryCounts['工作']}</span>
          </button>
          <button 
            className={`tab ${categoryFilter === '通知' ? 'active' : ''}`}
            onClick={() => {
              if (categoryCounts['通知'] === 0) {
                onClassify('通知')
              } else {
                onCategoryChange('通知')
              }
            }}
            disabled={classifying}
          >
            通知 <span className="tab-badge">{categoryCounts['通知']}</span>
          </button>
          <button 
            className={`tab ${categoryFilter === '营销' ? 'active' : ''}`}
            onClick={() => {
              if (categoryCounts['营销'] === 0) {
                onClassify('营销')
              } else {
                onCategoryChange('营销')
              }
            }}
            disabled={classifying}
          >
            营销 <span className="tab-badge">{categoryCounts['营销']}</span>
          </button>
          <button 
            className={`tab ${categoryFilter === '账单' ? 'active' : ''}`}
            onClick={() => {
              if (categoryCounts['账单'] === 0) {
                onClassify('账单')
              } else {
                onCategoryChange('账单')
              }
            }}
            disabled={classifying}
          >
            账单 <span className="tab-badge">{categoryCounts['账单']}</span>
          </button>
          {classifying && (
            <span style={{ marginLeft: '10px', fontSize: '12px', color: '#666' }}>
              分类中...
            </span>
          )}
        </div>
        <div className="actions">
          <button className="icon-btn" onClick={onSearch}><Search size={18} /></button>
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
                activeTab === 'sent' ? '已发送' :
                activeTab === 'drafts' ? '草稿箱' :
                activeTab === 'archive' ? '归档' :
                activeTab === 'trash' ? '垃圾箱' : '邮件'}
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
            <div 
              key={email.id} 
              className={`email-item ${!email.read ? 'unread' : ''}`}
              onClick={() => onEmailClick(String(email.id))}
              style={{ cursor: 'pointer' }}
            >
              <div className="sender-avatar" style={avatarStyle}>
                {email.sender ? email.sender[0] : '?'}
              </div>
              <div className="email-content">
                <div className="email-header">
                  <span className="sender-name">{email.sender}</span>
                  <span className="email-time">{email.time}</span>
                </div>
                <div className="email-subject">
                  {email.subject}
                  {email.category && (
                    <span 
                      style={{
                        marginLeft: '8px',
                        padding: '2px 8px',
                        fontSize: '11px',
                        borderRadius: '10px',
                        backgroundColor: 
                          email.category === '工作' ? '#dbeafe' :
                          email.category === '通知' ? '#e9d5ff' :
                          email.category === '营销' ? '#fef3c7' :
                          email.category === '账单' ? '#fecaca' :
                          '#e5e7eb',
                        color:
                          email.category === '工作' ? '#1e40af' :
                          email.category === '通知' ? '#7c3aed' :
                          email.category === '营销' ? '#b45309' :
                          email.category === '账单' ? '#b91c1c' :
                          '#6b7280',
                        fontWeight: 500
                      }}
                    >
                      {email.category}
                    </span>
                  )}
                </div>
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
