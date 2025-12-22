import { useState, useEffect } from 'react'
import { X, User, Save, Edit2} from 'lucide-react'
import axios from 'axios'
import './SettingsPanel.css'

interface AccountProfile {
  email: string
  displayName: string
  avatar: string
  signature: string
  replyTone: string
  autoReplyEnabled: boolean
}

interface SettingsPanelProps {
  currentAccount: string
  onClose: () => void
  onProfileUpdate?: (displayName: string, avatar: string) => void
}

export default function SettingsPanel({ currentAccount, onClose, onProfileUpdate }: SettingsPanelProps) {
  const [profile, setProfile] = useState<AccountProfile>({
    email: currentAccount,
    displayName: '',
    avatar: '',
    signature: '',
    replyTone: '正式',
    autoReplyEnabled: false
  })
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadProfile()
  }, [currentAccount])

  const loadProfile = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/profile?email=${currentAccount}`)
      if (response.data.success) {
        setProfile({
          email: currentAccount,
          displayName: response.data.profile.display_name || '',
          avatar: response.data.profile.avatar || '',
          signature: response.data.profile.signature || '',
          replyTone: response.data.profile.reply_tone || '正式',
          autoReplyEnabled: response.data.profile.auto_reply_enabled || false
        })
      }
    } catch (error) {
      console.error('Failed to load profile:', error)
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    setMessage('')
    try {
      const response = await axios.post('http://localhost:8000/api/profile', {
        email: currentAccount,
        display_name: profile.displayName,
        avatar: profile.avatar,
        signature: profile.signature,
        reply_tone: profile.replyTone,
        auto_reply_enabled: profile.autoReplyEnabled
      })
      
      if (response.data.success) {
        setMessage('✓ 设置已保存')
        setIsEditing(false)
        // 通知父组件更新显示名称和头像
        if (onProfileUpdate) {
          onProfileUpdate(profile.displayName, profile.avatar)
        }
        setTimeout(() => setMessage(''), 3000)
      }
    } catch (error) {
      setMessage('✗ 保存失败，请重试')
      console.error('Failed to save profile:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const avatarOptions = [
    '😀', '😎', '🤖', '👨‍💻', '👩‍💻', '🧑‍💼', '👨‍🎓', '👩‍🎓',
    '🦸', '🦹', '🧙', '🧝', '🧛', '🧜', '🧚', '👻',
    '🐱', '🐶', '🐼', '🐨', '🦊', '🦁', '🐯', '🐸'
  ]

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-panel" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <div className="settings-title">
            <User size={24} />
            <h2>账户设置</h2>
          </div>
          <button className="close-button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="settings-content">
          {/* 账户信息 */}
          <div className="settings-section">
            <div className="section-header">
              <User size={18} />
              <h3>个人资料</h3>
            </div>
            <div className="setting-item">
              <label>头像</label>
              <div className="avatar-selector">
                <div className="current-avatar">
                  {profile.avatar || '👤'}
                </div>
                {isEditing && (
                  <div className="avatar-options">
                    {avatarOptions.map((emoji, idx) => (
                      <div
                        key={idx}
                        className={`avatar-option ${profile.avatar === emoji ? 'selected' : ''}`}
                        onClick={() => setProfile({ ...profile, avatar: emoji })}
                      >
                        {emoji}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="setting-item">
              <label>显示名称</label>
              <input
                type="text"
                value={profile.displayName}
                onChange={(e) => setProfile({ ...profile, displayName: e.target.value })}
                disabled={!isEditing}
                placeholder="设置你的显示名称"
              />
            </div>
            <div className="setting-item">
              <label>邮箱地址</label>
              <input
                type="text"
                value={profile.email}
                disabled
                className="input-disabled"
              />
            </div>
          </div>

          {/* 邮件偏好 */}
          <div className="settings-section">
            <div className="section-header">
              <Edit2 size={18} />
              <h3>邮件偏好</h3>
            </div>
            <div className="setting-item">
              <label>默认回复语气</label>
              <select
                value={profile.replyTone}
                onChange={(e) => setProfile({ ...profile, replyTone: e.target.value })}
                disabled={!isEditing}
              >
                <option value="正式">正式</option>
                <option value="友好">友好</option>
                <option value="简洁">简洁</option>
                <option value="热情">热情</option>
              </select>
            </div>
            <div className="setting-item">
              <label>邮件签名</label>
              <textarea
                value={profile.signature}
                onChange={(e) => setProfile({ ...profile, signature: e.target.value })}
                disabled={!isEditing}
                placeholder="在邮件末尾添加的签名（例如：此致\n敬礼\n张三）"
                rows={4}
              />
            </div>
            <div className="setting-item checkbox-item">
              <label>
                <input
                  type="checkbox"
                  checked={profile.autoReplyEnabled}
                  onChange={(e) => setProfile({ ...profile, autoReplyEnabled: e.target.checked })}
                  disabled={!isEditing}
                />
                <span>启用智能自动回复建议</span>
              </label>
              <p className="help-text">AI 会在查看邮件时自动生成回复建议</p>
            </div>
          </div>

          {/* 消息提示 */}
          {message && (
            <div className={`message ${message.includes('✓') ? 'success' : 'error'}`}>
              {message}
            </div>
          )}
        </div>

        <div className="settings-footer">
          {isEditing ? (
            <>
              <button 
                className="btn btn-secondary" 
                onClick={() => {
                  setIsEditing(false)
                  loadProfile()
                }}
                disabled={isSaving}
              >
                取消
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleSave}
                disabled={isSaving}
              >
                {isSaving ? (
                  <>
                    <span className="spinner"></span>
                    保存中...
                  </>
                ) : (
                  <>
                    <Save size={16} />
                    保存设置
                  </>
                )}
              </button>
            </>
          ) : (
            <button 
              className="btn btn-primary" 
              onClick={() => setIsEditing(true)}
            >
              <Edit2 size={16} />
              编辑资料
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
