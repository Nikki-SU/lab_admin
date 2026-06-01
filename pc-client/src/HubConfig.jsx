import React, { useState } from 'react'

function HubConfig({ onBack, onComplete }) {
  const [config, setConfig] = useState({
    host: 'localhost',
    port: '8000',
    name: 'My LabVault Hub'
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    localStorage.setItem('hubConfig', JSON.stringify(config))
    onComplete()
  }

  return (
    <div className="config-container">
      <div className="config-card">
        <button className="back-btn" onClick={onBack}>← 返回</button>
        <h2>🖥️ 配置 Hub 服务器</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>服务器名称</label>
            <input
              type="text"
              value={config.name}
              onChange={(e) => setConfig({...config, name: e.target.value})}
              placeholder="例如：我的实验室 Hub"
            />
          </div>

          <div className="form-group">
            <label>主机地址</label>
            <input
              type="text"
              value={config.host}
              onChange={(e) => setConfig({...config, host: e.target.value})}
              placeholder="localhost 或 IP 地址"
            />
          </div>

          <div className="form-group">
            <label>端口</label>
            <input
              type="number"
              value={config.port}
              onChange={(e) => setConfig({...config, port: e.target.value})}
            />
          </div>

          <button type="submit" className="btn btn-primary">
            保存并启动 Hub
          </button>
        </form>
      </div>
    </div>
  )
}

export default HubConfig
