/**
 * RaoMySQL - 备份恢复页面
 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, Select, message, Tag, Space } from 'antd';
import { PlusOutlined, DeleteOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

const Backups = () => {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [connections, setConnections] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchBackups();
    fetchConnections();
  }, []);

  const fetchBackups = async () => {
    setLoading(true);
    try {
      const res = await api.get('/backups');
      setBackups(res.data.data || []);
    } catch (error) {
      message.error('获取备份列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchConnections = async () => {
    try {
      const res = await api.get('/connections');
      setConnections(res.data || []);
    } catch (error) {
      console.error('获取连接失败', error);
    }
  };

  const handleCreateBackup = async (values) => {
    try {
      await api.post('/backups', values);
      message.success('备份任务已创建');
      setModalVisible(false);
      form.resetFields();
      fetchBackups();
    } catch (error) {
      message.error('创建备份失败');
    }
  };

  const handleDelete = async (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个备份吗？',
      onOk: async () => {
        try {
          await api.delete(`/backups/${id}`);
          message.success('删除成功');
          fetchBackups();
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '连接ID', dataIndex: 'connection_id', key: 'connection_id', width: 80 },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status) => {
        const colors = { pending: 'orange', running: 'blue', success: 'green', failed: 'red' };
        return <Tag color={colors[status] || 'default'}>{status}</Tag>;
      }
    },
    { title: '类型', dataIndex: 'backup_type', key: 'backup_type' },
    { 
      title: '文件大小', 
      dataIndex: 'file_size', 
      key: 'file_size',
      render: (size) => size ? `${(size / 1024 / 1024).toFixed(2)} MB` : '-'
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v) => new Date(v).toLocaleString() },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" icon={<DownloadOutlined />}>下载</Button>
          <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card title="备份恢复" extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
          创建备份
        </Button>
      }>
        <Table
          dataSource={backups}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="创建备份"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateBackup}>
          <Form.Item name="connection_id" label="数据库连接" rules={[{ required: true }]}>
            <Select placeholder="选择数据库连接">
              {connections.map(c => (
                <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="database" label="数据库名" rules={[{ required: true }]}>
            <Input placeholder="输入数据库名" />
          </Form.Item>
          <Form.Item name="backup_name" label="备份名称（可选）">
            <Input placeholder="留空自动生成" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Backups;