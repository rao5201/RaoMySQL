import React from 'react'
import { Typography, Card, Empty } from 'antd'
const { Title } = Typography
export default function AIAssistant() {
  return (
    <div>
      <Title level={4}>🤖 AI 助手</Title>
      <Card>
        <Empty description="AI 智能助手（Phase 4 实现）" />
      </Card>
    </div>
  )
}
