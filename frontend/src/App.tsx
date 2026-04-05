import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, Layout, Menu, theme, Badge, Dropdown, Avatar, Space } from 'antd'
import { DatabaseOutlined, TableOutlined, RobotOutlined, AlertOutlined, SettingOutlined, UserOutlined, LogoutOutlined, DashboardOutlined } from '@ant-design/icons'
import zhCN from 'antd/locale/zh_CN'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Connections from './pages/Connections'
import SqlEditor from './pages/SqlEditor'
import Backups from './pages/Backups'
import Tasks from './pages/Tasks'
import AIAssistant from './pages/AIAssistant'
import Settings from './pages/Settings'

const { Header, Sider, Content } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/connections', icon: <DatabaseOutlined />, label: '数据库连接' },
  { key: '/sql', icon: <TableOutlined />, label: 'SQL 编辑器' },
  { key: '/backups', icon: <AlertOutlined />, label: '备份中心' },
  { key: '/tasks', icon: <SettingOutlined />, label: '定时任务' },
  { key: '/ai', icon: <RobotOutlined />, label: 'AI 助手' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
]

function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)

  const userMenu = {
    items: [
      { key: 'profile', icon: <UserOutlined />, label: '个人资料' },
      { type: 'divider' as const },
      { key: 'logout', icon: <LogoutOutlined />, label: '退出登录' },
    ]
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme="dark">
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 16, fontWeight: 700 }}>
          {collapsed ? 'RM' : '🔒 RaoMySQL'}
        </div>
        <Menu theme="dark" mode="inline" defaultSelectedKeys={['/dashboard']} items={menuItems} onClick={({ key }) => window.location.hash = key} />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', borderBottom: '1px solid #f0f0f0' }}>
          <Dropdown menu={userMenu} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
              <span>Admin</span>
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

function App() {
  const [token] = useState(() => localStorage.getItem('raomysql_token') || '')
  return (
    <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm, token: { colorPrimary: '#1890ff' } }} locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={token ? <Navigate to="/dashboard" /> : <Login />} />
          <Route path="/*" element={
            token ? (
              <AppLayout>
                <Routes>
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/connections" element={<Connections />} />
                  <Route path="/sql" element={<SqlEditor />} />
                  <Route path="/backups" element={<Backups />} />
                  <Route path="/tasks" element={<Tasks />} />
                  <Route path="/ai" element={<AIAssistant />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="*" element={<Navigate to="/dashboard" />} />
                </Routes>
              </AppLayout>
            ) : <Navigate to="/login" />
          } />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
