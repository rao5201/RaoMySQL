/**
 * RaoMySQL - Audit Log Dashboard
 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Space, Button, Input, Select, DatePicker, Row, Col, Statistic, message, Modal, Spin } from 'antd';
import { FileSearchOutlined, CheckCircleOutlined, CloseCircleOutlined, StopOutlined, ReloadOutlined, DeleteOutlined, BarChartOutlined } from '@ant-design/icons';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

const { RangePicker } = DatePicker;

const AuditLog = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [stats, setStats] = useState<any>(null);
  const [filters, setFilters] = useState<any>({});

  useEffect(() => { fetchLogs(); fetchStats(); }, [page]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params: any = { page, page_size: 50, ...filters };
      const res = await api.get('/audit/logs', { params });
      setLogs(res.data.data || []);
      setTotal(res.data.total || 0);
    } catch { message.error('Failed to load audit logs'); }
    finally { setLoading(false); }
  };

  const fetchStats = async () => {
    try {
      const res = await api.get('/audit/stats');
      setStats(res.data);
    } catch {}
  };

  const handleSearch = () => { setPage(1); fetchLogs(); };

  const handleCleanup = () => {
    Modal.confirm({
      title: 'Clean Old Logs',
      content: 'Delete audit logs older than 90 days?',
      onOk: async () => {
        try {
          const res = await api.delete('/audit/logs/cleanup', { params: { days: 90 } });
          message.success(`Deleted ${res.data.deleted} records`);
          fetchLogs(); fetchStats();
        } catch { message.error('Cleanup failed'); }
      }
    });
  };

  const actionColors: Record<string, string> = {
    login: 'blue', logout: 'default', query: 'green', write: 'orange',
    delete: 'red', backup: 'purple', restore: 'cyan', config: 'geekblue'
  };
  const statusIcons: Record<string, React.ReactNode> = {
    success: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    failed: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
    denied: <StopOutlined style={{ color: '#faad14' }} />,
  };

  const columns = [
    { title: 'Time', dataIndex: 'created_at', width: 170, render: (v: string) => new Date(v).toLocaleString() },
    { title: 'User', dataIndex: 'username', width: 100 },
    { title: 'Action', dataIndex: 'action', width: 100, render: (v: string) => <Tag color={actionColors[v]}>{v}</Tag> },
    { title: 'Resource', dataIndex: 'resource', width: 180, ellipsis: true },
    {
      title: 'Detail', dataIndex: 'detail', ellipsis: true,
      render: (v: any) => typeof v === 'string' ? (v.length > 120 ? v.slice(0, 120) + '...' : v) : JSON.stringify(v)?.slice(0, 120)
    },
    { title: 'IP', dataIndex: 'ip_address', width: 130 },
    {
      title: 'Status', dataIndex: 'status', width: 80, align: 'center' as const,
      render: (v: string) => <Tag icon={statusIcons[v]} color={v === 'success' ? 'success' : v === 'failed' ? 'error' : 'warning'}>{v}</Tag>
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      {/* Stats Cards */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}><Card><Statistic title="Total Logs" value={stats.total} prefix={<FileSearchOutlined />} /></Card></Col>
          <Col span={6}><Card><Statistic title="Today" value={stats.today} valueStyle={{ color: '#1890ff' }} /></Card></Col>
          <Col span={6}><Card><Statistic title="Failed" value={stats.failed} valueStyle={{ color: '#ff4d4f' }} prefix={<CloseCircleOutlined />} /></Card></Col>
          <Col span={6}><Card><Statistic title="Denied" value={stats.denied} valueStyle={{ color: '#faad14' }} prefix={<StopOutlined />} /></Card></Col>
        </Row>
      )}

      {/* Top Actions + Top Users */}
      {stats && (stats.top_actions?.length > 0 || stats.top_users?.length > 0) && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          {stats.top_actions?.length > 0 && (
            <Col span={12}>
              <Card title={<><BarChartOutlined /> Top Actions</>} size="small">
                {stats.top_actions.map((a: any) => (
                  <div key={a.action} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f5f5f5' }}>
                    <Tag color={actionColors[a.action]}>{a.action}</Tag>
                    <span style={{ fontWeight: 600 }}>{a.count}</span>
                  </div>
                ))}
              </Card>
            </Col>
          )}
          {stats.top_users?.length > 0 && (
            <Col span={12}>
              <Card title={<><BarChartOutlined /> Top Users</>} size="small">
                {stats.top_users.map((u: any) => (
                  <div key={u.username} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f5f5f5' }}>
                    <span>{u.username || 'unknown'}</span>
                    <span style={{ fontWeight: 600 }}>{u.count}</span>
                  </div>
                ))}
              </Card>
            </Col>
          )}
        </Row>
      )}

      {/* Filters + Table */}
      <Card
        title="Audit Logs"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => { fetchLogs(); fetchStats(); }}>Refresh</Button>
            <Button danger icon={<DeleteOutlined />} onClick={handleCleanup}>Cleanup</Button>
          </Space>
        }
      >
        <Space wrap style={{ marginBottom: 16 }}>
          <Input placeholder="Keyword" style={{ width: 180 }} onChange={e => setFilters(f => ({ ...f, keyword: e.target || undefined }))} allowClear />
          <Select placeholder="Action" style={{ width: 130 }} allowClear onChange={v => setFilters(f => ({ ...f, action: v }))}>
            {['login','logout','query','write','delete','backup','restore','config'].map(a => (
              <Select.Option key={a} value={a}>{a}</Select.Option>
            ))}
          </Select>
          <Select placeholder="Status" style={{ width: 120 }} allowClear onChange={v => setFilters(f => ({ ...f, status: v }))}>
            <Select.Option value="success">success</Select.Option>
            <Select.Option value="failed">failed</Select.Option>
            <Select.Option value="denied">denied</Select.Option>
          </Select>
          <Button type="primary" onClick={handleSearch}>Search</Button>
        </Space>

        <Table
          dataSource={logs}
          columns={columns}
          rowKey="id"
          loading={loading}
          size="small"
          scroll={{ y: 480 }}
          pagination={{
            current: page, total, pageSize: 50, showTotal: t => `Total ${t}`,
            onChange: p => setPage(p)
          }}
        />
      </Card>
    </div>
  );
};

export default AuditLog;
