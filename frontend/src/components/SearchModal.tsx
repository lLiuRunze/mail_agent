import { useState } from 'react'
import { X, Search, User, Mail, Loader2 } from 'lucide-react'
import api from '../lib/api'
import './SearchModal.css'

interface SearchModalProps {
  currentAccount: string
  onClose: () => void
  onResultClick?: (emailId: string) => void
}

interface SearchResult {
  id: string | number
  subject: string
  from: string
  from_name: string
  date: string
}

export default function SearchModal({ currentAccount, onClose, onResultClick }: SearchModalProps) {
  const [searchContent, setSearchContent] = useState('')
  const [searchSender, setSearchSender] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [searched, setSearched] = useState(false)

  const handleSearch = async () => {
    if (!searchContent && !searchSender) return

    setSearching(true)
    setSearched(false)

    try {
      const response = await api.post('/api/emails/search', {
        email: currentAccount,
        content: searchContent || undefined,
        sender: searchSender || undefined
      })

      if (response.data.success) {
        setResults(response.data.data?.emails || [])
      } else {
        setResults([])
      }
    } catch (error) {
      console.error('搜索失败:', error)
      setResults([])
    } finally {
      setSearching(false)
      setSearched(true)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="search-overlay" onClick={onClose}>
      <div className="search-modal" onClick={(e) => e.stopPropagation()}>
        <div className="search-header">
          <div className="search-title">
            <Search size={22} />
            <h2>搜索邮件</h2>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="search-body">
          <div className="search-input-group">
            <div className="search-input-wrapper">
              <Mail size={18} className="input-icon" />
              <input
                type="text"
                placeholder="搜索邮件内容或主题..."
                value={searchContent}
                onChange={(e) => setSearchContent(e.target.value)}
                onKeyPress={handleKeyPress}
                autoFocus
              />
            </div>
            
            <div className="search-input-wrapper">
              <User size={18} className="input-icon" />
              <input
                type="text"
                placeholder="搜索发件人..."
                value={searchSender}
                onChange={(e) => setSearchSender(e.target.value)}
                onKeyPress={handleKeyPress}
              />
            </div>
          </div>

          <button 
            className="search-btn"
            onClick={handleSearch}
            disabled={searching || (!searchContent && !searchSender)}
          >
            {searching ? (
              <>
                <Loader2 size={16} className="spin" />
                搜索中...
              </>
            ) : (
              <>
                <Search size={16} />
                搜索
              </>
            )}
          </button>

          <div className="search-results">
            {searching && (
              <div className="search-loading">
                <Loader2 size={32} className="spin" />
                <p>正在搜索...</p>
              </div>
            )}

            {!searching && searched && results.length === 0 && (
              <div className="search-empty">
                <Mail size={48} />
                <p>未找到匹配的邮件</p>
                <span>尝试使用不同的关键词</span>
              </div>
            )}

            {!searching && results.length > 0 && (
              <>
                <div className="results-header">
                  找到 {results.length} 封邮件
                </div>
                <div className="results-list">
                  {results.map((email) => (
                    <div 
                      key={email.id} 
                      className="result-item"
                      onClick={() => {
                        if (onResultClick) {
                          onResultClick(String(email.id))
                        }
                      }}
                    >
                      <div className="result-subject">{email.subject}</div>
                      <div className="result-meta">
                        <span className="result-sender">
                          {email.from_name || email.from}
                        </span>
                        <span className="result-date">{email.date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}

            {!searching && !searched && (
              <div className="search-hint">
                <Search size={48} />
                <p>输入关键词开始搜索</p>
                <span>支持搜索邮件内容、主题和发件人</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
