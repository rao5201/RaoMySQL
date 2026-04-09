import React, { useState, useEffect } from 'react'
import {
  Table, Button, Tag, Space, Modal, Form, Input, Select, message,
  Popconfirm, Card, Row, Col, Statistic, Typography, Tooltip
} from 'antd'
import {
  UserAddOutlined, EditOutlined, DeleteOutlined, ReloadOutlined,
  LockOutlined, StopOutlined, CheckCircleOutlined
} from '@ant-design/icons'
import api from '../api'

const { Title } = Typography
const { Option } = Select

export default function Users() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [stats, setStats] = useState<any>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isPwdModalOpen, setIsPwdModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<any>(null)
  const [pwdUserId, setPwdUserId] = useState<any>(null)
  const [filterRole, setFilterRole] = useState<string | undefined>()
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [searchKw, setSearchKw] = useState('')
  const [form] = Form.useForm()
  const [pwdForm] = Form.useForm()

  const token = localStorage.getItem('raomysql_token')
  const isAdmin = () => {
    try {
      return JSON.parse(atob(token?.split('.')[1] || 'e30')).role === 'admin'
    } catch { return false }
  }

  useEffect(() => {
    if (isAdmin()) loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const res = await api.get('/api/users/stats/overview')
      setStats(res.data)
    } catch {}
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const params: any = { page, page_size: pageSize }
      if (filterRole) params.role = filterRole
      if (filterStatus) params.status = filterStatus
      if (searchKw) params.keyword = searchKw
      const res = await api.get('/api/users', { params })
      setData(res.data.items)
      setTotal(res.data.total)
    } catch (err: any) {
      message.error(err.response?.data?.detail || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAdmin()) loadData()
  }, [page, pageSize, filterRole, filterStatus, searchKw])

  const handleCreate = () => {
    setEditingUser(null)
    form.resetFields()
    setIsModalOpen(true)
  }

  const handleEdit = (record: any) => {
    setEditingUser(record)
    form.setFieldsValue({ username: record.username, email: record.email, role: record.role, status: record.status })
    setIsModalOpen(true)
  }

  const handleDelete = async (userId: number) => {
    try {
      await api.delete(`/api/users/${userId}`)
      message.success('删除成功')
      loadData()
      loadStats()
    } catch (err: any) {
      message.error(err.response?.data?.detail || '删除失败')
    }
  }

  const handleToggle = async (userId: number) => {
    try {
      const res = await api.post(`/api/users/${userId}/toggle-status`)
      message.success(res.data.message)
      loadData()
      loadStats()
    } catch (err: any) {
      message.error(err.response?.data?.detail || '操作失败')
    }
  }

  const handleResetPwd = (userId: number) => {
    setPwdUserId(userId)
    pwdForm.resetFields()
    setIsPwdModalOpen(true)
  }

  const onModalOk = async () => {
    try {
      const values = await form.validateFields()
      if (editingUser) {
        await api.put(`/api/users/${editingUser.id}`, values)
        message.success('修改成功')
      } else {
        await api.post('/api/users', { ...values, password: values.password || 'Raomysql@123' })
        message.success('创建成功')
      }
      setIsModalOpen(false)
      loadData()
      loadStats()
    } catch (err: any) {
      if (!err.response?.data) throw err
      message.error(err.response.data.detail || '操作失败')
    }
  }

  const onPwdOk = async () => {
    try {
      const values = await pwdForm.validateFields()
      await api.post(`/api/users/${pwdUserId}/reset-password`, values)
      message.success('密码已重置为: ' + values.new_password)
      setIsPwdModalOpen(false)
    } catch (err: any) {
      if (!err.response?.data) throw err
      message.error(err.response.data.detail || '操作失败')
    }
  }

  const roleColor: Record<string, string> = {
    admin: 'red', editor: 'blue', viewer: 'default',
    support: 'green', finance: 'orange', supplier: 'purple'
  }
  const statusColor: Record<string, string> = { active: 'success', disabled: 'error' }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    {
      title: '用户名', dataIndex: 'username',
      render: (v: string, r: any) => (
        <b style={{ fontSize: 15 }}>{v}</b>
      )
    },
    {
      title: '角色', dataIndex: 'role',
      render: (v: string) => <Tag color={roleColor[v] || 'default'}>{v?.toUpperCase()}</Tag>
    },
    { title: '邮箱', dataIndex: 'email', ellipsis: true },
    {
      title: '状态', dataIndex: 'status',
      render: (v: string) => (
        <Tag color={statusColor[v]} icon={v === 'active' ? <CheckCircleOutlined /> : <StopOutlined />}>
          {v === 'active' ? '正常' : '禁用'}
        </Tag>
      )
    },
    { title: '创建时间', dataIndex: 'created_at', width: 170 },
    {
      title: '操作',
      width: 220,
      render: (_: any, record: any) => (
        <Space size="small">
          <Tooltip title="编辑"><Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} /></Tooltip>
          <Tooltip title="重置密码"><Button size="small" icon={<LockOutlined />} onClick={() => handleResetPwd(record.id)} /></Tooltip>
          <Tooltip title={record.status === 'active' ? '禁用' : '启用'}>
            <Button size="small" type={record.status === 'active' ? 'default' : 'primary'} danger={record.status === 'active'} onClick={() => handleToggle(record.id)}>
              {record.status === 'active' ? '禁用' : '启用'}
            </Button>
          </Tooltip>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Tooltip title="删除">
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: 0 }}>
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}><Card><Statistic title="总用户" value={stats.total} /></Card></Col>
          <Col span={6}><Card><Statistic title="正常" value={stats.active} valueStyle={{ color: '#52c41a' }} /></Card></Col>
          <Col span={6}><Card><Statistic title="禁用" value={stats.disabled} valueStyle={{ color: '#ff4d4f' }} /></Card></Col>
          <Col span={6}><Card><Statistic title="管理员" value={stats.by_role?.admin || 0} valueStyle={{ color: '#ff4d4f' }} /></Card></Col>
        </Row>
      )}

      <Card
        title={<Title level={4} style={{ margin: 0 }}>👥 用户管理</Title>}
        extra={
          <Space>
            <Input.Search placeholder="搜索用户名" style={{ width: 200 }} onSearch={v => { setSearchKw(v); setPage(1) }} allowClear />
            <Select placeholder="角色筛选" style={{ width: 120 }} allowClear onChange={v => { setFilterRole(v); setPage(1) }}>
              <Option value="admin">管理员</Option><Option value="editor">编辑</Option><Option value="viewer">访客</Option>
            </Select>
            <Select placeholder="状态筛选" style={{ width: 120 }} allowClear onChange={v => { setFilterStatus(v); setPage(1) }}>
              <Option value="active">正常</Option><Option value="disabled">禁用</Option>
            </Select>
            <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
            <Button type="primary" icon={<UserAddOutlined />} onClick={handleCreate}>添加用户</Button>
          </Space>
        }
      >
        <Table
          dataSource={data}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page, pageSize, total,
            showSizeChanger: true, showQuickJumper: true,
            showTotal: t => `共 ${t} 条`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps) }
          }}
        />
      </Card>

      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={isModalOpen}
        onOk={onModalOk}
        onCancel={() => setIsModalOpen(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="username" label="用户名" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input disabled={!!editingUser} placeholder={editingUser ? '(不可修改)' : '请输入用户名'} />
          </Form.Item>
          {!editingUser && (
            <Form.Item name="password" label="初始密码" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password placeholder="留空则使用默认密码: Raomysql@123" />
            </Form.Item>
          )}
          <Form.Item name="email" label="邮箱">
            <Input placeholder="选填" />
          </Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true, message: '请选择角色' }]}>
            <Select>
              <Option value="admin">管理员</Option>
              <Option value="editor">编辑</Option>
              <Option value="viewer">访客</Option>
            </Select>
          </Form.Item>
          {editingUser && (
            <Form.Item name="status" label="状态">
              <Select>
                <Option value="active">正常</Option>
                <Option value="disabled">禁用</Option>
              </Select>
            </Form.Item>
          )}
        </Form>
      </Modal>

      <Modal
        title="重置密码"
        open={isPwdModalOpen}
        onOk={onPwdOk}
        onCancel={() => setIsPwdModalOpen(false)}
        okText="确认重置"
      >
        <Form form={pwdForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '至少 6 个字符' }
            ]}
          >
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>
          <div style={{ background: '#fffbe6', padding: 12, borderRadius: 6, border: '1px solid #ffe58f' }}>
            💡 重置后请及时告知用户
          </div>
        </Form>
      </Modal>
    </div>
  )
}
