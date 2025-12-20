import { X, Minimize2, Maximize2, Send, Bot, Paperclip } from 'lucide-react'

interface ComposeModalProps {
  onClose: () => void
}

export default function ComposeModal({ onClose }: ComposeModalProps) {
  return (
    <div className="compose-overlay">
      <div className="compose-modal">
        <div className="compose-header">
          <div className="window-controls">
            <button onClick={onClose}><X size={16} /></button>
            <button><Minimize2 size={16} /></button>
            <button><Maximize2 size={16} /></button>
          </div>
          <button className="send-action">
            <Send size={16} />
          </button>
        </div>
        <div className="compose-body">
          <div className="field">
            <label>收件人</label>
            <input type="text" />
            <span className="cc-bcc">Cc Bcc</span>
          </div>
          <div className="field">
            <label>主题</label>
            <input type="text" />
          </div>
          <textarea placeholder="开始输入或使用 AI 写作..." className="compose-area"></textarea>
        </div>
        <div className="compose-footer">
          <button className="ai-btn">
            <Bot size={16} />
            <span>AI 写作</span>
          </button>
          <div className="format-tools">
            <button><Paperclip size={18} /></button>
            <button>Aa</button>
          </div>
        </div>
      </div>
    </div>
  )
}
