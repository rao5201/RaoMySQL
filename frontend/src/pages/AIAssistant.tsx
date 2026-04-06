/**
 * RaoMySQL - AI 助手页面
 */

import React, { useState } from 'react';
import { Card, Input, Button, List, Avatar, Space, Tag, Divider, message } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, ThunderboltOutlined } from '@ant-design/icons';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

const AIAssistant = () => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '你好！我是 RaoMySQL AI 助手，可以帮你：\n\n1. 自然语言转 SQL - 描述你想要的数据，我来生成 SQL\n2. 慢查询分析 - 分析你的 SQL 并提供优化建议\n3. 数据库操作建议 - 回答数据库相关问题\n\n请输入你的问题：', suggestions: [] }
  ]);
  const [mode, setMode] = useState('chat'); // chat/nl2sql/analyze

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      let response;
      if (mode === 'nl2sql') {
        response = await api.post('/ai/nl2sql', { question: input });
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: `生成的 SQL:\n\`\`\`sql\n${response.data.sql}\n\`\`\`\n\n说明: ${response.data.explanation}\n\n置信度: ${(response.data.confidence * 100).toFixed(0)}%`,
          suggestions: [] 
        }]);
      } else if (mode === 'analyze') {
        response = await api.post('/ai/analyze-slow', { sql: input });
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: `分析结果:\n\n问题类型: ${response.data.analysis.type}\n\n优化建议:\n${response.data.analysis.suggestions.map((s, i) => `${i+1}. ${s}`).join('\n')}\n\n预计提升: ${response.data.analysis.estimated_improvement}\n\n优化后的 SQL:\n\`\`\`sql\n${response.data.optimized_sql}\n\`\`\``,
          suggestions: [] 
        }]);
      } else {
        response = await api.post('/ai/chat', { message: input });
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: response.data.response,
          suggestions: response.data.suggestions || [] 
        }]);
      }
    } catch (error) {
      message.error('AI 响应失败');
      setMessages(prev => [...prev, { role: 'assistant', content: '抱歉，我遇到了问题，请稍后重试。', suggestions: [] }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion);
  };

  const handleModeChange = (newMode) => {
    setMode(newMode);
    setMessages([{ role: 'assistant', content: getModeWelcome(newMode), suggestions: [] }]);
  };

  const getModeWelcome = (m) => {
    const msgs = {
      chat: '你好！我是 RaoMySQL AI 助手，有什么可以帮你？',
      nl2sql: '请描述你想要查询的数据，例如：帮我查询过去7天注册的用户',
      analyze: '请输入需要分析的 SQL 语句，我会给出优化建议'
    };
    return msgs[m] || '你好！';
  };

  return (
    <div style={{ padding: 24, height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      <h1>AI 助手</h1>
      
      {/* 模式选择 */}
      <Space style={{ marginBottom: 16 }}>
        <Tag color={mode === 'chat' ? 'blue' : 'default'} onClick={() => handleModeChange('chat')} style={{ cursor: 'pointer' }}>💬 对话</Tag>
        <Tag color={mode === 'nl2sql' ? 'blue' : 'default'} onClick={() => handleModeChange('nl2sql')} style={{ cursor: 'pointer' }}>🔄 自然语言转 SQL</Tag>
        <Tag color={mode === 'analyze' ? 'blue' : 'default'} onClick={() => handleModeChange('analyze')} style={{ cursor: 'pointer' }}>⚡ 慢查询分析</Tag>
      </Space>

      {/* 聊天区域 */}
      <Card style={{ flex: 1, overflow: 'auto', marginBottom: 16 }}>
        <div style={{ height: '100%', overflow: 'auto' }}>
          <List
            dataSource={messages}
            renderItem={(item) => (
              <List.Item style={{ display: 'block', border: 'none', padding: '12px 0' }}>
                <Space align="start">
                  <Avatar icon={item.role === 'user' ? <UserOutlined /> : <RobotOutlined />} 
                    style={{ backgroundColor: item.role === 'user' ? '#1890ff' : '#52c41a' }} />
                  <div style={{ whiteSpace: 'pre-wrap', maxWidth: '80%' }}>
                    {item.content}
                    {item.suggestions && item.suggestions.length > 0 && (
                      <div style={{ marginTop: 12 }}>
                        <Divider style={{ margin: '8px 0' }}>快捷问题</Divider>
                        <Space wrap>
                          {item.suggestions.map((s, i) => (
                            <Tag key={i} style={{ cursor: 'pointer' }} onClick={() => handleSuggestionClick(s)}>
                              {s}
                            </Tag>
                          ))}
                        </Space>
                      </div>
                    )}
                  </div>
                </Space>
              </List.Item>
            )}
          />
        </div>
      </Card>

      {/* 输入区域 */}
      <Card>
        <Space.Compact style={{ width: '100%' }}>
          <Input.TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={mode === 'nl2sql' ? '描述你想要查询的数据...' : mode === 'analyze' ? '输入需要分析的 SQL...' : '输入你的问题...'}
            onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); handleSend(); } }}
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{ flex: 1 }}
          />
          <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={loading}>
            发送
          </Button>
        </Space.Compact>
      </Card>
    </div>
  );
};

export default AIAssistant;