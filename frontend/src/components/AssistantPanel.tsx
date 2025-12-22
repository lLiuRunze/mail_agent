import { Bot, Plus, MoreHorizontal, Loader2, Send, Edit2, Mail } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  intent?: string
  result?: any
  emailPreview?: {
    type: 'reply' | 'compose'
    to: string
    subject: string
    content: string
    email_id?: string
  }
}

interface AssistantPanelProps {
  messages: Message[]
  input: string
  setInput: (input: string) => void
  loading: boolean
  onSendMessage: () => void
  onSendEmail: (emailPreview: any, editedContent?: string) => void
}

export default function AssistantPanel({ 
  messages, 
  input, 
  setInput, 
  loading, 
  onSendMessage,
  onSendEmail
}: AssistantPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSendMessage()
    }
  }

  // Render execution result in a structured way
  const renderResult = (result: any) => {
    if (!result || typeof result !== 'object') return null
    
    // Show success/error status
    const statusColor = result.success ? '#10b981' : '#ef4444'
    const statusText = result.success ? '✓ 成功' : '✗ 失败'
    
    return (
      <div style={{
        marginTop: '8px',
        padding: '8px',
        background: 'rgba(0,0,0,0.05)',
        borderRadius: '6px',
        fontSize: '13px'
      }}>
        <div style={{ color: statusColor, fontWeight: 600, marginBottom: '4px' }}>
          {statusText}
        </div>
        
        {/* Show count for list operations */}
        {result.count !== undefined && (
          <div>找到 {result.count} 项</div>
        )}
        
        {/* Show affected count for batch operations */}
        {result.affected !== undefined && (
          <div>已处理 {result.affected} 项</div>
        )}
        
        {/* Show summary content for single email summary */}
        {result.data?.summary && typeof result.data.summary === 'string' && (
          <div style={{
            marginTop: '8px',
            padding: '12px',
            background: 'rgba(102, 126, 234, 0.1)',
            borderRadius: '8px',
            borderLeft: '3px solid #667eea'
          }}>
            <div style={{ fontWeight: 600, marginBottom: '8px', color: '#667eea', fontSize: '14px' }}>
              📝 邮件摘要
            </div>
            <div style={{ 
              fontSize: '14px', 
              lineHeight: '1.6',
              whiteSpace: 'pre-wrap',
              color: '#333'
            }}>
              {result.data.summary}
            </div>
            {result.data.subject && (
              <div style={{ 
                marginTop: '10px', 
                paddingTop: '8px',
                borderTop: '1px solid rgba(0,0,0,0.1)',
                fontSize: '12px', 
                color: '#666' 
              }}>
                <strong>主题:</strong> {result.data.subject}
              </div>
            )}
            {result.data.from && (
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                <strong>发件人:</strong> {result.data.from}
              </div>
            )}
          </div>
        )}
        
        {/* Show summaries for batch email summary */}
        {result.data?.summaries && Array.isArray(result.data.summaries) && (
          <div style={{ marginTop: '8px' }}>
            <div style={{ 
              fontWeight: 600, 
              marginBottom: '12px', 
              color: '#667eea',
              fontSize: '14px'
            }}>
              📋 批量摘要（共 {result.data.summaries.length} 封邮件）
            </div>
            {result.data.summaries.map((item: any, idx: number) => (
              <div key={idx} style={{
                marginTop: idx > 0 ? '12px' : '0',
                padding: '12px',
                background: 'rgba(102, 126, 234, 0.08)',
                borderRadius: '8px',
                borderLeft: '3px solid #667eea'
              }}>
                <div style={{ 
                  fontWeight: 600, 
                  marginBottom: '6px', 
                  fontSize: '13px',
                  color: '#333'
                }}>
                  {idx + 1}. {item.subject}
                </div>
                {item.from && (
                  <div style={{ 
                    fontSize: '11px', 
                    color: '#666', 
                    marginBottom: '8px' 
                  }}>
                    发件人: {item.from}
                  </div>
                )}
                <div style={{ 
                  fontSize: '13px', 
                  lineHeight: '1.6',
                  whiteSpace: 'pre-wrap',
                  color: '#444'
                }}>
                  {item.summary}
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* Show data summary for email lists (non-summary operations) */}
        {result.data && Array.isArray(result.data) && result.data.length > 0 && 
         !result.data[0]?.summary && (
          <div>
            <div style={{ marginTop: '4px', color: '#666' }}>
              显示前 {Math.min(3, result.data.length)} 项:
            </div>
            {result.data.slice(0, 3).map((item: any, idx: number) => (
              <div key={idx} style={{
                marginTop: '4px',
                padding: '4px',
                background: 'rgba(255,255,255,0.5)',
                borderRadius: '4px'
              }}>
                <div style={{ fontWeight: 500 }}>
                  {item.subject || item.from || 'No subject'}
                </div>
                {item.from && <div style={{ fontSize: '12px', color: '#666' }}>{item.from}</div>}
              </div>
            ))}
          </div>
        )}
        
        {/* Show error message */}
        {result.error && (
          <div style={{ color: '#ef4444', marginTop: '4px' }}>
            错误: {result.error}
          </div>
        )}
      </div>
    )
  }

  // Render email preview card with editing capability
  const EmailPreviewCard = ({ emailPreview }: { emailPreview: any }) => {
    const [isEditing, setIsEditing] = useState(false)
    const [editedContent, setEditedContent] = useState(emailPreview.content)
    const [isSending, setIsSending] = useState(false)

    const handleSend = async () => {
      console.log('EmailPreviewCard handleSend called', { emailPreview, isEditing, editedContent })
      setIsSending(true)
      try {
        await onSendEmail(emailPreview, isEditing ? editedContent : undefined)
        console.log('onSendEmail completed successfully')
      } catch (error) {
        console.error('onSendEmail error:', error)
      } finally {
        setIsSending(false)
      }
    }

    return (
      <div style={{
        marginTop: '12px',
        padding: '12px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '12px',
        color: 'white'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
          <Mail size={16} style={{ marginRight: '6px' }} />
          <span style={{ fontWeight: 600 }}>
            {emailPreview.type === 'reply' ? '邮件回复预览' : '新建邮件预览'}
          </span>
        </div>
        
        <div style={{
          background: 'rgba(255,255,255,0.15)',
          borderRadius: '8px',
          padding: '10px',
          marginBottom: '10px'
        }}>
          <div style={{ marginBottom: '6px', fontSize: '13px', opacity: 0.9 }}>
            <strong>收件人:</strong> {emailPreview.to}
          </div>
          <div style={{ marginBottom: '8px', fontSize: '13px', opacity: 0.9 }}>
            <strong>主题:</strong> {emailPreview.subject}
          </div>
          
          {isEditing ? (
            <textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              style={{
                width: '100%',
                minHeight: '120px',
                padding: '8px',
                background: 'rgba(255,255,255,0.95)',
                color: '#333',
                border: 'none',
                borderRadius: '6px',
                fontSize: '13px',
                fontFamily: 'inherit',
                resize: 'vertical'
              }}
            />
          ) : (
            <div style={{
              fontSize: '13px',
              lineHeight: '1.6',
              whiteSpace: 'pre-wrap',
              opacity: 0.95
            }}>
              {emailPreview.content}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
          {isEditing ? (
            <>
              <button
                onClick={() => {
                  setIsEditing(false)
                  setEditedContent(emailPreview.content)
                }}
                style={{
                  padding: '6px 12px',
                  background: 'rgba(255,255,255,0.2)',
                  border: 'none',
                  borderRadius: '6px',
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 500
                }}
              >
                取消编辑
              </button>
              <button
                onClick={handleSend}
                disabled={isSending}
                style={{
                  padding: '6px 16px',
                  background: 'rgba(255,255,255,0.95)',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#667eea',
                  cursor: isSending ? 'not-allowed' : 'pointer',
                  fontSize: '13px',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  opacity: isSending ? 0.6 : 1
                }}
              >
                {isSending ? <Loader2 size={14} className="spin" /> : <Send size={14} />}
                {isSending ? '发送中...' : '发送'}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setIsEditing(true)}
                style={{
                  padding: '6px 12px',
                  background: 'rgba(255,255,255,0.2)',
                  border: 'none',
                  borderRadius: '6px',
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 500,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Edit2 size={14} />
                编辑
              </button>
              <button
                onClick={handleSend}
                disabled={isSending}
                style={{
                  padding: '6px 16px',
                  background: 'rgba(255,255,255,0.95)',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#667eea',
                  cursor: isSending ? 'not-allowed' : 'pointer',
                  fontSize: '13px',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  opacity: isSending ? 0.6 : 1
                }}
              >
                {isSending ? <Loader2 size={14} className="spin" /> : <Send size={14} />}
                {isSending ? '发送中...' : '直接发送'}
              </button>
            </>
          )}
        </div>
      </div>
    )
  }

  return (
    <aside className="assistant-panel">
      <div className="assistant-header">
        <div className="assistant-title">
          <span className="sparkle">✨</span>
          Mail Agent
        </div>
        <div className="window-controls">
          <button><Plus size={18} /></button>
          <button><MoreHorizontal size={18} /></button>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="sparkle-large">✨</div>
            <h3>我是你的个人助手</h3>
            <p>我可以帮你把每一封邮件转化为清晰的下一步行动。</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className="chat-avatar">
                  <Bot size={16} />
                </div>
              )}
              <div className="chat-bubble">
                {msg.content}
                {msg.intent && (
                  <div className="chat-meta">
                    <span className="intent-tag">意图: {msg.intent}</span>
                  </div>
                )}
                {msg.result && renderResult(msg.result)}
                {msg.emailPreview && <EmailPreviewCard emailPreview={msg.emailPreview} />}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="chat-message assistant">
            <div className="chat-avatar"><Bot size={16} /></div>
            <div className="chat-bubble loading">
              <Loader2 className="spin" size={16} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="suggestion-chips">
        <button onClick={() => setInput('查看最近10封邮件')}>查看最近10封邮件</button>
        <button onClick={() => setInput('搜索标题包含账单的邮件')}>搜索账单邮件</button>
        <button onClick={() => setInput('总结最近的邮件')}>总结最近邮件</button>
      </div>

      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <input 
            type="text" 
            placeholder="问点什么..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
          />
          <button onClick={onSendMessage} disabled={!input.trim()}>
            <Send size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}
