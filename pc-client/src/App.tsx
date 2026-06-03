import { useState, useEffect } from 'react'
import axios from 'axios'
import WelcomePage from './WelcomePage'
import HubConfig from './HubConfig'
import LeafConfig from './LeafConfig'

interface User {
  id: string
  name: string
  level: string
  group_id?: string
  status: string
}

interface File {
  id: string
  zone: string
  name: string
  path: string
  size: number
  owner_id: string
  edited: boolean
  edit_count: number
  uploader: string
  upload_time: string
  source_type: string
  source_device: string
  metadata?: any
}

interface LogEntry {
  id: string
  timestamp: string
  operator: string
  location: string
  action: string
  detail: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

function Login({ onLogin, onBack }: { onLogin: (token: string, user: User) => void, onBack: () => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)
      
      const res = await axios.post(`${API_BASE}/token`, formData)
      const token = res.data.access_token
      
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      const userRes = await axios.get(`${API_BASE}/users/me`)
      
      onLogin(token, userRes.data)
    } catch (err) {
      setError('用户名或密码错误')
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <button className="back-btn" onClick={onBack} style={{alignSelf: 'flex-start'}}>← 返回</button>
        <h2>🔬 LabVault</h2>
        {error && <div className="alert-box alert-warning">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名"
              required
            />
          </div>
          <div className="form-group">
            <label>密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              required
            />
          </div>
          <button type="submit" className="btn btn-primary">登录</button>
        </form>
        <p style={{ marginTop: '20px', textAlign: 'center', color: '#888', fontSize: '14px' }}>
          测试账号: admin / admin123
        </p>
      </div>
    </div>
  )
}

function FileList({ zone, title, readonly, user }: { zone: string, title: string, readonly?: boolean, user: User }) {
  const [files, setFiles] = useState<File[]>([])
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchFiles = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get(`${API_BASE}/files`, { params: { zone } })
      setFiles(res.data)
    } catch (err: any) {
      console.error('Failed to fetch files:', err)
      setError(err.response?.data?.detail || '加载文件失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFiles()
  }, [zone])

  const handleDownload = async (file: File) => {
    setError(null)
    try {
      const res = await axios.get(`${API_BASE}/files/${file.id}`, {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', file.name)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err: any) {
      console.error('Failed to download:', err)
      alert(err.response?.data?.detail || '下载失败')
    }
  }

  const handleDelete = async (fileId: string) => {
    if (!window.confirm('确定要删除此文件吗？')) return

    setError(null)
    try {
      await axios.delete(`${API_BASE}/files/${fileId}`)
      fetchFiles()
    } catch (err: any) {
      console.error('Failed to delete:', err)
      alert(err.response?.data?.detail || '删除失败')
    }
  }

  const handleFileUpload = async (file: any) => {
    if (readonly) {
      setError('实验数据区为只读模式，不支持上传')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('zone', zone)
      formData.append('path', `/${file.name}`)
      formData.append('source_device', 'PC')

      await axios.post(`${API_BASE}/files/upload`, formData)
      fetchFiles()
    } catch (err: any) {
      console.error('Failed to upload:', err)
      setError(err.response?.data?.detail || '上传失败')
    } finally {
      setLoading(false)
    }
  }

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(true)
  }

  const onDragLeave = () => {
    setDragging(false)
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0])
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div>
      {error && <div className="alert-box alert-warning">{error}</div>}

