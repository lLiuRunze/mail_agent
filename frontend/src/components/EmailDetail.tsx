import { useState, useEffect } from 'react'
import { X, Mail, User, Calendar, Paperclip, Reply, Forward, Trash2, Archive, Loader2 } from 'lucide-react'
import axios from 'axios'
import './EmailDetail.css'

interface EmailDetailProps {
  emailId: string
  currentAccount: string
  onClose: () => void
  onReply?: () => void
  onForward?: () => void
  onDelete?: () => void
  onArchive?: () => void
}

interface EmailContent {
  id: string
  subject: string
  from: string
  from_name: string
  to: string | string[]
  cc?: string | string[]
  date: string
  body: string
  attachments?: Array<{
    filename: string
    size: number
  }>
  read: boolean
}

export default function EmailDetail({ 
  emailId, 
  currentAccount, 
  onClose,
  onReply,
  onForward,
  onDelete,
  onArchive 
}: EmailDetailProps) {
  const [email, setEmail] = useState<EmailContent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    console.log('EmailDetail mounted with:', { emailId, currentAccount })
    if (emailId && currentAccount) {
      loadEmailDetail()
    } else {
      console.warn('Missing emailId or currentAccount')
      setError('缺少必要参数')
      setLoading(false)
    }
    
    return () => {
      // Cleanup on unmount
      console.log('EmailDetail unmounting')
      setEmail(null)
      setError(null)
    }
  }, [emailId, currentAccount])

  const loadEmailDetail = async () => {
    setLoading(true)
    setError(null)
    
    try {
      console.log('Loading email detail for ID:', emailId)
      const response = await axios.post('http://localhost:8000/api/emails/detail', {
        email: currentAccount,
        email_id: emailId
      })

      console.log('Email detail response:', response.data)

      if (response.data.success) {
        setEmail(response.data.data)
      } else {
        setError(response.data.message || '加载邮件失败')
      }
    } catch (err: any) {
      console.error('加载邮件详情失败:', err)
      setError(err.response?.data?.detail || err.message || '加载邮件详情失败')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const formatRecipients = (recipients: string | string[] | undefined): string => {
    if (!recipients) return '未知'
    if (typeof recipients === 'string') return recipients
    if (Array.isArray(recipients)) return recipients.join(', ')
    return String(recipients)
  }

  const renderEmailBody = (body: string) => {
    if (!body) return <p style={{ color: '#9ca3af' }}>邮件内容为空</p>
    
    // 检查是否包含 HTML 标签
    const hasHtml = /<[^>]+>/.test(body)
    
    if (hasHtml) {
      return (
        <div 
          dangerouslySetInnerHTML={{ __html: body }} 
          style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
        />
      )
    } else {
      return (
        <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {body}
        </div>
      )
    }
  }

  return (
    <div className="email-detail-overlay" onClick={onClose}>
      <div className="email-detail-panel" onClick={(e) => e.stopPropagation()}>
        <div className="email-detail-header">
          <h2>邮件详情</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {loading && (
          <div className="email-detail-loading">
            <Loader2 size={32} className="spin" />
            <p>加载中...</p>
          </div>
        )}

        {error && (
          <div className="email-detail-error">
            <p>{error}</p>
            <button onClick={loadEmailDetail}>重试</button>
          </div>
        )}

        {!loading && !error && email && (
          <>
            <div className="email-detail-content">
              <div className="email-subject">
                <h3>{email.subject}</h3>
              </div>

              <div className="email-meta">
                <div className="meta-row">
                  <User size={16} />
                  <span className="meta-label">发件人：</span>
                  <span className="meta-value">
                    {email.from_name ? `${email.from_name} <${email.from}>` : email.from}
                  </span>
                </div>

                <div className="meta-row">
                  <Mail size={16} />
                  <span className="meta-label">收件人：</span>
                  <span className="meta-value">{formatRecipients(email.to)}</span>
                </div>

                {email.cc && (
                  <div className="meta-row">
                    <Mail size={16} />
                    <span className="meta-label">抄送：</span>
                    <span className="meta-value">{formatRecipients(email.cc)}</span>
                  </div>
                )}

                <div className="meta-row">
                  <Calendar size={16} />
                  <span className="meta-label">时间：</span>
                  <span className="meta-value">{formatDate(email.date)}</span>
                </div>
              </div>

              {email.attachments && email.attachments.length > 0 && (
                <div className="email-attachments">
                  <div className="attachments-header">
                    <Paperclip size={16} />
                    <span>附件 ({email.attachments.length})</span>
                  </div>
                  <div className="attachments-list">
                    {email.attachments.map((att, idx) => (
                      <div key={idx} className="attachment-item">
                        <Paperclip size={14} />
                        <span className="attachment-name">{att.filename}</span>
                        <span className="attachment-size">{formatFileSize(att.size)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="email-body">
                {renderEmailBody(email.body)}
              </div>
            </div>

            <div className="email-detail-actions">
              {onReply && (
                <button className="action-btn primary" onClick={onReply}>
                  <Reply size={18} />
                  回复
                </button>
              )}
              {onForward && (
                <button className="action-btn" onClick={onForward}>
                  <Forward size={18} />
                  转发
                </button>
              )}
              {onArchive && (
                <button className="action-btn" onClick={onArchive}>
                  <Archive size={18} />
                  归档
                </button>
              )}
              {onDelete && (
                <button className="action-btn danger" onClick={onDelete}>
                  <Trash2 size={18} />
                  删除
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
