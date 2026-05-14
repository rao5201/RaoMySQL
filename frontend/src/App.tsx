import React, { useState, useEffect } from 'react'
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, Layout, Menu, theme, Badge, Dropdown, Avatar, Space } from 'antd'
import {
  DatabaseOutlined, TableOutlined, RobotOutlined, AlertOutlined,
  SettingOutlined, UserOutlined, LogoutOutlined, DashboardOutlined,
  FileSearchOutlined, ExportOutlined, TeamOutlined, CloudUploadOutlined,
  BellOutlined
} from '@ant-design/icons'
import zhCN from 'antd/locale/zh_CN'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Connections from './pages/Connections'
import SqlEditor from './pages/SqlEditor'
import Backups from './pages/Backups'
import Tasks from './pages/Tasks'
import AIAssistant from './pages/AIAssistant'
import Settings from './pages/Settings'
import AuditLog from './pages/AuditLog'
import DataExport from './pages/DataExport'
import AIServices from './pages/AIServices'
import AISettings from './pages/AISettings'
import Users from './pages/Users'
import AlertsCenter from './pages/AlertsCenter'
import request from './api'

const { Header, Sider, Content } = Layout

function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const [unreadAlerts, setUnreadAlerts] = useState(0)

  useEffect(() => {
    // 加载未读告警数
    request.get('/alerts/stats/summary').then(r => {
      setUnreadAlerts(r.data?.unread || 0)
    }).catch(() => {})
  }, [])

  const handleMenuClick = (key: string) => {
    if (key === '/login' || key === '/logout') {
      localStorage.removeItem('raomysql_token')
      window.location.hash = '/login'
    } else {
      window.location.hash = key
    }
  }

  const userMenu = {
    items: [
      { key: '/profile', icon: <UserOutlined />, label: 'Profile' },
      { type: 'divider' as const },
      { key: '/logout', icon: <LogoutOutlined />, label: 'Logout', danger: true },
    ]
  }

  const getUsername = () => {
    try {
      const token = localStorage.getItem('raomysql_token') || ''
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.username || 'User'
    } catch { return 'User' }
  }

  const getRole = () => {
    try {
      const token = localStorage.getItem('raomysql_token') || ''
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.role || 'viewer'
    } catch { return 'viewer' }
  }

  const menuItems = [
    { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
    { key: '/connections', icon: <DatabaseOutlined />, label: 'Connections' },
    { key: '/sql', icon: <TableOutlined />, label: 'SQL Editor' },
    { key: '/backups', icon: <CloudUploadOutlined />, label: 'Backups' },
    { key: '/alerts', icon: <BellOutlined />, label: (
      <span>Alerts{unreadAlerts > 0 && <Badge count={unreadAlerts} size="small" style={{ marginLeft: 6 }} />}</span>
    )},
    { key: '/tasks', icon: <SettingOutlined />, label: 'Tasks' },
    { type: 'divider' as const },
    { key: '/ai', icon: <RobotOutlined />, label: 'AI Services' },
    { key: '/ai-settings', icon: <RobotOutlined />, label: 'AI Settings' },
    { type: 'divider' as const },
    { key: '/users', icon: <TeamOutlined />, label: 'User Management' },
    { key: '/export', icon: <ExportOutlined />, label: 'Data Export' },
    { key: '/audit', icon: <FileSearchOutlined />, label: 'Audit Log' },
    { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme="dark" width={220}>
        <a href="./index.html" style={{
          height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontSize: 16, fontWeight: 700, letterSpacing: 1,
          textDecoration: 'none', cursor: 'pointer'
        }}>
          {collapsed ? '🏠' : '🏠 RaoMySQL'}
        </a>
        <Menu
          theme="dark" mode="inline" defaultSelectedKeys={['/dashboard']}
          items={menuItems} onClick={({ key }) => handleMenuClick(key)}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#fff', padding: '0 24px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <a href="./index.html" style={{ color: '#1890ff', fontSize: 14, textDecoration: 'none' }}>
            ← 返回首页
          </a>
          <Dropdown menu={{ ...userMenu, onClick: ({ key }) => handleMenuClick(key) }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
              <span>{getUsername()}</span>
              <Badge count={getRole()} style={{ backgroundColor: getRole() === 'admin' ? '#ff4d4f' : '#1890ff' }} />
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: 16, overflow: 'initial' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}

export default function App() {
  const [token] = useState(() => localStorage.getItem('raomysql_token') || '')
  return (
    <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm, token: { colorPrimary: '#1890ff' } }} locale={zhCN}>
      <HashRouter>
        <Routes>
          <Route path="/login" element={token ? <Navigate to="/dashboard" /> : <Login />} />
          <Route path="/register" element={token ? <Navigate to="/dashboard" /> : <Register />} />
          <Route path="/*" element={
            token ? (
              <AppLayout>
                <Routes>
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/connections" element={<Connections />} />
                  <Route path="/sql" element={<SqlEditor />} />
                  <Route path="/backups" element={<Backups />} />
                  <Route path="/alerts" element={<AlertsCenter />} />
                  <Route path="/tasks" element={<Tasks />} />
                  <Route path="/ai" element={<AIServices />} />
                  <Route path="/ai-settings" element={<AISettings />} />
                  <Route path="/users" element={<Users />} />
                  <Route path="/export" element={<DataExport />} />
                  <Route path="/audit" element={<AuditLog />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="*" element={<Navigate to="/dashboard" />} />
                </Routes>
              </AppLayout>
            ) : <Navigate to="/login" />
          } />
        </Routes>
      </HashRouter>
    </ConfigProvider>
  )
}
