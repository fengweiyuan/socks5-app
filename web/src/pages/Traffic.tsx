import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Select, DatePicker } from 'antd';
import { CloudOutlined, DownloadOutlined, UploadOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { fetchTrafficStats, fetchRealtimeTraffic } from '../store/slices/trafficSlice';

const { RangePicker } = DatePicker;

const Traffic: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { stats, realtimeData, loading } = useSelector((state: RootState) => state.traffic);
  const [timeRange, setTimeRange] = useState('1h');

  useEffect(() => {
    dispatch(fetchTrafficStats());
    dispatch(fetchRealtimeTraffic());
    
    const interval = setInterval(() => {
      dispatch(fetchTrafficStats());
      dispatch(fetchRealtimeTraffic());
    }, 30000); // 30秒更新一次

    return () => clearInterval(interval);
  }, [dispatch]);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getTrafficChartOption = () => {
    const chartData = realtimeData.map(item => ({
      time: new Date(item.timestamp).getTime(),
      sent: item.bytesSent / (1024 * 1024), // 转换为MB
      recv: item.bytesRecv / (1024 * 1024), // 转换为MB
    }));

    return {
      title: {
        text: '实时流量监控',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        formatter: function (params: any) {
          const time = new Date(params[0].value[0]).toLocaleString();
          let result = `${time}<br/>`;
          params.forEach((param: any) => {
            result += `${param.marker}${param.seriesName}: ${param.value[1].toFixed(2)} MB<br/>`;
          });
          return result;
        },
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
          data: chartData.map(item => [item.time, item.sent]),
          itemStyle: { color: '#1890ff' },
        },
        {
          name: '接收流量',
          type: 'line',
          smooth: true,
          data: chartData.map(item => [item.time, item.recv]),
          itemStyle: { color: '#52c41a' },
        },
      ],
    };
  };

  const getBandwidthChartOption = () => {
    // 这里可以添加带宽使用率图表
    return {
      title: {
        text: '带宽使用率',
        left: 'center',
      },
      tooltip: {
        trigger: 'item',
      },
      series: [
        {
          type: 'pie',
          radius: '50%',
          data: [
            { value: stats?.totalBytesSent || 0, name: '发送流量' },
            { value: stats?.totalBytesRecv || 0, name: '接收流量' },
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    };
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总发送流量"
              value={formatBytes(stats?.totalBytesSent || 0)}
              prefix={<UploadOutlined />}
              valueStyle={{ color: '#1890ff' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总接收流量"
              value={formatBytes(stats?.totalBytesRecv || 0)}
              prefix={<DownloadOutlined />}
              valueStyle={{ color: '#52c41a' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总流量"
              value={formatBytes((stats?.totalBytesSent || 0) + (stats?.totalBytesRecv || 0))}
              prefix={<CloudOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃连接"
              value={stats?.activeConnections || 0}
              valueStyle={{ color: '#faad14' }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={16}>
          <Card title="实时流量监控">
            <div style={{ marginBottom: 16 }}>
              <Select
                value={timeRange}
                onChange={setTimeRange}
                style={{ width: 120 }}
              >
                <Select.Option value="1h">最近1小时</Select.Option>
                <Select.Option value="6h">最近6小时</Select.Option>
                <Select.Option value="24h">最近24小时</Select.Option>
              </Select>
            </div>
            <ReactECharts
              option={getTrafficChartOption()}
              style={{ height: 400 }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="流量分布">
            <ReactECharts
              option={getBandwidthChartOption()}
              style={{ height: 400 }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Traffic;