      {!readonly && (
        <div
          className={`upload-area ${dragging ? 'dragging' : ''}`}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => document.getElementById('fileInput')?.click()}
        >
          <input
            id="fileInput"
            type="file"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
          />
          <p>📤 点击或拖拽文件到此区域上传</p>
        </div>
      )}

      {readonly && (
        <div className="alert-box alert-info">
          🔒 实验数据区为只读模式：数据由实验室电脑（Leaf Agent）自动上传，本客户端仅可查看和下载
        </div>
      )}

      <div className="file-list">
        <h3>{title} {loading && <span style={{ fontSize: '14px', color: '#888' }}>(加载中...)</span>}</h3>
        {files.length === 0 ? (
          <p style={{ color: '#888', padding: '20px 0' }}>暂无文件</p>
        ) : (
          files.map((file) => (
            <div key={file.id} className={`file-item ${file.edited ? 'edited' : ''}`}>
              <div className="file-info">
                <span>📄</span>
                <div>
                  <div className="file-name">
                    {file.name}
                    {file.edited && <span style={{ color: '#e74c3c', marginLeft: '8px' }}>⚠️ 已编辑</span>}
                  </div>
                  <div className="file-meta">
                    {formatSize(file.size)} · {new Date(file.upload_time).toLocaleString()}
                    {file.source_device && <span style={{ marginLeft: '8px' }}>· 来源: {file.source_device}</span>}
                  </div>
                </div>
              </div>
              <div className="file-actions">
                <button className="btn btn-secondary btn-sm" onClick={() => handleDownload(file)} disabled={loading}>
                  下载
                </button>
                {file.uploader === user.id && (
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(file.id)} disabled={loading}>
                    删除
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function EditedFiles({ user }: { user: User }) {
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchEditedFiles = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get(`${API_BASE}/files`, { params: { edited_only: true } })
      setFiles(res.data)
    } catch (err: any) {
      console.error('Failed to fetch edited files:', err)
      setError(err.response?.data?.detail || '加载已编辑文件失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEditedFiles()
  }, [])

  const handleDownload = async (file: File) => {
    try {
      const res = await axios.get(`${API_BASE}/files/${file.id}`, {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', file.name)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err: any) {
      alert(err.response?.data?.detail || '下载失败')
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div>
      <div className="alert-box alert-warning">
        ⚠️ 此区域显示所有被编辑过的文件。这些文件在上传后被修改过，系统不提供信任背书，请谨慎使用。
      </div>

      {error && <div className="alert-box alert-warning">{error}</div>}

      <div className="file-list">
        <h3>已编辑文件列表 {loading && <span style={{ fontSize: '14px', color: '#888' }}>(加载中...)</span>}</h3>

        {files.length === 0 ? (
          <p style={{ color: '#888', padding: '20px 0' }}>
            {loading ? '正在加载...' : '暂无已编辑文件'}
          </p>
        ) : (
          <table className="edited-files-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
                <th style={{ padding: '12px 8px' }}>文件名</th>
                <th style={{ padding: '12px 8px' }}>来源设备</th>
                <th style={{ padding: '12px 8px' }}>编辑次数</th>
                <th style={{ padding: '12px 8px' }}>大小</th>
                <th style={{ padding: '12px 8px' }}>上传时间</th>
                <th style={{ padding: '12px 8px' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => (
                <tr key={file.id} style={{ borderBottom: '1px solid #eee', backgroundColor: file.edited ? '#fff3cd' : 'transparent' }}>
                  <td style={{ padding: '10px 8px' }}>
                    <span style={{ fontWeight: 'bold' }}>📄 {file.name}</span>
                    <span style={{ color: '#e74c3c', marginLeft: '8px', fontSize: '12px' }}>
                      ⚠️ 已编辑 {file.edit_count} 次
                    </span>
                  </td>
                  <td style={{ padding: '10px 8px', color: '#666' }}>{file.source_device || '未知'}</td>
                  <td style={{ padding: '10px 8px', color: '#e74c3c', fontWeight: 'bold' }}>{file.edit_count}</td>
                  <td style={{ padding: '10px 8px' }}>{formatSize(file.size)}</td>
                  <td style={{ padding: '10px 8px' }}>{new Date(file.upload_time).toLocaleString()}</td>
                  <td style={{ padding: '10px 8px' }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleDownload(file)}
                      disabled={loading}
                    >
                      下载
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([])

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await axios.get(`${API_BASE}/logs`)
        setLogs(res.data)
      } catch (err) {
        console.error('Failed to fetch logs:', err)
      }
    }
    fetchLogs()
  }, [])

  return (
    <div className="file-list">
      <h3>操作日志</h3>
      <table className="log-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>操作者</th>
            <th>位置</th>
            <th>操作</th>
            <th>详情</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id}>
              <td>{new Date(log.timestamp).toLocaleString()}</td>
              <td>{log.operator}</td>
              <td>{log.location}</td>
              <td>{log.action}</td>
              <td>{log.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function MainApp({ user, onLogout }: { user: User, onLogout: () => void }) {
  const [currentPage, setCurrentPage] = useState('data')
  const [collabTab, setCollabTab] = useState('date')

  return (
    <div className="container">
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>🔬 LabVault</h2>
        </div>
        <div className="sidebar-nav">
          <div
            className={`nav-item ${currentPage === 'data' ? 'active' : ''}`}
            onClick={() => setCurrentPage('data')}
          >
            📊 我的数据
          </div>
          <div
            className={`nav-item ${currentPage === 'edited' ? 'active' : ''}`}
            onClick={() => setCurrentPage('edited')}
          >
            ⚠️ 已编辑文件
          </div>
          <div
            className={`nav-item ${currentPage === 'collab' ? 'active' : ''}`}
            onClick={() => setCurrentPage('collab')}
          >
            📂 协作区
          </div>
          <div
            className={`nav-item ${currentPage === 'logs' ? 'active' : ''}`}
            onClick={() => setCurrentPage('logs')}
          >
            📝 日志
          </div>
        </div>
      </div>
      <div className="main-content">
        <div className="header">
          <h1>
            {currentPage === 'data' && '我的数据'}
            {currentPage === 'edited' && '已编辑文件'}
            {currentPage === 'collab' && '协作区'}
            {currentPage === 'logs' && '操作日志'}
          </h1>
          <div className="user-info">
            <span>👤 {user.name} ({user.level})</span>
            <button className="btn btn-secondary btn-sm" onClick={onLogout}>
              退出
            </button>
          </div>
        </div>

        {currentPage === 'data' && <FileList zone="DATA" title="实验数据" readonly={true} user={user} />}
        {currentPage === 'collab' && (
          <div>
            <div className="tab-buttons">
              <button
                className={`tab-btn ${collabTab === 'date' ? 'active' : ''}`}
                onClick={() => setCollabTab('date')}
              >
                📅 按日期
              </button>
              <button
                className={`tab-btn ${collabTab === 'user' ? 'active' : ''}`}
                onClick={() => setCollabTab('user')}
              >
                👤 按用户
              </button>
            </div>
            <FileList zone="COLLABORATION" title="协作文件" user={user} />
          </div>
        )}
        {currentPage === 'edited' && <EditedFiles user={user} />}
        {currentPage === 'logs' && <Logs />}
      </div>
    </div>
  )
}

function App() {
  const [mode, setMode] = useState<string | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      axios.get(`${API_BASE}/users/me`).then((res) => {
        setUser(res.data)
        setMode('pc')
      }).catch(() => {
        setToken(null)
        localStorage.removeItem('token')
      })
    }
  }, [token])

  const handleSelectMode = (selectedMode: string) => {
    setMode(selectedMode)
  }

  const handleLogin = (newToken: string, newUser: User) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
    setUser(newUser)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
    setMode(null)
  }

  const handleBack = () => {
    if (token) {
      handleLogout()
    } else {
      setMode(null)
    }
  }

  if (mode === null) {
    return <WelcomePage onSelectMode={handleSelectMode} />
  }

  if (mode === 'hub') {
    return <HubConfig onBack={handleBack} onComplete={() => setMode(null)} />
  }

  if (mode === 'leaf') {
    return <LeafConfig onBack={handleBack} onComplete={() => setMode(null)} />
  }

  if (mode === 'pc' && !user) {
    return <Login onLogin={handleLogin} onBack={handleBack} />
  }

  if (mode === 'pc' && user) {
    return <MainApp user={user} onLogout={handleLogout} />
  }

  return null
}

export default App
