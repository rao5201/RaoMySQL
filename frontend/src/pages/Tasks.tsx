import React from 'react'
import { Typography, Card, Empty } from 'antd'
const { Title } = Typography
export default function Tasks() {
  return (
    <div>
      <Title level={4}>⏰ 定时任务</Title>
      <Card>
        <Empty description="定时任务管理（Phase 3 实现）" />
      </Card>
    </div>
  )
}
