import React, { useEffect, useState } from 'react';
import { Table, Card, DatePicker, Select, Input, Button, Space, Tag } from 'antd';
import { SearchOutlined, DownloadOutlined, DeleteOutlined } from '@ant-design/icons';
import api from '../api/auth';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface LogEntry {
  id: number;
  username: string;
  clientIP: string;
  targetURL: string;
  method: string;
  status: string;
  userAgent: string;
  timestamp: string;
}

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    dateRange: null,
    status: '',
    username: '',
  });

  useEffect(() => {
    fetchLogs();
  }, [filters]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filters.dateRange) {
        params.startDate = filters.dateRange[0].format('YYYY-MM-DD');
        params.endDate = filters.dateRange[1].format('YYYY-MM-DD');
      }
      if (filters.status) params.status = filters.status;
      if (filters.username) params.username = filters.username;

      const response = await api.get('/logs', { params });
      setLogs(response.logs || []);
    } catch (error) {
      console.error('获取日志失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await api.get('/logs/export', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `logs_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('导出日志失败:', error);
    }
  };

  const handleClearLogs = async () => {
    try {
      await api.delete('/logs');
      fetchLogs();
    } catch (error) {
      console.error('清理日志失败:', error);
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '客户端IP',
      dataIndex: 'clientIP',
      key: 'clientIP',
    },
    {
      title: '目标URL',
      dataIndex: 'targetURL',
      key: 'targetURL',
      ellipsis: true,
    },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'success' ? 'green' : 'red'}>
          {status === 'success' ? '成功' : '失败'}
        </Tag>
      ),
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => new Date(timestamp).toLocaleString(),
      sorter: (a: LogEntry, b: LogEntry) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    },
  ];

  return (
    <div>
      <Card title="日志审计">
        <div style={{ marginBottom: 16 }}>
          <Space wrap>
            <RangePicker
              value={filters.dateRange}
              onChange={(dates) => setFilters({ ...filters, dateRange: dates })}
              placeholder={['开始日期', '结束日期']}
            />
            <Select
              placeholder="状态"
              value={filters.status}
              onChange={(value) => setFilters({ ...filters, status: value })}
              style={{ width: 120 }}
              allowClear
            >
              <Option value="success">成功</Option>
              <Option value="failed">失败</Option>
            </Select>
            <Input
              placeholder="用户名"
              value={filters.username}
              onChange={(e) => setFilters({ ...filters, username: e.target.value })}
              style={{ width: 150 }}
              prefix={<SearchOutlined />}
            />
            <Button type="primary" onClick={fetchLogs}>
              搜索
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              导出
            </Button>
            <Button danger icon={<DeleteOutlined />} onClick={handleClearLogs}>
              清理日志
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
            pageSize: 20,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );
};

export default Logs;
