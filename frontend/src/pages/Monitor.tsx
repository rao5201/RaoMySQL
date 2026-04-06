/**
 * RaoMySQL - 监控中心页面
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Progress, Button, Space, Tabs } from 'antd';
import { ReloadOutlined, WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

const Monitor = () => {
  const [health, setHealth] = useState({});
  const [connections, setConnections] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [healthRes, alertsRes] = await Promise.all([
        api.get('/monitor/health'),
        api.get('/monitor/alerts')
      ]);
      setHealth(healthRes.data);
      setAlerts(alertsRes.data.data || []);
    } catch (error) {
      console.error('获取监控数据失败', error);
    } finally {
      setLoading(false);
    }
  };

  const getConnectionStatus = async (id) => {
    try {
      const res = await api.get(`/monitor/${id}/status`);
      return res.data;
    } catch (error) {
      return { status: 'disconnected' };
    }
  };

  const alertColumns = [
    { title: '级别', dataIndex: 'level', key: 'level', 
      render: (level) => {
        const colors = { critical: 'red', warning: 'orange', info: 'blue' };
        return <Tag color={colors[level]}>{level}</Tag>;
      }
    },
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (s) => <Tag color={s === 'unread' ? 'red' : 'default'}>{s}</Tag>
    },
    { title: '时间', dataIndex: 'created_at', key: 'created_at', render: (v) => new Date(v).toLocaleString() },
    {
      title: '操作', key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleMarkRead(record.id)}>标记已读</Button>
          <Button type="link" size="small" onClick={() => handleResolve(record.id)}>解决</Button>
        </Space>
      )
    }
  ];

  const handleMarkRead = async (id) => {
    try {
      await api.put(`/monitor/alerts/${id}/read`);
      fetchData();
    } catch (error) {
      console.error('标记失败', error);
    }
  };

  const handleResolve = async (id) => {
    try {
      await api.put(`/monitor/alerts/${id}/resolve`);
      fetchData();
    } catch (error) {
      console.error('解决失败', error);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>监控中心</h1>
      
      {/* 健康概览 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总连接数" value={health.total_connections || 0} prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="健康" value={health.healthy || 0} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="警告" value={health.warning || 0} prefix={<WarningOutlined />} valueStyle={{ color: '#faad14' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="严重" value={health.critical || 0} prefix={<WarningOutlined />} valueStyle={{ color: '#ff4d4f' }} />
          </Card>
        </Col>
      </Row>

      {/* 健康评分 */}
      <Card title="健康评分" style={{ marginBottom: 24 }}>
        <Progress percent={health.score || 0} status={health.score >= 80 ? 'success' : health.score >= 60 ? 'normal' : 'exception'} />
        <p style={{ color: '#999', marginTop: 8 }}>最后检查: {health.last_checked ? new Date(health.last_checked).toLocaleString() : '-'}</p>
      </Card>

      {/* 告警列表 */}
      <Card title="告警列表" extra={<Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>}>
        <Table dataSource={alerts} columns={alertColumns} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
      </Card>
    </div>
  );
};

export default Monitor;