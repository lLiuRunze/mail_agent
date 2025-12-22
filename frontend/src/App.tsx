import { useState, useEffect } from 'react'
import axios from 'axios'
import { Loader2, X } from 'lucide-react'
import Login from './login'
import Sidebar from './components/Sidebar'
import EmailList from './components/EmailList'
import AssistantPanel from './components/AssistantPanel'
import ComposeModal from './components/ComposeModal'
import SettingsPanel from './components/SettingsPanel'
import SearchModal from './components/SearchModal'
import EmailDetail from './components/EmailDetail'
import './App.css'

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

function App() {
  // Auth State
  const [accounts, setAccounts] = useState<string[]>([])
  const [currentAccount, setCurrentAccount] = useState('')
  const [authChecking, setAuthChecking] = useState(true)
  const [showAddAccount, setShowAddAccount] = useState(false)
  
  // User Profile
  const [userProfiles, setUserProfiles] = useState<Record<string, {displayName: string, avatar: string}>>({})

  // Chat State
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '你好！我是你的智能邮件助手 MailAgent。我可以帮你处理邮件、查找信息或整理收件箱。' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  // UI State
  const [activeTab, setActiveTab] = useState('inbox')
  const [showCompose, setShowCompose] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showSearch, setShowSearch] = useState(false)
  const [showEmailDetail, setShowEmailDetail] = useState(false)
  const [selectedEmailId, setSelectedEmailId] = useState<string>('')
  const [readFilter, setReadFilter] = useState<'all' | 'read' | 'unread'>('all')
  
  // Email Data
  const [emails, setEmails] = useState<Email[]>([])
  const [loadingEmails, setLoadingEmails] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [classifying, setClassifying] = useState(false)

  useEffect(() => {
    checkAuth()
  }, [])

  useEffect(() => {
    if (currentAccount) {
      fetchEmails()
      loadUserProfile(currentAccount)
    }
  }, [currentAccount, activeTab])

  const loadUserProfile = async (email: string) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/profile?email=${email}`)
      if (response.data.success) {
        setUserProfiles(prev => ({
          ...prev,
          [email]: {
            displayName: response.data.profile.display_name || '',
            avatar: response.data.profile.avatar || ''
          }
        }))
      }
    } catch (error) {
      console.error('Failed to load user profile:', error)
    }
  }

  const handleProfileUpdate = (displayName: string, avatar: string) => {
    setUserProfiles(prev => ({
      ...prev,
      [currentAccount]: { displayName, avatar }
    }))
  }

  const handleEmailClick = (emailId: string) => {
    console.log('Email clicked:', emailId, 'Current account:', currentAccount)
    if (!currentAccount) {
      console.error('No current account set!')
      return
    }
    setSelectedEmailId(emailId)
    setShowEmailDetail(true)
  }

  const handleReplyFromDetail = async (emailId: string) => {
    // 关闭详情页
    setShowEmailDetail(false)
    setSelectedEmailId('')
    
    // 添加用户消息到聊天
    setMessages(prev => [...prev, {
      role: 'user',
      content: `回复邮件 ${emailId}`
    }])
    
    setLoading(true)
    
    try {
      // 调用后端生成回复
      const generateResponse = await axios.post(`http://localhost:8000/api/emails/${emailId}/generate-reply`, {
        email: currentAccount,
        auto_generate: true
      })
      
      if (generateResponse.data.success) {
        const genData = generateResponse.data.data
        const previewContent = genData.reply_content
        const emailInfo = {
          type: 'reply' as const,
          to: genData.from,
          subject: `Re: ${genData.subject}`,
          content: previewContent,
          email_id: emailId
        }
        
        // 添加AI回复消息到聊天
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `我已为你生成了回复邮件的草稿，你可以查看并编辑后发送。`,
          emailPreview: emailInfo
        }])
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `生成回复失败: ${generateResponse.data.message}`
        }])
      }
    } catch (err: any) {
      console.error('Generate reply error:', err)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `生成回复失败: ${err.response?.data?.detail || err.message}`
      }])
    } finally {
      setLoading(false)
    }
  }

  const fetchEmails = async () => {
    setLoadingEmails(true)
    try {
      // Determine folder based on activeTab
      // Use folder type names that backend can intelligently match
      let folder = 'INBOX'
      
      if (activeTab === 'sent') {
        folder = 'sent'  // Backend will find "Sent Messages" or "已发送"
      } else if (activeTab === 'drafts') {
        folder = 'drafts'  // Backend will find "Drafts" or "草稿箱"
      } else if (activeTab === 'starred') {
        // Backend will automatically filter FLAGGED emails from INBOX
        folder = 'starred'
      } else if (activeTab === 'archive') {
        folder = 'archive'  // Backend will find "Archive" or "归档"
      } else if (activeTab === 'trash') {
        folder = 'trash'  // Backend will find "Deleted Messages" or "已删除"
      } else if (activeTab === 'all') {
        folder = 'INBOX' // Get all from inbox
      } else if (activeTab === 'inbox') {
        folder = 'INBOX'
      }
      
      const response = await axios.get('http://localhost:8000/api/emails', {
        params: {
          email: currentAccount,
          days: 30,
          limit: 30,
          folder: folder
        }
      })
      
      if (response.data.success) {
        const mappedEmails: Email[] = response.data.emails.map((e: any) => ({
          id: e.id,
          sender: e.from_name || e.from,
          subject: e.subject,
          preview: e.body ? e.body.substring(0, 100) + '...' : '点击查看邮件内容...',
          time: formatEmailDate(e.date),
          read: e.seen !== undefined ? e.seen : true,
          tags: []
        }))
        setEmails(mappedEmails)
      }
    } catch (error: any) {
      console.error('Failed to fetch emails:', error)
      // Show error message to user
      if (error.response?.status === 500 && activeTab === 'sent') {
        console.log('Sent folder might not exist or have different name')
        setEmails([])
      }
    } finally {
      setLoadingEmails(false)
    }
  }

  const formatEmailDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      const now = new Date()
      if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
      return date.toLocaleDateString()
    } catch (e) {
      return dateStr
    }
  }

  const classifyEmails = async (targetCategory?: string) => {
    if (!currentAccount || emails.length === 0) return
    
    setClassifying(true)
    try {
      // 收集所有邮件ID
      const emailIds = emails.map(email => email.id.toString())
      
      console.log(`开始批量分类 ${emailIds.length} 封邮件...`)
      
      // 调用批量分类接口
      const response = await axios.post(
        'http://localhost:8000/api/emails/batch/classify',
        { 
          email: currentAccount,
          email_ids: emailIds
        }
      )
      
      if (response.data.success) {
        const { classifications } = response.data.data
        
        // 创建分类映射
        const classificationMap: { [key: string]: string } = {}
        classifications.forEach((item: any) => {
          classificationMap[item.email_id] = item.classification.category
        })
        
        // 更新邮件列表，添加分类信息
        setEmails(prev => prev.map(email => ({
          ...email,
          category: classificationMap[email.id.toString()] || email.category
        })))
        
        console.log(`批量分类完成: ${response.data.data.success}/${response.data.data.total} 成功`)
        
        // 如果指定了目标分类，则切换到该分类筛选
        if (targetCategory) {
          setCategoryFilter(targetCategory)
        }
      }
    } catch (error) {
      console.error('批量分类失败:', error)
    } finally {
      setClassifying(false)
    }
  }

  const checkAuth = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/check-auth')
      if (response.data.authenticated) {
        setAccounts(response.data.accounts)
        setCurrentAccount(response.data.active_account)
      }
    } catch (error) {
      console.error('Auth check failed:', error)
    } finally {
      setAuthChecking(false)
    }
  }

  const handleLoginSuccess = (email: string) => {
    if (!accounts.includes(email)) {
      setAccounts(prev => [...prev, email])
    }
    setCurrentAccount(email)
    setShowAddAccount(false)
  }

  const handleLogout = async (email: string) => {
    try {
      await axios.post('http://localhost:8000/api/logout', null, {
        params: { email }
      })
      
      // Remove from accounts list
      const updatedAccounts = accounts.filter(acc => acc !== email)
      setAccounts(updatedAccounts)
      
      // If logged out from current account, switch to another or show login
      if (email === currentAccount) {
        if (updatedAccounts.length > 0) {
          setCurrentAccount(updatedAccounts[0])
        } else {
          setCurrentAccount('')
        }
      }
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    const originalInput = input
    setInput('')
    setLoading(true)

    try {
      // Parse the user input using NLU to determine intent
      const parseResponse = await axios.post('http://localhost:8000/api/chat', {
        message: originalInput,
        email: currentAccount,
        preview_only: true  // 使用预览模式
      })

      const data = parseResponse.data
      const intent = data.intent
      const parameters = data.parameters
      
      // Check if this is a reply or compose operation that needs preview
      if (intent === 'reply_email' || intent === 'compose_email') {
        // Generate preview content
        setLoading(true)
        let previewContent = ''
        let emailInfo: any = {}
        
        if (intent === 'reply_email') {
          // Get email info and generate reply
          const emailId = parameters.email_id || 'latest'
          try {
            // Call generate_reply endpoint with correct path
            const generateResponse = await axios.post(`http://localhost:8000/api/emails/${emailId}/generate-reply`, {
              email: currentAccount,
              auto_generate: true
            })
            
            if (generateResponse.data.success) {
              const genData = generateResponse.data.data
              previewContent = genData.reply_content
              emailInfo = {
                to: genData.from,
                subject: `Re: ${genData.subject}`,
                email_id: emailId
              }
            }
          } catch (err: any) {
            console.error('Generate reply error:', err)
            // If generation fails, show error
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: `生成回复失败: ${err.response?.data?.detail || err.message}`
            }])
            setLoading(false)
            return
          }
        } else if (intent === 'compose_email') {
          // For compose, call backend to generate content
          const contentPrompt = parameters.content_prompt || parameters.content || ''
          const toAddr = parameters.to_addr || ''
          const subject = parameters.subject || ''
          
          if (!toAddr) {
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: '请指定收件人地址'
            }])
            setLoading(false)
            return
          }
          
          try {
            // Call backend to generate complete email content
            const genResponse = await axios.post('http://localhost:8000/api/generate/compose', {
              email: currentAccount,
              to: [toAddr],
              subject: subject,
              content: contentPrompt
            })
            
            const genData = genResponse.data
            previewContent = genData.content || contentPrompt || '（请输入邮件内容）'
            emailInfo = {
              to: genData.to || toAddr,
              subject: genData.subject || subject || '新邮件'
            }
          } catch (err: any) {
            console.error('Error generating compose content:', err)
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: `生成邮件内容失败: ${err.response?.data?.detail || err.message}`
            }])
            setLoading(false)
            return
          }
        }
        
        if (emailInfo.to) {
          // Add preview message to chat
          const previewMessage: Message = {
            role: 'assistant',
            content: `已生成${intent === 'reply_email' ? '回复' : '邮件'}内容，请查看预览并选择发送或编辑后发送：`,
            intent: intent,
            emailPreview: {
              type: intent === 'reply_email' ? 'reply' : 'compose',
              to: emailInfo.to,
              subject: emailInfo.subject,
              content: previewContent,
              email_id: emailInfo.email_id
            }
          }
          
          setMessages(prev => [...prev, previewMessage])
          setLoading(false)
          return
        }
      }
      
      // For other operations or if preview failed, execute directly
      const executeResponse = await axios.post('http://localhost:8000/api/chat', {
        message: originalInput,
        email: currentAccount
      })
      
      const result = executeResponse.data
      const assistantMessage: Message = {
        role: 'assistant',
        content: result.message || '任务已执行',
        intent: result.intent,
        result: result.result
      }
      
      setMessages(prev => [...prev, assistantMessage])
      
      // If the operation modified email list, refresh the inbox
      if (result.intent && ['archive_email', 'delete_email', 
          'forward_email', 'mark_read', 'mark_unread', 'batch_archive', 
          'batch_delete'].includes(result.intent)) {
        fetchEmails()
      }
    } catch (error: any) {
      console.error('Error sending message:', error)
      const errorMessage = error.response?.data?.detail || '抱歉，服务暂时不可用。'
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: errorMessage 
      }])
    } finally {
      setLoading(false)
    }
  }
  
  const handleSendEmail = async (emailPreview: any, editedContent?: string) => {
    console.log('handleSendEmail called with:', { emailPreview, editedContent })
    setLoading(true)
    
    try {
      const content = editedContent || emailPreview.content
      let endpoint = ''
      let payload: any = {}
      
      if (emailPreview.type === 'reply') {
        endpoint = 'http://localhost:8000/api/reply'
        payload = {
          email: currentAccount,
          email_id: emailPreview.email_id,
          content: content
        }
      } else {
        endpoint = 'http://localhost:8000/api/compose'
        payload = {
          email: currentAccount,
          to: [emailPreview.to],
          subject: emailPreview.subject,
          content: content
        }
      }
      
      console.log('Sending to endpoint:', endpoint, 'with payload:', payload)
      const response = await axios.post(endpoint, payload)
      console.log('Send response:', response.data)
      
      if (response.data.success) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `✓ ${emailPreview.type === 'reply' ? '回复' : '邮件'}已成功发送到: ${emailPreview.to}`,
          result: response.data
        }])
        fetchEmails()
      }
    } catch (error: any) {
      console.error('Error sending email:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `发送失败: ${error.response?.data?.detail || '未知错误'}`
      }])
    } finally {
      setLoading(false)
    }
  }

  if (authChecking) {
    return <div className="loading-screen"><Loader2 className="spin" size={40} /></div>
  }

  if (accounts.length === 0) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  return (
    <div className="app-container">
      {/* Add Account Modal */}
      {showAddAccount && (
        <div className="modal-overlay" style={{zIndex: 1000}}>
          <div className="modal-content" style={{maxWidth: '480px', padding: 0, overflow: 'hidden'}}>
            <div style={{position: 'absolute', right: '10px', top: '10px', zIndex: 10}}>
              <button onClick={() => setShowAddAccount(false)} style={{background: 'none', border: 'none', cursor: 'pointer'}}>
                <X size={24} />
              </button>
            </div>
            <Login onLoginSuccess={handleLoginSuccess} embedded={true} />
          </div>
        </div>
      )}

      <Sidebar 
        currentAccount={currentAccount}
        accounts={accounts}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onAccountChange={setCurrentAccount}
        onAddAccount={() => setShowAddAccount(true)}
        onLogout={handleLogout}
        onOpenSettings={() => setShowSettings(true)}
        displayName={userProfiles[currentAccount]?.displayName}
        avatar={userProfiles[currentAccount]?.avatar}
      />

      <EmailList 
        emails={emails}
        loading={loadingEmails}
        onCompose={() => setShowCompose(true)}
        onSearch={() => setShowSearch(true)}
        onEmailClick={handleEmailClick}
        readFilter={readFilter}
        onReadFilterChange={setReadFilter}
        activeTab={activeTab}
        categoryFilter={categoryFilter}
        onCategoryChange={setCategoryFilter}
        classifying={classifying}
        onClassify={classifyEmails}
      />

      {showCompose && (
        <ComposeModal 
          onClose={() => setShowCompose(false)}
          currentAccount={currentAccount}
          onSendSuccess={fetchEmails}
        />
      )}

      {showSearch && (
        <SearchModal 
          currentAccount={currentAccount}
          onClose={() => setShowSearch(false)}
          onResultClick={(email) => {
            console.log('Search result clicked:', email)
            setShowSearch(false)
          }}
        />
      )}

      {showEmailDetail && selectedEmailId && currentAccount && (
        <EmailDetail
          emailId={selectedEmailId}
          currentAccount={currentAccount}
          onClose={() => {
            setShowEmailDetail(false)
            setSelectedEmailId('')
          }}
          onReply={() => handleReplyFromDetail(selectedEmailId)}
        />
      )}

      {showSettings && (
        <SettingsPanel 
          currentAccount={currentAccount}
          onClose={() => setShowSettings(false)}
          onProfileUpdate={handleProfileUpdate}
        />
      )}

      <AssistantPanel 
        messages={messages}
        input={input}
        setInput={setInput}
        loading={loading}
        onSendMessage={sendMessage}
        onSendEmail={handleSendEmail}
      />
    </div>
  )
}

export default App
