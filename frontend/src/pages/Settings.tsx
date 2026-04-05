import React from 'react'
import { Typography, Card, Empty } from 'antd'
const { Title } = Typography
export default function Settings() {
  return (
    <div>
      <Title level={4}>⚙️ 系统设置</Title>
      <Card>
        <Empty description="系统设置与用户管理（Phase 3 实现）" />
      </Card>
    </div>
  )
}
