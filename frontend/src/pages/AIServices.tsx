/**
 * RaoMySQL - AI Services Hub
 * Four AI tools: NL2SQL, Slow Query Analysis, SQL Review, AI Chat + Alert Analysis
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Card, Row, Col, Input, Button, Select, Tag, Space, message, Tabs,
  Typography, Empty, Spin, Alert, Tooltip, Divider, Badge
} from 'antd';
import {
  RobotOutlined, ThunderboltOutlined, SafetyCertificateOutlined,
  BulbOutlined, AlertOutlined, SendOutlined, CopyOutlined,
  DatabaseOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined,
  ExperimentOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { TextArea } = Input;
const { Text, Title, Paragraph } = Typography;

const api = axios.create({ baseURL: '/api' });

/* ============================
   1. NL2SQL Tool
   ============================ */
const NL2SQLTool = () => {
  const [connections, setConnections] = useState<any[]>([]);
  const [connId, setConnId] = useState<number | null>(null);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    api.get('/connections').then(r => setConnections(r.data || [])).catch(() => {});
  }, []);

  const handleGenerate = async () => {
    if (!connId || !question.trim()) { message.warning('Select connection and enter question'); return; }
    setLoading(true);
    try {
      const r = await api.post('/ai/nl2sql', { question, connection_id: connId });
      setResult(r.data);
    } catch { message.error('NL2SQL failed'); }
    finally { setLoading(false); }
  };

  const copySql = () => {
    if (result?.sql) { navigator.clipboard.writeText(result.sql); message.success('Copied'); }
  };

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Select
            style={{ width: '100%' }}
            placeholder="Select Database Connection"
            onChange={setConnId}
            value={connId}
          >
            {connections.map(c => (
              <Select.Option key={c.id} value={c.id}>
                <Space><DatabaseOutlined />{c.name} <Text type="secondary">({c.host}:{c.port})</Text></Space>
              </Select.Option>
            ))}
          </Select>
        </Col>
        <Col span={16}>
          <Space.Compact style={{ width: '100%' }}>
            <Input
              placeholder="e.g. Show top 10 users registered in the last 7 days"
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onPressEnter={handleGenerate}
            />
            <Button type="primary" icon={<ThunderboltOutlined />} loading={loading} onClick={handleGenerate}>Generate</Button>
          </Space.Compact>
        </Col>
      </Row>

      {loading && <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" tip="AI is generating SQL..." /></div>}

      {result && !loading && (
        <Card size="small" title={<Space>Generated SQL <Tag color={result.confidence > 0.8 ? 'green' : 'orange'}>{(result.confidence * 100).toFixed(0)}% confidence</Tag></Space>}>
          <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: 16, borderRadius: 6, overflow: 'auto', fontSize: 14, lineHeight: 1.6 }}>
            {result.sql}
          </pre>
          <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between' }}>
            <Text type="secondary">{result.explanation}</Text>
            <Space>
              <Button icon={<CopyOutlined />} onClick={copySql}>Copy SQL</Button>
              <Button type="primary">Execute</Button>
            </Space>
          </div>
        </Card>
      )}

      {!result && !loading && (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Describe what data you want, AI will generate SQL" />
      )}
    </div>
  );
};

/* ============================
   2. Slow Query Analyzer
   ============================ */
