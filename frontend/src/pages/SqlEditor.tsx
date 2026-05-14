import React, { useState, useEffect, useRef } from 'react'
import { Layout, Select, Button, Table, Typography, Space, Tag, message, Tabs, Spin, Tree, Card, Modal, Input, Popconfirm } from 'antd'
import { PlayCircleOutlined, SaveOutlined, HistoryOutlined, ApiOutlined, DeleteOutlined, FolderOutlined } from '@ant-design/icons'
import { EditorView, basicSetup } from 'codemirror'
import { sql } from '@codemirror/lang-sql'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorState } from '@codemirror/state'
import api from '../api'

const { Sider, Content } = Layout
const { Title, Text } = Typography

export default function SqlEditor() {
  const [connections, setConnections] = useState<any[]>([])
  const [connId, setConnId] = useState<number | null>(null)
  const [schema, setSchema] = useState<any>(null)
  const [loadingSchema, setLoadingSchema] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<any[]>([])
  const [snippets, setSnippets] = useState<any[]>([])
  const [saveModalVisible, setSaveModalVisible] = useState(false)
  const [snippetName, setSnippetName] = useState('')
  const editorRef = useRef<HTMLDivElement>(null)
  const viewRef = useRef<EditorView | null>(null)
  const [sqlText, setSqlText] = useState('SELECT 1 as test;')

  useEffect(() => {
    api.get('/api/connections').then(r => { setConnections(r.data); if (r.data.length) setConnId(r.data[0].id) }).catch(() => {})
    api.get('/api/query/history?limit=20').then(r => setHistory(r.data)).catch(() => {})
    api.get('/api/query/snippets').then(r => setSnippets(r.data)).catch(() => {})
    // 初始化 CodeMirror
    if (editorRef.current && !viewRef.current) {
      const state = EditorState.create({ doc: sqlText, extensions: [basicSetup, sql(), oneDark] })
      viewRef.current = new EditorView({ state, parent: editorRef.current })
    }
  }, [])

  useEffect(() => {
    if (connId) {
      setLoadingSchema(true)
      api.get(`/api/connections/${connId}/schema`).then(r => setSchema(r.data)).catch(() => {}).finally(() => setLoadingSchema(false))
    }
  }, [connId])

  const handleRun = async () => {
    if (!connId) { message.warning('请先选择数据库连接'); return }
    const sql = viewRef.current?.state.doc.toString() || sqlText
    if (!sql.trim()) { message.warning('SQL 不能为空'); return }
    setLoading(true)
    try {
      const res = await api.post('/api/query', { connection_id: connId, sql })
      setResult(res.data)
      if (res.data.status === 'success') {
        message.success(`执行成功，耗时 ${res.data.duration_ms}ms`)
      } else {
        message.error(res.data.error || '执行失败')
      }
    } catch (e: any) {
      message.error(e.response?.data?.detail || '执行失败')
    } finally { setLoading(false) }
  }

  const handleSaveSnippet = async () => {
    const sql = viewRef.current?.state.doc.toString() || sqlText
    if (!sql.trim()) { message.warning('SQL 不能为空'); return }
    if (!snippetName.trim()) { message.warning('请输入片段名称'); return }
    try {
      await api.post('/api/query/snippets', { name: snippetName, sql_text: sql })
      message.success('片段已保存')
      setSaveModalVisible(false)
      setSnippetName('')
      api.get('/api/query/snippets').then(r => setSnippets(r.data)).catch(() => {})
    } catch (e: any) {
      message.error(e.response?.data?.detail || '保存失败')
    }
  }

  const handleLoadSnippet = (sqlText: string) => {
    if (viewRef.current) {
      viewRef.current.dispatch({ changes: { from: 0, to: viewRef.current.state.doc.length, insert: sqlText } })
    } else {
      setSqlText(sqlText)
    }
    message.success('已加载片段')
  }

  const handleDeleteSnippet = async (id: number, e: any) => {
    e.stopPropagation()
    try {
      await api.delete(`/api/query/snippets/${id}`)
      message.success('已删除')
      api.get('/api/query/snippets').then(r => setSnippets(r.data)).catch(() => {})
    } catch (e: any) {
      message.error(e.response?.data?.detail || '删除失败')
    }
  }

  const schemaTree = schema ? Object.entries(schema.tables || {}).map(([table, cols]: [any, any]) => ({
    title: table,
    key: table,
    icon: <ApiOutlined />,
    children: (cols as any[]).map((c: any) => ({ title: <Text type="secondary">{c.Field} <span style={{fontSize:11}}>({c.Type})</span></Text>, key: `${table}.${c.Field}` }))
  })) : []

  return (
    <div style={{ height: 'calc(100vh - 120px)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <Title level={4} style={{ margin: 0 }}>🛠️ SQL 编辑器</Title>
        <Space>
          <Select
            placeholder="📂 加载片段"
            style={{ width: 180 }}
            allowClear
            options={snippets.map(s => ({ label: s.name, value: s.id, sql_text: s.sql_text }))}
            onChange={(val, opt: any) => val && handleLoadSnippet(opt.sql_text)}
            suffixIcon={<FolderOutlined />}
          />
          <Button icon={<SaveOutlined />} onClick={() => setSaveModalVisible(true)}>保存片段</Button>
          <Select placeholder="选择连接" value={connId} onChange={setConnId} style={{ width: 200 }} options={connections.map(c => ({ label: c.name, value: c.id }))} />
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleRun} loading={loading}>执行 (Ctrl+Enter)</Button>
        </Space>
      </div>
      <Layout style={{ height: 'calc(100% - 48px)', border: '1px solid #d9d9d9', borderRadius: 8, overflow: 'hidden' }}>
        <Sider width={220} style={{ background: '#1e1e1e', padding: 8, overflow: 'auto' }}>
          <div style={{ color: '#aaa', fontSize: 12, marginBottom: 8 }}>📂 表结构 {loadingSchema && <Spin size="small" />}</div>
          {schemaTree.length > 0 ? <Tree treeData={schemaTree} defaultExpandAll size="small" /> : <Text type="secondary">选择连接后加载</Text>}
        </Sider>
        <Content style={{ display: 'flex', flexDirection: 'column' }}>
          <div ref={editorRef} className="sql-editor-wrap" style={{ flex: '0 0 200px', background: '#1e1e1e' }} />
          <div style={{ flex: 1, overflow: 'auto', padding: 12, background: '#fafafa' }}>
            {result && (
              <>
                <Space style={{ marginBottom: 8 }}>
                  <Tag color={result.status === 'success' ? 'green' : 'red'}>{result.type}</Tag>
                  <Text type="secondary">耗时: {result.duration_ms}ms</Text>
                  {result.row_count !== undefined && <Text type="secondary">共 {result.row_count} 行</Text>}
                  {result.rows_affected !== undefined && <Text type="secondary">影响 {result.rows_affected} 行</Text>}
                </Space>
                {result.status === 'success' && result.rows && (
                  <Table size="small" dataSource={result.rows} columns={result.columns.map((c: string) => ({ title: c, dataIndex: c, ellipsis: true }))} pagination={{ pageSize: 100 }} scroll={{ x: 'max-content' }} bordered />
                )}
                {result.status === 'error' && <div style={{ color: '#ff4d4f', padding: 12, background: '#fff2f0', borderRadius: 8 }}>{result.error}</div>}
              </>
            )}
          </div>
        </Content>
      </Layout>
      <Modal title="保存 SQL 片段" open={saveModalVisible} onOk={handleSaveSnippet} onCancel={() => setSaveModalVisible(false)}>
        <Input
          placeholder="片段名称（如：用户统计查询）"
          value={snippetName}
          onChange={e => setSnippetName(e.target.value)}
          onPressEnter={handleSaveSnippet}
        />
      </Modal>
    </div>
  )
}
