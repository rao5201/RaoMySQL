/**
 * RaoMySQL - AI Settings Page
 * Configure AI provider, model, API key, endpoint, and test connection
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Form, Input, Select, Button, Space, Tag, Alert, Divider,
  Typography, Row, Col, Switch, message, Spin, Tooltip, Result, Steps
} from 'antd';
import {
  SettingOutlined, CheckCircleOutlined, CloseCircleOutlined,
  ApiOutlined, ExperimentOutlined, KeyOutlined, CloudServerOutlined,
  ReloadOutlined, SaveOutlined, RobotOutlined, BulbOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Text, Title, Paragraph } = Typography;

const api = axios.create({ baseURL: '/api' });

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI', desc: 'GPT-4o, GPT-4, GPT-3.5' },
  { value: 'ollama', label: 'Ollama (Local)', desc: 'Llama 3, Qwen, Mistral — runs locally' },
];

const MODELS: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
  ollama: ['llama3', 'qwen2', 'mistral', 'codellama', 'deepseek-coder'],
};

const AISettings = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; msg: string } | null>(null);
  const [config, setConfig] = useState<any>(null);
  const [showKey, setShowKey] = useState(false);

  useEffect(() => { fetchConfig(); }, []);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const r = await api.get('/ai/config');
      setConfig(r.data);
      form.setFieldsValue({
        provider: r.data.provider || 'openai',
        model: r.data.model || 'gpt-4',
        endpoint: r.data.endpoint || '',
        api_key: '', // never expose key in UI
      });
    } catch {}
    finally { setLoading(false); }
  };

  const handleProviderChange = (provider: string) => {
    form.setFieldsValue({ model: MODELS[provider]?.[0] || '' });
    if (provider === 'ollama') {
      form.setFieldsValue({ endpoint: 'http://localhost:11434' });
    } else {
      form.setFieldsValue({ endpoint: '' });
    }
  };

  const handleSave = async (values: any) => {
    setSaving(true);
    try {
      await api.put('/ai/config', {
        provider: values.provider,
        model: values.model,
        api_key: values.api_key || undefined,
        endpoint: values.endpoint || undefined,
      });
      message.success('AI config saved (runtime only, set env vars for persistence)');
      fetchConfig();
    } catch (e: any) {
      message.error(e.response?.data?.detail || 'Save failed');
    }
    finally { setSaving(false); }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const values = form.getFieldsValue();
      if (values.provider === 'ollama' && !values.endpoint) {
        setTestResult({ ok: false, msg: 'Ollama requires an endpoint URL' });
        setTesting(false);
        return;
      }
      // Quick chat test
      const r = await api.post('/ai/chat', {
        message: 'Say "AI connection successful" in one sentence.',
        connection_id: null
      });
      if (r.data?.response) {
        setTestResult({ ok: true, msg: r.data.response.slice(0, 200) });
      } else {
        setTestResult({ ok: false, msg: 'No response from AI' });
      }
    } catch (e: any) {
      setTestResult({ ok: false, msg: e.response?.data?.detail || e.message || 'Connection failed' });
    }
    finally { setTesting(false); }
  };

  if (loading) return <div style={{ textAlign: 'center', padding: 60 }}><Spin size="large" /></div>;

  return (
    <div style={{ padding: 24, maxWidth: 800 }}>
      <Title level={4}><SettingOutlined /> AI Settings</Title>

      {/* Current Status */}
      {config && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Text type="secondary">Provider</Text><br />
              <Tag color="blue" style={{ marginTop: 4 }}>{config.provider?.toUpperCase()}</Tag>
            </Col>
            <Col span={6}>
              <Text type="secondary">Model</Text><br />
              <Text strong style={{ marginTop: 4, display: 'block' }}>{config.model || '-'}</Text>
            </Col>
            <Col span={6}>
              <Text type="secondary">Status</Text><br />
              <Tag icon={config.enabled ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                color={config.enabled ? 'green' : 'default'} style={{ marginTop: 4 }}>
                {config.enabled ? 'Connected' : 'Not Configured'}
              </Tag>
            </Col>
            <Col span={6}>
              <Text type="secondary">Endpoint</Text><br />
              <Text style={{ marginTop: 4, display: 'block', fontSize: 12 }}>
                {config.endpoint || 'Default'}
              </Text>
            </Col>
          </Row>
        </Card>
      )}

      {/* Setup Guide */}
      {!config?.enabled && (
        <Alert
          message="Quick Setup Guide"
          description={
            <Steps direction="vertical" size="small" current={-1} items={[
              { title: 'OpenAI', description: 'Set your API key from platform.openai.com' },
              { title: 'Ollama (Free/Local)', description: 'Install Ollama, run: ollama pull llama3, set endpoint to http://localhost:11434' },
              { title: 'Save & Test', description: 'Click Save then Test Connection below' },
            ]} />
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Config Form */}
      <Card title={<><ApiOutlined /> Provider Configuration</>}>
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Form.Item name="provider" label="AI Provider" rules={[{ required: true }]}>
            <Select onChange={handleProviderChange}>
              {PROVIDERS.map(p => (
                <Select.Option key={p.value} value={p.value}>
                  <Space>
                    {p.value === 'ollama' ? <CloudServerOutlined /> : <RobotOutlined />}
                    <span>{p.label}</span>
                    <Text type="secondary" style={{ fontSize: 12 }}>({p.desc})</Text>
                  </Space>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="model" label="Model" rules={[{ required: true }]}>
            <Select showSearch placeholder="Select or type model name">
              {(MODELS[Form.useWatch('provider', form) as string] || []).map(m => (
                <Select.Option key={m} value={m}>{m}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="api_key" label={
            <Space>API Key <Tooltip title="Only needed for OpenAI. Leave empty to keep current key."><Tag>Optional if unchanged</Tag></Tooltip></Space>
          }>
            <Input.Password
              placeholder={config?.enabled ? 'Leave empty to keep current key' : 'sk-...'}
              visibilityToggle={{ visible: showKey, onVisibleChange: setShowKey }}
            />
          </Form.Item>

          <Form.Item name="endpoint" label={
            <Space>Custom Endpoint <Tooltip title="Required for Ollama. Optional for OpenAI (uses default)"><Tag>Optional</Tag></Tooltip></Space>
          }>
            <Input placeholder={form.getFieldValue('provider') === 'ollama' ? 'http://localhost:11434' : 'https://api.openai.com/v1 (default)'} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>
                Save Config
              </Button>
              <Button icon={<ExperimentOutlined />} loading={testing} onClick={handleTest}>
                Test Connection
              </Button>
              <Button icon={<ReloadOutlined />} onClick={fetchConfig}>
                Refresh
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* Test Result */}
      {testResult && (
        <Card style={{ marginTop: 16 }}>
          <Result
            status={testResult.ok ? 'success' : 'error'}
            title={testResult.ok ? 'Connection Successful' : 'Connection Failed'}
            subTitle={testResult.msg}
          />
        </Card>
      )}

      {/* Usage Tips */}
      <Card title={<><BulbOutlined /> Usage Tips</>} size="small" style={{ marginTop: 16 }}>
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Text strong>NL2SQL</Text>
            <Paragraph type="secondary" style={{ margin: '4px 0 0' }}>
              Select a connection, describe your data need in plain language. AI reads your schema and generates optimized SQL.
            </Paragraph>
          </Col>
          <Col span={12}>
            <Text strong>Slow Query Analysis</Text>
            <Paragraph type="secondary" style={{ margin: '4px 0 0' }}>
              Paste any SQL query. AI identifies performance bottlenecks and suggests indexes or rewrites.
            </Paragraph>
          </Col>
          <Col span={12}>
            <Text strong>SQL Security Review</Text>
            <Paragraph type="secondary" style={{ margin: '4px 0 0' }}>
              Detects risky patterns: DELETE without WHERE, SELECT *, leading wildcards, and more.
            </Paragraph>
          </Col>
          <Col span={12}>
            <Text strong>AI Chat</Text>
            <Paragraph type="secondary" style={{ margin: '4px 0 0' }}>
              General Q&A with optional DB context. Select a connection for schema-aware answers.
            </Paragraph>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default AISettings;
