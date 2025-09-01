import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, Tag } from 'antd';
import { UserOutlined, CloudOutlined, EyeOutlined, ClockCircleOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import api from '../api/auth';

interface SystemStats {
  totalBytesSent: number;
  totalBytesRecv: number;
  activeConnections: number;
  totalUsers: number;
  onlineUsers: number;
}

interface OnlineUser {
  id: number;
  username: string;
  clientIP: string;
  startTime: string;
  bytesSent: number;
  bytesRecv: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<SystemStats>({
    totalBytesSent: 0,
    totalBytesRecv: 0,
    activeConnections: 0,
    totalUsers: 0,
    onlineUsers: 0,
  });
  const [onlineUsers, setOnlineUsers] = useState<OnlineUser[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // 30秒更新一次
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, onlineRes] = await Promise.all([
        api.get('/traffic'),
        api.get('/online'),
      ]);
      setStats(statsRes.stats);
      setOnlineUsers(onlineRes.online_users || []);
    } catch (error) {
      console.error('获取仪表盘数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const trafficChartOption = {
    title: {
      text: '实时流量监控',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: ['发送流量', '接收流量'],
      top: 30,
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      name: '流量 (MB)',
    },
    series: [
      {
        name: '发送流量',
        type: 'line',
        smooth: true,
        data: [], // 这里需要从API获取实时数据
      },
      {
        name: '接收流量',
        type: 'line',
        smooth: true,
        data: [], // 这里需要从API获取实时数据
      },
    ],
  };

  const onlineUsersColumns = [
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
      title: '连接时间',
      dataIndex: 'startTime',
      key: 'startTime',
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: '发送流量',
      dataIndex: 'bytesSent',
      key: 'bytesSent',
      render: (bytes: number) => formatBytes(bytes),
    },
    {
      title: '接收流量',
      dataIndex: 'bytesRecv',
      key: 'bytesRecv',
      render: (bytes: number) => formatBytes(bytes),
    },
    {
      title: '状态',
      key: 'status',
      render: () => <Tag color="green">在线</Tag>,
    },
  ];

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总用户数"
              value={stats.totalUsers}
              prefix={<UserOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="在线用户"
              value={stats.onlineUsers}
              prefix={<EyeOutlined />}
              valueStyle={{ color: '#3f8600' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃连接"
              value={stats.activeConnections}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总流量"
              value={formatBytes(stats.totalBytesSent + stats.totalBytesRecv)}
              prefix={<CloudOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="流量统计" className="stats-card">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="发送流量"
                  value={formatBytes(stats.totalBytesSent)}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="接收流量"
                  value={formatBytes(stats.totalBytesRecv)}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="实时流量图表" className="stats-card">
            <ReactECharts option={trafficChartOption} style={{ height: 200 }} />
          </Card>
        </Col>
      </Row>

      <Card title="在线用户" style={{ marginTop: 16 }}>
        <Table
          columns={onlineUsersColumns}
          dataSource={onlineUsers}
          rowKey="id"
          loading={loading}
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
};

export default Dashboard;