const SlowQueryTool = () => {
  const [sql, setSql] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!sql.trim()) { message.warning('Enter SQL to analyze'); return; }
    setLoading(true);
    try {
      const r = await api.post('/ai/analyze-slow', { sql });
      setResult(r.data);
    } catch { message.error('Analysis failed'); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <TextArea
        value={sql}
        onChange={e => setSql(e.target.value)}
        placeholder="Paste your SQL query here for performance analysis..."
        rows={5}
        style={{ marginBottom: 12, fontFamily: 'monospace', fontSize: 14 }}
      />
      <Button type="primary" icon={<ThunderboltOutlined />} loading={loading} onClick={handleAnalyze} block>
        Analyze Performance
      </Button>

      {loading && <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" /></div>}

      {result && !loading && (
        <Card size="small" style={{ marginTop: 16 }} title={
          <Space>Analysis Result <Tag color={result.type === 'critical' ? 'red' : result.type === 'warning' ? 'orange' : 'green'}>{result.type}</Tag></Space>
        }>
          {result.suggestions?.length > 0 && (
            <div>
              <Text strong>Optimization Suggestions:</Text>
              <ul style={{ marginTop: 8 }}>
                {result.suggestions.map((s: string, i: number) => (
                  <li key={i}><Text>{typeof s === 'string' ? s : JSON.stringify(s)}</Text></li>
                ))}
              </ul>
            </div>
          )}
          <Row gutter={16} style={{ marginTop: 12 }}>
            <Col span={12}><Text type="secondary">Estimated Improvement: <Tag color="blue">{result.estimated_improvement}</Tag></Text></Col>
          </Row>
          {result.optimized_sql && (
            <div style={{ marginTop: 16 }}>
              <Text strong>Optimized SQL:</Text>
              <pre style={{ background: '#f6f8fa', padding: 12, borderRadius: 6, marginTop: 8, overflow: 'auto', fontSize: 13 }}>
                {result.optimized_sql}
              </pre>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

/* ============================
   3. SQL Security Review
   ============================ */
const SQLReviewTool = () => {
  const [sql, setSql] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleReview = async () => {
    if (!sql.trim()) { message.warning('Enter SQL to review'); return; }
    setLoading(true);
    try {
      const r = await api.post('/ai/review-sql', null, { params: { sql } });
      setResult(r.data);
    } catch { message.error('Review failed'); }
    finally { setLoading(false); }
  };

  const riskConfig: Record<string, { color: string; icon: React.ReactNode }> = {
    high: { color: '#ff4d4f', icon: <CloseCircleOutlined /> },
    medium: { color: '#faad14', icon: <WarningOutlined /> },
    low: { color: '#52c41a', icon: <CheckCircleOutlined /> },
  };

  return (
    <div>
      <TextArea
        value={sql}
        onChange={e => setSql(e.target.value)}
        placeholder="Paste SQL for security review..."
        rows={5}
        style={{ marginBottom: 12, fontFamily: 'monospace', fontSize: 14 }}
      />
      <Button type="primary" icon={<SafetyCertificateOutlined />} loading={loading} onClick={handleReview} block>
        Security Review
      </Button>

      {result && !loading && (
        <Card size="small" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={4}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 32, color: riskConfig[result.risk]?.color || '#999' }}>
                  {riskConfig[result.risk]?.icon || '?'}
                </div>
                <Tag color={result.risk === 'high' ? 'red' : result.risk === 'medium' ? 'orange' : 'green'} style={{ marginTop: 8, fontSize: 16, padding: '4px 16px' }}>
                  {result.risk?.toUpperCase()}
                </Tag>
              </div>
            </Col>
            <Col span={20}>
              <Text strong>Detected Rules:</Text>
              {result.rules?.length > 0 ? (
                <ul style={{ marginTop: 8, marginBottom: 0 }}>
                  {result.rules.map((r: string, i: number) => (
                    <li key={i}><Text>{r}</Text></li>
                  ))}
                </ul>
              ) : (
                <div style={{ marginTop: 8 }}><Tag color="green">No issues found</Tag></div>
              )}
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );
};

/* ============================
   4. AI Chat (with DB context)
   ============================ */
const AIChatTool = () => {
  const [connections, setConnections] = useState<any[]>([]);
  const [connId, setConnId] = useState<number | null>(null);
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    { role: 'assistant', content: 'Hi! I\'m RaoMySQL AI. Ask me anything about your database — I can help with queries, optimization, schema design, and more.\n\nSelect a connection for context-aware answers.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get('/connections').then(r => setConnections(r.data || [])).catch(() => {});
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const r = await api.post('/ai/chat', { message: input, connection_id: connId });
      setMessages(prev => [...prev, { role: 'assistant', content: r.data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'AI is currently unavailable. Check AI config in Settings.' }]);
    }
    finally { setLoading(false); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Select
        style={{ width: '100%', marginBottom: 12 }}
        placeholder="Select connection for DB context (optional)"
        onChange={setConnId}
        value={connId}
        allowClear
        size="small"
      >
        {connections.map(c => (
          <Select.Option key={c.id} value={c.id}>{c.name} ({c.database})</Select.Option>
        ))}
      </Select>

      <div style={{ flex: 1, overflow: 'auto', background: '#fafafa', borderRadius: 8, padding: 16, marginBottom: 12 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', marginBottom: 12, justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '75%', padding: '8px 14px', borderRadius: 12, background: m.role === 'user' ? '#1890ff' : '#fff',
              color: m.role === 'user' ? '#fff' : '#333', boxShadow: '0 1px 2px rgba(0,0,0,0.08)', whiteSpace: 'pre-wrap'
            }}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && <div style={{ textAlign: 'center' }}><Spin size="small" /></div>}
        <div ref={chatEndRef} />
      </div>

      <Space.Compact>
        <Input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask anything about your database..."
          onPressEnter={handleSend}
          disabled={loading}
        />
        <Button type="primary" icon={<SendOutlined />} loading={loading} onClick={handleSend}>Send</Button>
      </Space.Compact>
    </div>
  );
};

/* ============================
   5. Alert Analysis Tool
   ============================ */
const AlertAnalysisTool = () => {
  const [alertData, setAlertData] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');

  const handleAnalyze = async () => {
    if (!alertData.trim()) { message.warning('Paste alert data'); return; }
    setLoading(true);
    try {
      let parsed;
      try { parsed = JSON.parse(alertData); } catch { parsed = { raw: alertData }; }
      const r = await api.post('/ai/analyze-alert', parsed);
      setResult(r.data.analysis);
    } catch { message.error('Analysis failed'); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <TextArea
        value={alertData}
        onChange={e => setAlertData(e.target.value)}
        placeholder='Paste alert JSON or description, e.g.:\n{"level": "critical", "title": "High CPU", "value": 95}'
        rows={6}
        style={{ marginBottom: 12, fontFamily: 'monospace' }}
      />
      <Button type="primary" icon={<AlertOutlined />} loading={loading} onClick={handleAnalyze} block>
        AI Analyze Alert
      </Button>

      {loading && <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" /></div>}

      {result && !loading && (
        <Card size="small" style={{ marginTop: 16 }} title={<><BulbOutlined /> AI Recommendation</>}>
          <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{result}</Paragraph>
        </Card>
      )}
    </div>
  );
};

/* ============================
   Main AIServices Page
   ============================ */
const AIServices = () => {
  const [config, setConfig] = useState<any>(null);

  useEffect(() => {
    api.get('/ai/config').then(r => setConfig(r.data)).catch(() => {});
  }, []);

  const tabItems = [
    {
      key: 'nl2sql',
      label: <Space><ThunderboltOutlined /> NL2SQL</Space>,
      children: <NL2SQLTool />
    },
    {
      key: 'analyze',
      label: <Space><BulbOutlined /> Slow Query</Space>,
      children: <SlowQueryTool />
    },
    {
      key: 'review',
      label: <Space><SafetyCertificateOutlined /> SQL Review</Space>,
      children: <SQLReviewTool />
    },
    {
      key: 'chat',
      label: <Space><RobotOutlined /> AI Chat</Space>,
      children: <AIChatTool />
    },
    {
      key: 'alert',
      label: <Space><AlertOutlined /> Alert Analysis</Space>,
      children: <AlertAnalysisTool />
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>AI Services</Title>
          <Text type="secondary">Powered by {config?.provider || '?'} — {config?.model || '?'}</Text>
        </div>
        {config && (
          <Tag color={config.enabled ? 'green' : 'default'} icon={config.enabled ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
            {config.enabled ? 'Connected' : 'Not Configured'}
          </Tag>
        )}
      </div>

      {!config?.enabled && (
        <Alert
          message="AI Not Configured"
          description="Please go to AI Settings to configure your AI provider and API key."
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          action={<Button size="small" type="primary" onClick={() => window.location.hash = '#/ai-settings'}>Go to Settings</Button>}
        />
      )}

      <Card style={{ minHeight: 560 }}>
        <Tabs items={tabItems} defaultActiveKey="nl2sql" size="large" />
      </Card>
    </div>
  );
};

export default AIServices;
