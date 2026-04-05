import React from 'react'
import { Typography, Card, Empty } from 'antd'
const { Title } = Typography
export default function Backups() {
  return (
    <div>
      <Title level={4}>💾 备份中心</Title>
      <Card>
        <Empty description="备份管理功能（Phase 2 实现）" />
      </Card>
    </div>
  )
}
