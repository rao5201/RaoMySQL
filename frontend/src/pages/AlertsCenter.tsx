import React, { useState, useEffect } from 'react'
import {
  Card, Table, Tag, Button, Space, Modal, Form, Input, Select,
  Popconfirm, Typography, Badge, Statistic, Row, Col, message, Tabs, Drawer
} from 'antd'
import {
  BellOutlined, CheckCircleOutlined, DeleteOutlined, EyeOutlined,
  WarningOutlined, CloseCircleOutlined, InfoCircleOutlined, PlusOutlined
} from '@ant-design/icons'
import request from '../api'

const { Title, Text } = Typography
const { TextArea } = Input

const LEVEL_COLORS: Record<string, string> = {
  critical: 'red', warning: 'orange', info: 'blue'
}
const LEVEL_ICONS: Record<string, React.ReactNode> = {
  critical: <CloseCircleOutlined />, warning: <WarningOutlined />, info: <InfoCircleOutlined />
}
const STATUS_COLORS: Record<string, string> = {
  unread: 'red', read: 'default', resolved: 'green'
}

export default function AlertsCenter() {
  const [alerts, setAlerts] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({ total: 0, unread: 0, critical_unread: 0, warning_unread: 0, today: 0 })
  const [levelFilter, setLevelFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('unread')
  const [createVisible, setCreateVisible] = useState(false)
  const [detailVisible, setDetailVisible] = useState(false)
  const [selectedAlert, setSelectedAlert] = useState<any>(null)
  const [connections, setConnections] = useState<any[]>([])
  const [form] = Form.useForm()
  const pageSize = 20

  const loadStats = async () => {
    try {
      const res = await request.get('/alerts/stats/summary')
      setStats(res.data)
    } catch { /* ignore */ }
  }

  const loadAlerts = async () => {
    setLoading(true)
    try {
      const params: any = { page, page_size: pageSize }
      if (levelFilter) params.level = levelFilter
      if (statusFilter) params.status = statusFilter
      const res = await request.get('/alerts', { params })
      setAlerts(res.data.data)
      setTotal(res.data.total)
    } finally {
      setLoading(false)
    }
  }

  const loadConnections = async () => {
    try {
      const res = await request.get('/connections')
      setConnections(res.data)
    } catch { /* ignore */ }
  }

  useEffect(() => { loadStats(); loadAlerts(); loadConnections() }, [page, levelFilter, statusFilter])

  const handleRead = async (id: number) => {
    await request.put(`/alerts/${id}/read`)
    message.success('已标记为已读')
    loadAlerts(); loadStats()
  }

  const handleResolve = async (id: number) => {
    await request.put(`/alerts/${id}/resolve`)
    message.success('已标记为已解决')
    loadAlerts(); loadStats()
  }

  const handleDelete = async (id: number) => {
    await request.delete(`/alerts/${id}`)
    message.success('已删除')
    loadAlerts(); loadStats()
  }

  const handleBatchRead = async () => {
    const unread = alerts.filter(a => a.status === 'unread').map(a => a.id)
    if (!unread.length) { message.warning('没有未读告警'); return }
    await request.put('/alerts/batch/read', { alert_ids: unread })
    message.success('全部已读')
    loadAlerts(); loadStats()
  }

  const handleCreate = async (values: any) => {
    await request.post('/alerts', values)
    message.success('告警已创建')
    setCreateVisible(false); form.resetFields()
    loadAlerts(); loadStats()
  }

  const columns = [
    {
      title: '级别', dataIndex: 'level', width: 100,
      render: (level: string) => (
        <Tag color={LEVEL_COLORS[level] || 'default'} icon={LEVEL_ICONS[level]}>
          {level.toUpperCase()}
        </Tag>
      ),
      filters: [
        { text: 'Critical', value: 'critical' },
        { text: 'Warning', value: 'warning' },
        { text: 'Info', value: 'info' },
      ],
      onFilter: (value: any, record: any) => record.level === value,
    },
    {
      title: '标题', dataIndex: 'title',
      render: (title: string, row: any) => (
        <a onClick={() => { setSelectedAlert(row); setDetailVisible(true) }}>
          {row.status === 'unread' ? <strong>{title}</strong> : title}
        </a>
      ),
    },
    {
      title: '连接', dataIndex: 'connection_name', width: 140,
      render: (v: string) => v || <Text type="secondary">—</Text>,
    },
    {
      title: '状态', dataIndex: 'status', width: 90,
      render: (s: string) => <Tag color={STATUS_COLORS[s]}>{s === 'unread' ? '未读' : s === 'read' ? '已读' : '已解决'}</Tag>,
      filters: [
        { text: '未读', value: 'unread' },
        { text: '已读', value: 'read' },
        { text: '已解决', value: 'resolved' },
      ],
      onFilter: (value: any, record: any) => record.status === value,
    },
    { title: '时间', dataIndex: 'created_at', width: 170 },
    {
      title: '操作', width: 180,
      render: (_: any, row: any) => (
        <Space>
          {row.status !== 'read' && (
            <Button size="small" icon={<EyeOutlined />} onClick={() => handleRead(row.id)}>
              已读
            </Button>
          )}
          {row.status !== 'resolved' && (
            <Button size="small" type="link" icon={<CheckCircleOutlined />}
              onClick={() => handleResolve(row.id)}>解决</Button>
          )}
          <Popconfirm title="删除此告警？" onConfirm={() => handleDelete(row.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}><BellOutlined /> 告警中心</Title>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {[
          { label: '全部告警', value: stats.total, color: 'blue' },
          { label: '未读', value: stats.unread, color: stats.unread > 0 ? 'red' : 'default' },
          { label: '严重未读', value: stats.critical_unread, color: 'red' },
          { label: '今日新增', value: stats.today, color: 'orange' },
        ].map(s => (
          <Col span={6} key={s.label}>
            <Card size="small">
              <Statistic title={s.label} value={s.value} valueStyle={{ color: s.color === 'red' ? '#cf1322' : s.color === 'orange' ? '#d46b08' : s.color === 'blue' ? '#1677ff' : undefined }} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 工具栏 */}
      <Card size="small" style={{ marginBottom: 12 }}>
        <Space wrap>
          <Button icon={<PlusOutlined />} type="primary" onClick={() => setCreateVisible(true)}>
            创建告警
          </Button>
          <Button icon={<CheckCircleOutlined />} onClick={handleBatchRead}>
            全部标为已读
          </Button>
          <Select placeholder="告警级别" allowClear style={{ width: 120 }}
            onChange={v => { setLevelFilter(v || ''); setPage(1) }}>
            <Select.Option value="critical">Critical</Select.Option>
            <Select.Option value="warning">Warning</Select.Option>
            <Select.Option value="info">Info</Select.Option>
          </Select>
          <Select placeholder="状态" allowClear style={{ width: 120 }}
            onChange={v => { setStatusFilter(v || ''); setPage(1) }} value={statusFilter}>
            <Select.Option value="unread">未读</Select.Option>
            <Select.Option value="read">已读</Select.Option>
            <Select.Option value="resolved">已解决</Select.Option>
          </Select>
        </Space>
      </Card>

      {/* 告警列表 */}
      <Card>
        <Table
          dataSource={alerts}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page, pageSize, total,
            showTotal: t => `共 ${t} 条`,
            onChange: p => setPage(p),
            showSizeChanger: false,
          }}
          locale={{ emptyText: '暂无告警' }}
        />
      </Card>

      {/* 创建告警 */}
      <Modal title="创建告警" open={createVisible} onCancel={() => setCreateVisible(false)} footer={null}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="level" label="级别" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="critical"><Tag color="red">CRITICAL</Tag></Select.Option>
              <Select.Option value="warning"><Tag color="orange">WARNING</Tag></Select.Option>
              <Select.Option value="info"><Tag color="blue">INFO</Tag></Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="connection_id" label="关联连接">
            <Select allowClear placeholder="选择数据库连接（可选）">
              {connections.map(c => <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}>
            <Input placeholder="告警标题" />
          </Form.Item>
          <Form.Item name="content" label="详情">
            <TextArea rows={4} placeholder="详细描述..." />
          </Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">创建</Button>
            <Button onClick={() => setCreateVisible(false)}>取消</Button>
          </Space>
        </Form>
      </Modal>

      {/* 告警详情 */}
      <Drawer title="告警详情" open={detailVisible} onClose={() => setDetailVisible(false)}
        width={500}
        extra={
          selectedAlert && (
            <Space>
              {selectedAlert.status !== 'read' && (
                <Button size="small" onClick={() => { handleRead(selectedAlert.id); setDetailVisible(false) }}>
                  标为已读
                </Button>
              )}
              {selectedAlert.status !== 'resolved' && (
                <Button size="small" type="primary" onClick={() => { handleResolve(selectedAlert.id); setDetailVisible(false) }}>
                  标为已解决
                </Button>
              )}
            </Space>
          )
        }>
        {selectedAlert && (
          <div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div><Tag color={LEVEL_COLORS[selectedAlert.level]} icon={LEVEL_ICONS[selectedAlert.level]}>
                {selectedAlert.level?.toUpperCase()}
              </Tag> <Tag color={STATUS_COLORS[selectedAlert.status]}>
                {selectedAlert.status === 'unread' ? '未读' : selectedAlert.status === 'read' ? '已读' : '已解决'}
              </Tag></div>
              <Title level={5}>{selectedAlert.title}</Title>
              <Text type="secondary">创建于：{selectedAlert.created_at}</Text>
              {selectedAlert.connection_name && <Text type="secondary"><br/>关联连接：{selectedAlert.connection_name}</Text>}
              <hr/>
              <Text>{selectedAlert.content || '（无详情）'}</Text>
            </Space>
          </div>
        )}
      </Drawer>
    </div>
  )
}
