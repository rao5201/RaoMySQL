/**
 * RaoMySQL - Data Export Page
 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Select, Button, Input, Tag, Space, message, Row, Col, Statistic, Tooltip, Radio, InputNumber } from 'antd';
import { DownloadOutlined, FileExcelOutlined, FileTextOutlined, DatabaseOutlined, ReloadOutlined, TableOutlined } from '@ant-design/icons';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

const DataExport = () => {
  const [connections, setConnections] = useState<any[]>([]);
  const [tables, setTables] = useState<string[]>([]);
  const [tableCounts, setTableCounts] = useState<Record<string, number>>({});
  const [selectedConn, setSelectedConn] = useState<number | null>(null);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [exportFormat, setExportFormat] = useState<'csv' | 'json'>('csv');
  const [columns, setColumns] = useState('');
  const [whereClause, setWhereClause] = useState('');
  const [rowLimit, setRowLimit] = useState(10000);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);

  useEffect(() => { fetchConnections(); }, []);

  const fetchConnections = async () => {
    try {
      const res = await api.get('/connections');
      setConnections(res.data || []);
    } catch { message.error('Failed to load connections'); }
  };

  const fetchTables = async (connId: number) => {
    setFetching(true);
    try {
      const res = await api.get('/export/tables', { params: { connection_id: connId } });
      setTables(res.data.tables || []);
      fetchAllCounts(connId, res.data.tables || []);
    } catch { message.error('Failed to load tables'); }
    finally { setFetching(false); }
  };

  const fetchAllCounts = async (connId: number, tbls: string[]) => {
    const counts: Record<string, number> = {};
    for (const t of tbls.slice(0, 20)) {
      try {
        const res = await api.get('/export/count', { params: { connection_id: connId, table: t } });
        counts[t] = res.data.count;
      } catch {}
    }
    setTableCounts(counts);
  };

  const handleConnChange = (v: number) => {
    setSelectedConn(v);
    setSelectedTable('');
    setTables([]);
    setTableCounts({});
    if (v) fetchTables(v);
  };

  const handleExport = async () => {
    if (!selectedConn || !selectedTable) { message.warning('Select connection and table'); return; }
    setLoading(true);
    try {
      const endpoint = exportFormat === 'csv' ? '/export/csv' : '/export/json';
      const params: any = { connection_id: selectedConn, table: selectedTable, limit: rowLimit };
      if (columns.trim()) params.columns = columns.trim();
      if (whereClause.trim()) params.where = whereClause.trim();

      const res = await api.get(endpoint, { params, responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([res.data]));
      const ext = exportFormat === 'csv' ? 'csv' : 'json';
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedTable}_export.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
      message.success(`Exported ${selectedTable} as ${ext.toUpperCase()}`);
    } catch { message.error('Export failed'); }
    finally { setLoading(false); }
  };

  const tableColumns = [
    {
      title: 'Table', dataIndex: 'name', key: 'name',
      render: (name: string) => (
        <Button type="link" size="small" onClick={() => setSelectedTable(name)} icon={<TableOutlined />}>
          {name}
        </Button>
      )
    },
    {
      title: 'Rows', dataIndex: 'count', key: 'count', width: 120,
      render: (count: number) => count !== undefined ? (
        <Tag color={count > 100000 ? 'red' : count > 10000 ? 'orange' : 'green'}>
          {count.toLocaleString()}
        </Tag>
      ) : '-'
    }
  ];

  const totalRows = Object.values(tableCounts).reduce((a, b) => a + b, 0);

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Connections" value={connections.length} prefix={<DatabaseOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Tables" value={tables.length} prefix={<TableOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Total Rows" value={totalRows} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Selected" value={selectedTable || '-'} />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        {/* Export Config */}
        <Col span={8}>
          <Card title="Export Configuration" size="small">
            <div style={{ marginBottom: 12 }}>
              <label style={{ fontWeight: 600, display: 'block', marginBottom: 6 }}>Connection</label>
              <Select
                style={{ width: '100%' }}
                placeholder="Select database connection"
                onChange={handleConnChange}
                loading={fetching}
                value={selectedConn}
              >
                {connections.map(c => (
                  <Select.Option key={c.id} value={c.id}>{c.name} ({c.host})</Select.Option>
                ))}
              </Select>
            </div>

            <div style={{ marginBottom: 12 }}>
              <label style={{ fontWeight: 600, display: 'block', marginBottom: 6 }}>Target Table</label>
              <Select
                style={{ width: '100%' }}
                placeholder="Select or pick from list"
                onChange={setSelectedTable}
                value={selectedTable || undefined}
                showSearch
                notFoundContent={selectedConn ? (tables.length ? 'No match' : 'Loading...') : 'Select connection first'}
              >
                {tables.map(t => (
                  <Select.Option key={t} value={t}>
                    {t} {tableCounts[t] !== undefined ? `(${tableCounts[t].toLocaleString()} rows)` : ''}
                  </Select.Option>
                ))}
              </Select>
            </div>

            <div style={{ marginBottom: 12 }}>
              <label style={{ fontWeight: 600, display: 'block', marginBottom: 6 }}>Format</label>
              <Radio.Group value={exportFormat} onChange={e => setExportFormat(e.target.value)} buttonStyle="solid">
                <Radio.Button value="csv"><FileExcelOutlined /> CSV</Radio.Button>
                <Radio.Button value="json"><FileTextOutlined /> JSON</Radio.Button>
              </Radio.Group>
            </div>

            <div style={{ marginBottom: 12 }}>
              <label style={{ fontWeight: 600, display: 'block', marginBottom: 6 }}>
                Columns <Tooltip title="Comma separated, leave empty for *"><span style={{ color: '#999' }}>(optional)</span></Tooltip>
              </label>
              <Input placeholder="id, name, created_at" value={columns} onChange={e => setColumns(e.target.value)} />
            </div>

            <div style={{ marginBottom: 12 }}>
              <label style={{ fontWeight: 600, display: 'block', marginBottom: 6 }}>
                WHERE <Tooltip title="SQL WHERE clause without WHERE keyword"><span style={{ color: '#999' }}>(optional)</span></Tooltip>
              </label>
              <Input placeholder="status = 'active' AND created_at > '2024-01-01'" value={whereClause} onChange={e => setWhereClause(e.target.value)} />
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ fontWeight: 600, display: 'block', marginBottom: 6 }}>Row Limit</label>
              <InputNumber min={1} max={100000} value={rowLimit} onChange={v => setRowLimit(v || 10000)} style={{ width: '100%' }} />
            </div>

            <Button
              type="primary"
              icon={<DownloadOutlined />}
              loading={loading}
              onClick={handleExport}
              block
              disabled={!selectedConn || !selectedTable}
              size="large"
            >
              Export {selectedTable ? selectedTable : ''} as {exportFormat.toUpperCase()}
            </Button>
          </Card>
        </Col>

        {/* Table Browser */}
        <Col span={16}>
          <Card
            title={<><DatabaseOutlined /> Table Browser</>}
            size="small"
            extra={<Button icon={<ReloadOutlined />} size="small" onClick={() => selectedConn && fetchTables(selectedConn)}>Refresh</Button>}
          >
            {!selectedConn ? (
              <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>
                <DatabaseOutlined style={{ fontSize: 48, marginBottom: 16 }} /><br />
                Select a database connection to browse tables
              </div>
            ) : (
              <Table
                dataSource={tables.map(t => ({ key: t, name: t, count: tableCounts[t] }))}
                columns={tableColumns}
                pagination={{ pageSize: 15 }}
                size="small"
                scroll={{ y: 500 }}
                onRow={(row) => ({
                  onClick: () => setSelectedTable(row.name),
                  style: { cursor: 'pointer', background: row.name === selectedTable ? '#e6f7ff' : undefined }
                })}
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DataExport;
