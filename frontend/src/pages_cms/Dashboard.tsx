/**
 * RaoCMS - 仪表盘
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button } from 'antd';
import { ArticleOutlined, UserOutlined, ShopOutlined, DollarOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    articles: 0,
    users: 0,
    suppliers: 0,
    products: 0
  });
  const [recentArticles, setRecentArticles] = useState([]);
  const [pendingAudits, setPendingAudits] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // 获取统计数据
      const [articlesRes, usersRes, suppliersRes] = await Promise.all([
        api.get('/articles?page_size=5'),
        api.get('/portal/users/stats'),
        api.get('/suppliers/stats')
      ]);

      setStats({
        articles: articlesRes.data.length || 0,
        users: usersRes.data.total || 0,
        suppliers: suppliersRes.data.total || 0,
        products: 0
      });

      setRecentArticles(articlesRes.data.slice(0, 5));
      
      // 获取待审核文章
      const pending = articlesRes.data.filter(a => a.status === 'pending');
      setPendingAudits(pending);
    } catch (error) {
      console.error('获取数据失败', error);
    }
  };

  const user = JSON.parse(localStorage.getItem('cms_user') || '{}');
  const roleColors = {
    admin: '#f5222d',
    customer_service: '#1890ff',
    finance: '#52c41a'
  };

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status) => {
        const colors = { draft: 'default', pending: 'orange', published: 'green', rejected: 'red', offline: 'default' };
        return <Tag color={colors[status] || 'default'}>{status}</Tag>;
      }
    },
    { title: '作者', dataIndex: 'author_name', key: 'author_name' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v) => new Date(v).toLocaleString() }
  ];

  return (
    <div style={{ padding: 24 }}>
      <h1>仪表盘</h1>
      
      {/* 欢迎信息 */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2>欢迎回来，{user.real_name || user.username}</h2>
            <span style={{ color: '#999' }}>角色：<Tag color={roleColors[user.role]}>{user.role}</Tag></span>
          </div>
        </div>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="文章总数" value={stats.articles} prefix={<ArticleOutlined />} onClick={() => navigate('/articles')} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="注册用户" value={stats.users} prefix={<UserOutlined />} onClick={() => navigate('/portal-users')} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="供应商" value={stats.suppliers} prefix={<ShopOutlined />} onClick={() => navigate('/suppliers')} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="产品数量" value={stats.products} prefix={<DollarOutlined />} onClick={() => navigate('/products')} />
          </Card>
        </Col>
      </Row>

      {/* 待审核提醒 */}
      {pendingAudits.length > 0 && (
        <Card 
          title="待审核文章" 
          extra={<Button type="link" onClick={() => navigate('/articles')}>查看全部</Button>}
          style={{ marginBottom: 24 }}
        >
          <Table
            dataSource={pendingAudits}
            columns={columns}
            rowKey="id"
            pagination={false}
            size="small"
          />
        </Card>
      )}

      {/* 最近文章 */}
      <Card 
        title="最近文章" 
        extra={<Button type="link" onClick={() => navigate('/articles')}>查看全部</Button>}
      >
        <Table
          dataSource={recentArticles}
          columns={columns}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
};

export default Dashboard;