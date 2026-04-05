import React, { useEffect, useState } from 'react'
import { Table, Button, Modal, Form, Input, Select, Tag, Space, message, Popconfirm, Typography, Card } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, ExperimentOutlined, DatabaseOutlined } from '@ant-design/icons'
import api from '../api'

const { Title } = Typography

export default function Connections() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await api.get('/api/connections')
      setData(res.data)
    } catch { message.error('加载连接失败') }
    finally { setLoading(false) }
  }

  const handleTest = async (id: number) => {
    try {
      const res = await api.post(`/api/connections/${id}/test`)
      if (res.data.status === 'ok') message.success('连接成功！')
      else message.error('连接失败: ' + res.data.message)
    } catch (e: any) { message.error(e.response?.data?.detail || '测试失败') }
  }

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/api/connections/${id}`)
      message.success('已删除')
      loadData()
    } catch (e: any) { message.error(e.response?.data?.detail || '删除失败') }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingId) {
        await api.put(`/api/connections/${editingId}`, values)
        message.success('更新成功')
      } else {
        await api.post('/api/connections', values)
        message.success('添加成功')
      }
      setModalOpen(false)
      form.resetFields()
      setEditingId(null)
      loadData()
    } catch (e: any) { message.error(e.response?.data?.detail || '操作失败') }
  }

  const openEdit = (record: any) => {
    setEditingId(record.id)
    form.setFieldsValue({ ...record, password: '' })
    setModalOpen(true)
  }

  const columns = [
    { title: '名称', dataIndex: 'name', render: (v: string) => <b>{v}</b> },
    { title: '主机', dataIndex: 'host' },
    { title: '端口', dataIndex: 'port', width: 80 },
    { title: '数据库', dataIndex: 'database_name' },
    { title: '标签', dataIndex: 'tags', render: (v: string) => v ? v.split(',').map((t: string) => <Tag key={t}>{t}</Tag>) : null },
    { title: 'SSL', dataIndex: 'ssl_enabled', render: (v: boolean) => <Tag color={v ? 'blue' : 'default'}>{v ? '是' : '否'}</Tag> },
    {
      title: '操作',
      width: 200,
      render: (_: any, record: any) => (
        <Space>
          <Button size="small" icon={<ExperimentOutlined />} onClick={() => handleTest(record.id)}>测试</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>编辑</Button>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>🔗 数据库连接管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingId(null); form.resetFields(); setModalOpen(true) }}>
          添加连接
        </Button>
      </div>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />

      <Modal
        title={editingId ? '编辑连接' : '添加数据库连接'}
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields(); setEditingId(null) }}
        onOk={() => form.submit()}
        width={560}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit} initialValues={{ port: 3306, ssl_enabled: false, max_connections: 100 }}>
          <Form.Item label="连接名称" name="name" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="例如：生产数据库" />
          </Form.Item>
          <Space style={{ width: '100%' }}>
            <Form.Item label="主机地址" name="host" rules={[{ required: true }]} style={{ flex: 1 }}>
              <Input placeholder="127.0.0.1" />
            </Form.Item>
            <Form.Item label="端口" name="port" rules={[{ required: true }]} style={{ width: 100 }}>
              <Input type="number" />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }}>
            <Form.Item label="用户名" name="username" rules={[{ required: true }]} style={{ flex: 1 }}>
              <Input placeholder="root" />
            </Form.Item>
            <Form.Item label={editingId ? '新密码（留空不变）' : '密码'} name="password" rules={[{ required: !editingId }]} style={{ flex: 1 }}>
              <Input.Password />
            </Form.Item>
          </Space>
          <Form.Item label="数据库名" name="database_name" rules={[{ required: true }]}>
            <Input placeholder="mydb" />
          </Form.Item>
          <Form.Item label="标签（逗号分隔）" name="tags">
            <Input placeholder="生产环境, MySQL 8.0" />
          </Form.Item>
          <Space>
            <Form.Item label="SSL 连接" name="ssl_enabled" valuePropName="checked">
              <Input type="checkbox" />
            </Form.Item>
            <Form.Item label="最大连接数" name="max_connections">
              <Input type="number" />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </div>
  )
}
