import React, { useState } from 'react'

function WelcomePage({ onSelectMode }) {
  const [selectedMode, setSelectedMode] = useState(null)

  const handleModeSelect = (mode) => {
    setSelectedMode(mode)
    onSelectMode(mode)
  }

  return (
    <div className="welcome-container">
      <div className="welcome-card">
        <h1 className="welcome-title">🔬 LabVault</h1>
        <p className="welcome-subtitle">实验室数据存储与管理系统</p>
        
        <div className="mode-selector">
          <div 
            className={`mode-card ${selectedMode === 'pc' ? 'selected' : ''}`}
            onClick={() => handleModeSelect('pc')}
          >
            <div className="mode-icon">💻</div>
            <h3>个人电脑</h3>
            <p>登录账号，管理和查看您的数据</p>
          </div>

          <div 
            className={`mode-card ${selectedMode === 'hub' ? 'selected' : ''}`}
            onClick={() => handleModeSelect('hub')}
          >
            <div className="mode-icon">🖥️</div>
            <h3>配置 Hub</h3>
            <p>设置和管理中央服务器</p>
          </div>

          <div 
            className={`mode-card ${selectedMode === 'leaf' ? 'selected' : ''}`}
            onClick={() => handleModeSelect('leaf')}
          >
            <div className="mode-icon">🔬</div>
            <h3>Leaf 设备</h3>
            <p>配置实验室设备，申请接入权限</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WelcomePage
