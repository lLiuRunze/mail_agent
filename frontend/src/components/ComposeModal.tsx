import { useState } from 'react'
import { X, Minimize2, Maximize2, Send, Bot, Paperclip, Loader2 } from 'lucide-react'
import api from '../lib/api'

interface ComposeModalProps {
  onClose: () => void
  currentAccount: string
  onSendSuccess?: () => void
}

export default function ComposeModal({ onClose, currentAccount, onSendSuccess }: ComposeModalProps) {
  const [to, setTo] = useState('')
  const [subject, setSubject] = useState('')
  const [content, setContent] = useState('')
  const [showAiPrompt, setShowAiPrompt] = useState(false)
  const [aiPrompt, setAiPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)

  const handleAiGenerate = async () => {
    if (!aiPrompt.trim() || !to || !subject) {
      alert('请先填写收件人、主题，并输入AI写作需求')
      return
    }

    setLoading(true)
    try {
      const response = await api.post('/api/generate/compose', {
        email: currentAccount,
        to: [to],
        subject: subject,
        content: aiPrompt
      })

      if (response.data.content) {
        setContent(response.data.content)
        setShowAiPrompt(false)
        setAiPrompt('')
      }
    } catch (error: any) {
      console.error('AI生成失败:', error)
      alert(`AI生成失败: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSend = async () => {
    if (!to || !subject || !content) {
      alert('请填写收件人、主题和内容')
      return
    }

    setSending(true)
    try {
      const response = await api.post('/api/compose', {
        email: currentAccount,
        to: [to],
        subject: subject,
        content: content
      })

      if (response.data.success) {
        alert('邮件发送成功！')
        onSendSuccess?.()
        onClose()
      }
    } catch (error: any) {
      console.error('发送失败:', error)
      alert(`发送失败: ${error.response?.data?.detail || error.message}`)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="compose-overlay">
      <div className="compose-modal">
        <div className="compose-header">
          <div className="window-controls">
            <button onClick={onClose}><X size={16} /></button>
            <button><Minimize2 size={16} /></button>
            <button><Maximize2 size={16} /></button>
          </div>
          <button className="send-action" onClick={handleSend} disabled={sending}>
            {sending ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
          </button>
        </div>
        <div className="compose-body">
          <div className="field">
            <label>收件人</label>
            <input 
              type="text" 
              value={to}
              onChange={(e) => setTo(e.target.value)}
              placeholder="recipient@example.com"
            />
            <span className="cc-bcc">Cc Bcc</span>
          </div>
          <div className="field">
            <label>主题</label>
            <input 
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="邮件主题"
            />
          </div>
          <textarea 
            placeholder="开始输入或使用 AI 写作..." 
            className="compose-area"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          ></textarea>
        </div>
        <div className="compose-footer">
          <button className="ai-btn" onClick={() => setShowAiPrompt(true)}>
            <Bot size={16} />
            <span>AI 写作</span>
          </button>
          <div className="format-tools">
            <button><Paperclip size={18} /></button>
            <button>Aa</button>
          </div>
        </div>
      </div>

      {showAiPrompt && (
        <div className="ai-prompt-overlay" onClick={() => setShowAiPrompt(false)}>
          <div className="ai-prompt-modal" onClick={(e) => e.stopPropagation()}>
            <div className="ai-prompt-header">
              <h3>AI 写作</h3>
              <button onClick={() => setShowAiPrompt(false)}><X size={18} /></button>
            </div>
            <div className="ai-prompt-body">
              <textarea
                placeholder="请描述你想写什么样的邮件，例如：写一封请假邮件、写一封感谢信等..."
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
                autoFocus
              />
            </div>
            <div className="ai-prompt-footer">
              <button onClick={() => setShowAiPrompt(false)} disabled={loading}>
                取消
              </button>
              <button 
                className="primary" 
                onClick={handleAiGenerate}
                disabled={loading || !aiPrompt.trim()}
              >
                {loading ? <><Loader2 size={16} className="spin" /> 生成中...</> : '生成'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
