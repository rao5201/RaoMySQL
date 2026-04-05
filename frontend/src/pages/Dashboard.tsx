import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Typography, Progress, List, Spin, message } from 'antd'
import { DatabaseOutlined, ClockCircleOutlined, AlertOutlined, CheckCircleOutlined, RobotOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import api from '../api'

const { Title } = Typography

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [connections, setConnections] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const [stats, setStats] = useState({ total_conns: 0, healthy: 0, unhealthy: 0, total_backups: 0 })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [connRes, alertRes] = await Promise.all([
        api.get('/api/connections'),
        api.get('/api/alerts').catch(() => ({ data: [] }))
      ])
      setConnections(connRes.data)
      setAlerts(alertRes.data?.slice(0, 5) || [])
      setStats({ total_conns: connRes.data.length, healthy: connRes.data.length, unhealthy: 0, total_backups: 0 })
    } catch {
      // 可能还没初始化
    } finally {
      setLoading(false)
    }
  }

  const gaugeOption = (value: number, color: string) => ({
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 100,
      splitNumber: 4,
      itemStyle: { color },
      progress: { show: true, width: 18 },
      pointer: { show: false },
      axisLine: { lineStyle: { width: 18, color: [[1, '#e8e8e8']] } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      title: { show: false },
      detail: { fontSize: 28, fontWeight: 700, formatter: '{value}%', color: '#333', offsetCenter: [0, '10%'] },
      data: [{ value }],
      center: ['50%', '70%'],
      radius: '90%'
    }]
  })

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><Spin size="large" /></div>

  return (
    <div>
      <Title level={4}>📊 仪表盘</Title>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}><Card><Statistic title="数据库连接" value={stats.total_conns} prefix={<DatabaseOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title="健康" value={stats.healthy} valueStyle={{ color: '#52c41a' }} prefix={<CheckCircleOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title="异常" value={stats.unhealthy} valueStyle={{ color: '#ff4d4f' }} prefix={<AlertOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title="AI 助手" value="在线" prefix={<RobotOutlined />} valueStyle={{ color: '#1890ff' }} /></Card></Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="🔗 数据库连接状态">
            <List
              dataSource={connections}
              renderItem={(item: any) => (
                <List.Item>
                  <List.Item.Meta title={item.name} description={`${item.host}:${item.port} / ${item.database_name}`} />
                  <Tag color="green">在线</Tag>
                </List.Item>
              )}
              locale={{ emptyText: '暂无连接，请先添加数据库连接' }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="🚨 最新告警">
            <List
              dataSource={alerts}
              renderItem={(item: any) => (
                <List.Item>
                  <Tag color={item.level === 'critical' ? 'red' : item.level === 'warning' ? 'orange' : 'blue'}>{item.level}</Tag>
                  <span>{item.title}</span>
                </List.Item>
              )}
              locale={{ emptyText: '🎉 暂无告警，一切正常' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={8}>
          <Card title="连接健康评分">
            <ReactECharts option={gaugeOption(100, '#52c41a')} style={{ height: 200 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="容量使用">
            <ReactECharts option={gaugeOption(45, '#1890ff')} style={{ height: 200 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="慢查询趋势">
            <ReactECharts option={{
              xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'] },
              yAxis: { type: 'value' },
              series: [{ data: [12, 8, 5, 3, 7, 2, 1], type: 'bar', itemStyle: { color: '#1890ff' } }]
            }} style={{ height: 200 }} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
