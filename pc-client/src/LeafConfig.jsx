import React, { useState } from 'react'

function LeafConfig({ onBack, onComplete }) {
  const [request, setRequest] = useState({
    deviceName: '',
    deviceType: 'lab_device',
    ipAddress: '',
    purpose: '',
    requesterName: ''
  })
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    // 模拟提交申请
    localStorage.setItem('leafRequest', JSON.stringify(request))
    setSubmitted(true)
  }

  if (submitted) {
    return (
      <div className="config-container">
        <div className="config-card">
          <h2>✅ 申请已提交</h2>
          <p>您的 Leaf 设备接入申请已发送，请等待管理员审批。</p>
          <div className="request-summary">
            <p><strong>设备名称：</strong> {request.deviceName}</p>
            <p><strong>类型：</strong> {request.deviceType === 'lab_device' ? '实验设备' : '汇报电脑'}</p>
            <p><strong>申请人：</strong> {request.requesterName}</p>
          </div>
          <button className="btn btn-primary" onClick={onBack}>
            返回首页
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="config-container">
      <div className="config-card">
        <button className="back-btn" onClick={onBack}>← 返回</button>
        <h2>🔬 Leaf 设备申请</h2>
        <p className="subtitle">请填写以下信息申请接入 Hub</p>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>设备名称</label>
            <input
              type="text"
              value={request.deviceName}
              onChange={(e) => setRequest({...request, deviceName: e.target.value})}
              placeholder="例如：FT-IR-01"
              required
            />
          </div>

          <div className="form-group">
            <label>设备类型</label>
            <select
              value={request.deviceType}
              onChange={(e) => setRequest({...request, deviceType: e.target.value})}
            >
              <option value="lab_device">实验设备（数据区）</option>
              <option value="presentation">汇报电脑（协作区）</option>
            </select>
          </div>

          <div className="form-group">
            <label>IP 地址</label>
            <input
              type="text"
              value={request.ipAddress}
              onChange={(e) => setRequest({...request, ipAddress: e.target.value})}
              placeholder="例如：192.168.1.100"
              required
            />
          </div>

          <div className="form-group">
            <label>申请人姓名</label>
            <input
              type="text"
              value={request.requesterName}
              onChange={(e) => setRequest({...request, requesterName: e.target.value})}
              placeholder="您的姓名"
              required
            />
          </div>

          <div className="form-group">
            <label>用途说明</label>
            <textarea
              value={request.purpose}
              onChange={(e) => setRequest({...request, purpose: e.target.value})}
              placeholder="简要说明设备用途"
              rows="4"
            />
          </div>

          <button type="submit" className="btn btn-primary">
            提交申请
          </button>
        </form>
      </div>
    </div>
  )
}

export default LeafConfig
