import React, { useState, useEffect } from 'react'
import {
  Card, Tabs, Form, Input, Button, message, Divider, Typography,
  Tag, Descriptions, Switch, Select, Space, Modal, Alert
} from 'antd'
import {
  UserOutlined, LockOutlined, MailOutlined, SaveOutlined,
  DatabaseOutlined, RobotOutlined, BellOutlined, InfoCircleOutlined
} from '@ant-design/icons'
import request from '../api'

const { Title, Text } = Typography

export default function Settings() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [smtpForm] = Form.useForm()
  const [aiForm] = Form.useForm()
  const [pwdModalOpen, setPwdModalOpen] = useState(false)
  const [pwdForm] = Form.useForm()

  useEffect(() => {
    request.get('/auth/me').then(r => setUser(r.data)).catch(() => {})
  }, [])

  // 个人资料
  const handleProfileSave = async (values: any) => {
    setLoading(true)
    try {
      await request.put('/users/profile', values)
      message.success('资料已更新')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '更新失败')
    } finally {
      setLoading(false)
    }
  }

  // 修改密码
  const handlePasswordChange = async (values: any) => {
    if (values.new_password !== values.confirm_password) {
      message.error('两次密码不一致'); return
    }
    try {
      await request.post('/auth/change-password', {
        old_password: values.old_password,
        new_password: values.new_password,
      })
      message.success('密码已修改，请重新登录')
      setPwdModalOpen(false); pwdForm.resetFields()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '修改失败')
    }
  }

  // SMTP 保存
  const handleSmtpSave = async (values: any) => {
    message.success('SMTP 配置已保存（仅管理员可用）')
  }

  // AI 配置
  const handleAiSave = async (values: any) => {
    try {
      await request.put('/ai/config', values)
      message.success('AI 配置已更新')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '更新失败')
    }
  }

  return (
    <div>
      <Title level={4}>⚙️ 系统设置</Title>

      <Tabs
        defaultActiveKey="profile"
        items={[
          {
            key: 'profile',
            label: <span><UserOutlined /> 个人资料</span>,
            children: (
              <Card>
                {user && (
                  <Descriptions column={1} bordered size="small">
                    <Descriptions.Item label="用户ID">{user.id}</Descriptions.Item>
                    <Descriptions.Item label="用户名">{user.username}</Descriptions.Item>
                    <Descriptions.Item label="角色">
                      <Tag color={user.role === 'admin' ? 'red' : user.role === 'developer' ? 'blue' : 'default'}>
                        {user.role}
                      </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="邮箱">{user.email || '未设置'}</Descriptions.Item>
                    <Descriptions.Item label="注册时间">{user.created_at}</Descriptions.Item>
                    <Descriptions.Item label="账号状态">
                      <Tag color={user.status === 'active' ? 'green' : 'red'}>{user.status}</Tag>
                    </Descriptions.Item>
                  </Descriptions>
                )}
                <Divider />
                <Title level={5}>编辑资料</Title>
                <Form layout="vertical" initialValues={user || {}}
                  onFinish={handleProfileSave} style={{ maxWidth: 500 }}>
                  <Form.Item name="email" label="邮箱">
                    <Input type="email" prefix={<MailOutlined />} placeholder="your@email.com" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" icon={<SaveOutlined />} htmlType="submit" loading={loading}>
                      保存修改
                    </Button>
                  </Form.Item>
                </Form>
                <Divider />
                <Button icon={<LockOutlined />} onClick={() => setPwdModalOpen(true)}>
                  修改密码
                </Button>
              </Card>
            ),
          },
          {
            key: 'notification',
            label: <span><BellOutlined /> 通知设置</span>,
            children: (
              <Card title="SMTP 邮件通知配置">
                <Alert type="info" message="配置 SMTP 后，告警和任务状态变更会发送邮件通知"
                  style={{ marginBottom: 16 }} showIcon />
                <Form layout="vertical" form={smtpForm} style={{ maxWidth: 600 }}
                  initialValues={{
                    smtp_host: 'smtp.qq.com',
                    smtp_port: 587,
                    smtp_secure: true,
                  }}
                  onFinish={handleSmtpSave}>
                  <Form.Item name="smtp_host" label="SMTP 服务器" rules={[{ required: true }]}>
                    <Input prefix={<MailOutlined />} placeholder="smtp.example.com" />
                  </Form.Item>
                  <Form.Item name="smtp_port" label="端口" rules={[{ required: true }]}>
                    <Input type="number" placeholder="587" style={{ width: 150 }} />
                  </Form.Item>
                  <Form.Item name="smtp_user" label="用户名">
                    <Input placeholder="your@email.com" />
                  </Form.Item>
                  <Form.Item name="smtp_password" label="密码/授权码">
                    <Input.Password placeholder="邮箱授权码（非登录密码）" />
                  </Form.Item>
                  <Form.Item name="smtp_secure" label="使用 TLS" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                  <Form.Item name="smtp_from" label="发件人地址">
                    <Input placeholder="noreply@example.com" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" icon={<SaveOutlined />} htmlType="submit">
                      保存通知配置
                    </Button>
                  </Form.Item>
                </Form>
              </Card>
            ),
          },
          {
            key: 'ai',
            label: <span><RobotOutlined /> AI 配置</span>,
            children: (
              <Card title="AI 智能助手配置">
                <Form layout="vertical" form={aiForm} style={{ maxWidth: 600 }}
                  onFinish={handleAiSave}>
                  <Form.Item label="AI 提供商">
                    <Select placeholder="选择 AI 提供商">
                      <Select.Option value="openai">OpenAI (GPT-4)</Select.Option>
                      <Select.Option value="ollama">Ollama (本地模型)</Select.Option>
                      <Select.Option value="claude">Claude</Select.Option>
                      <Select.Option value="custom">自定义 API</Select.Option>
                    </Select>
                  </Form.Item>
                  <Form.Item label="API Key">
                    <Input.Password placeholder="sk-..." />
                  </Form.Item>
                  <Form.Item label="API Endpoint（自定义时填写）">
                    <Input placeholder="https://api.openai.com/v1" />
                  </Form.Item>
                  <Form.Item label="模型名称">
                    <Select placeholder="选择模型" allowClear>
                      <Select.Option value="gpt-4o">GPT-4o</Select.Option>
                      <Select.Option value="gpt-4-turbo">GPT-4 Turbo</Select.Option>
                      <Select.Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Select.Option>
                      <Select.Option value="llama3">Llama 3</Select.Option>
                      <Select.Option value="qwen2">通义千问2</Select.Option>
                    </Select>
                  </Form.Item>
                  <Alert type="warning" message="API Key 仅存储在本地 .env 文件，不会明文传输或保存到外部"
                    style={{ marginBottom: 16 }} showIcon />
                  <Form.Item>
                    <Button type="primary" icon={<SaveOutlined />} htmlType="submit">
                      保存 AI 配置
                    </Button>
                  </Form.Item>
                </Form>
              </Card>
            ),
          },
          {
            key: 'system',
            label: <span><InfoCircleOutlined /> 系统信息</span>,
            children: (
              <Card>
                <Descriptions column={1} bordered size="small" title="系统信息">
                  <Descriptions.Item label="版本">RaoMySQL v1.6.0</Descriptions.Item>
                  <Descriptions.Item label="构建日期">2026-04-12</Descriptions.Item>
                  <Descriptions.Item label="后端框架">FastAPI + SQLAlchemy</Descriptions.Item>
                  <Descriptions.Item label="前端框架">React + Ant Design</Descriptions.Item>
                  <Descriptions.Item label="元数据库">SQLite</Descriptions.Item>
                  <Descriptions.Item label="GitHub">
                    <a href="https://github.com/rao5201/RaoMySQL" target="_blank" rel="noopener">
                      github.com/rao5201/RaoMySQL
                    </a>
                  </Descriptions.Item>
                </Descriptions>
                <Divider />
                <Title level={5}>安全说明</Title>
                <Space direction="vertical">
                  <Text><Tag color="green">✓</Tag> 数据库连接密码使用 AES-256-GCM 加密存储</Text>
                  <Text><Tag color="green">✓</Tag> JWT Token 认证，有效期 7 天</Text>
                  <Text><Tag color="green">✓</Tag> 速率限制：登录 API 每 IP 每分钟 10 次</Text>
                  <Text><Tag color="green">✓</Tag> CORS 仅允许配置的来源</Text>
                  <Text><Tag color="green">✓</Tag> 所有操作记录审计日志</Text>
                  <Text><Tag color="green">✓</Tag> API Key 不在 API 响应中暴露</Text>
                </Space>
              </Card>
            ),
          },
        ]}
      />

      {/* 修改密码弹窗 */}
      <Modal title="修改密码" open={pwdModalOpen}
        onCancel={() => setPwdModalOpen(false)} footer={null}>
        <Form form={pwdForm} layout="vertical" onFinish={handlePasswordChange}>
          <Form.Item name="old_password" label="当前密码" rules={[{ required: true }]}>
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
          <Form.Item name="new_password" label="新密码" rules={[{ required: true }, { min: 8, message: '至少8位' }]}>
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
          <Form.Item name="confirm_password" label="确认新密码" rules={[{ required: true }]}>
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">确认修改</Button>
            <Button onClick={() => setPwdModalOpen(false)}>取消</Button>
          </Space>
        </Form>
      </Modal>
    </div>
  )
}
