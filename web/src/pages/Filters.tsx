import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, Switch, Space, Tag, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import api from '../api/auth';

const { Option } = Select;

interface FilterRule {
  id: number;
  pattern: string;
  type: string;
  description: string;
  enabled: boolean;
  createdAt: string;
}

const Filters: React.FC = () => {
  const [filters, setFilters] = useState<FilterRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingFilter, setEditingFilter] = useState<FilterRule | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchFilters();
  }, []);

  const fetchFilters = async () => {
    setLoading(true);
    try {
      const response = await api.get('/filters');
      setFilters(response.filters || []);
    } catch (error) {
      console.error('获取过滤规则失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingFilter(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: FilterRule) => {
    setEditingFilter(record);
    form.setFieldsValue({
      pattern: record.pattern,
      type: record.type,
      description: record.description,
      enabled: record.enabled,
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/filters/${id}`);
      fetchFilters();
    } catch (error) {
      console.error('删除过滤规则失败:', error);
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingFilter) {
        await api.put(`/filters/${editingFilter.id}`, values);
      } else {
        await api.post('/filters', values);
      }
      setModalVisible(false);
      form.resetFields();
      fetchFilters();
    } catch (error) {
      console.error('保存过滤规则失败:', error);
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
      title: '匹配模式',
      dataIndex: 'pattern',
      key: 'pattern',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'block' ? 'red' : 'green'}>
          {type === 'block' ? '阻止' : '允许'}
        </Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'green' : 'red'}>
          {enabled ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: FilterRule) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个过滤规则吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          添加过滤规则
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={filters}
        rowKey="id"
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
      />

      <Modal
        title={editingFilter ? '编辑过滤规则' : '添加过滤规则'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="pattern"
            label="匹配模式"
            rules={[
              { required: true, message: '请输入匹配模式' },
              { min: 2, message: '匹配模式至少2个字符' },
            ]}
          >
            <Input placeholder="例如: *.google.com 或 192.168.1.*" />
          </Form.Item>

          <Form.Item
            name="type"
            label="规则类型"
            rules={[{ required: true, message: '请选择规则类型' }]}
          >
            <Select>
              <Option value="block">阻止访问</Option>
              <Option value="allow">允许访问</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
            rules={[{ max: 200, message: '描述不能超过200个字符' }]}
          >
            <Input.TextArea rows={3} placeholder="可选：添加规则描述" />
          </Form.Item>

          <Form.Item
            name="enabled"
            label="启用状态"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingFilter ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Filters;
