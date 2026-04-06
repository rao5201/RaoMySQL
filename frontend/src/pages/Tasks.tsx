/**
 * RaoMySQL - 定时任务页面
 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, Select, Switch, Tag, Space, message } from 'antd';
import { PlusOutlined, PlayCircleOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const res = await api.get('/tasks');
      setTasks(res.data.data || []);
    } catch (error) {
      message.error('获取任务列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values) => {
    try {
      if (editingTask) {
        await api.put(`/tasks/${editingTask.id}`, values);
        message.success('更新成功');
      } else {
        await api.post('/tasks', values);
        message.success('创建成功');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingTask(null);
      fetchTasks();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleRun = async (id) => {
    try {
      await api.post(`/tasks/${id}/run`);
      message.success('任务已触发执行');
    } catch (error) {
      message.error('执行失败');
    }
  };

  const handleDelete = async (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个任务吗？',
      onOk: async () => {
        try {
          await api.delete(`/tasks/${id}`);
          message.success('删除成功');
          fetchTasks();
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  const handleEdit = (task) => {
    setEditingTask(task);
    form.setFieldsValue(task);
    setModalVisible(true);
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '任务名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'task_type', key: 'task_type', 
      render: (type) => <Tag>{type}</Tag> 
    },
    { title: 'Cron 表达式', dataIndex: 'cron_expr', key: 'cron_expr' },
    { title: '状态', dataIndex: 'enabled', key: 'enabled',
      render: (enabled) => <Tag color={enabled ? 'green' : 'default'}>{enabled ? '启用' : '禁用'}</Tag>
    },
    { title: '上次执行', dataIndex: 'last_run_at', key: 'last_run_at', 
      render: (v) => v ? new Date(v).toLocaleString() : '-' 
    },
    { title: '执行状态', dataIndex: 'last_status', key: 'last_status',
      render: (s) => s ? <Tag color={s === 'success' ? 'green' : 'red'}>{s}</Tag> : '-'
    },
    {
      title: '操作', key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" icon={<PlayCircleOutlined />} onClick={() => handleRun(record.id)}>执行</Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card title="定时任务" extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingTask(null); form.resetFields(); setModalVisible(true); }}>
          创建任务
        </Button>
      }>
        <Table dataSource={tasks} columns={columns} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
      </Card>

      <Modal
        title={editingTask ? '编辑任务' : '创建任务'}
        open={modalVisible}
        onCancel={() => { setModalVisible(false); setEditingTask(null); form.resetFields(); }}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="任务名称" rules={[{ required: true }]}>
            <Input placeholder="输入任务名称" />
          </Form.Item>
          <Form.Item name="task_type" label="任务类型" rules={[{ required: true }]}>
            <Select placeholder="选择任务类型">
              <Select.Option value="backup">数据库备份</Select.Option>
              <Select.Option value="health_check">健康检查</Select.Option>
              <Select.Option value="report">报告生成</Select.Option>
              <Select.Option value="cleanup">数据清理</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="cron_expr" label="Cron 表达式">
            <Input placeholder="例如: 0 2 * * * (每天凌晨2点)" />
          </Form.Item>
          <Form.Item name="config" label="配置 (JSON)">
            <Input.TextArea rows={3} placeholder='{"database": "mydb"}' />
          </Form.Item>
          <Form.Item name="enabled" label="启用任务" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Tasks;