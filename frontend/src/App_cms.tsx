/**
 * RaoCMS - 企业网站后台管理系统
 * React 前端入口
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ArticleList from './pages/ArticleList';
import ArticleEditor from './pages/ArticleEditor';
import UserList from './pages/UserList';
import PortalUserList from './pages/PortalUserList';
import SupplierList from './pages/SupplierList';
import ProductList from './pages/ProductList';
import FinanceDashboard from './pages/FinanceDashboard';
import Settings from './pages/Settings';

// 主题配置
const theme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
  },
};

// 简单权限检查
const requireAuth = (children) => {
  const token = localStorage.getItem('cms_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// 路由守卫 - 角色检查
const withRoleCheck = (children, allowedRoles) => {
  const token = localStorage.getItem('cms_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  const userStr = localStorage.getItem('cms_user');
  if (userStr) {
    const user = JSON.parse(userStr);
    if (!allowedRoles.includes(user.role)) {
      return <Navigate to="/" replace />;
    }
  }
  
  return children;
};

function App() {
  return (
    <ConfigProvider theme={theme}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={requireAuth(<Dashboard />)} />
          <Route path="/articles" element={requireAuth(<ArticleList />)} />
          <Route path="/articles/new" element={withRoleCheck(<ArticleEditor />, ['admin', 'customer_service'])} />
          <Route path="/articles/:id" element={withRoleCheck(<ArticleEditor />, ['admin', 'customer_service'])} />
          <Route path="/users" element={withRoleCheck(<UserList />, ['admin'])} />
          <Route path="/portal-users" element={withRoleCheck(<PortalUserList />, ['admin'])} />
          <Route path="/suppliers" element={withRoleCheck(<SupplierList />, ['admin', 'finance'])} />
          <Route path="/products" element={withRoleCheck(<ProductList />, ['admin', 'finance'])} />
          <Route path="/finance" element={withRoleCheck(<FinanceDashboard />, ['admin', 'finance'])} />
          <Route path="/settings" element={withRoleCheck(<Settings />, ['admin'])} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;