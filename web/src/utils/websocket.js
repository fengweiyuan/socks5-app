// WebSocket客户端工具
class WebSocketClient {
  constructor(url, options = {}) {
    this.url = url;
    this.options = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      ...options
    };
    
    this.ws = null;
    this.reconnectAttempts = 0;
    this.reconnectTimer = null;
    this.heartbeatTimer = null;
    this.isConnecting = false;
    this.isConnected = false;
    
    // 事件处理器
    this.eventHandlers = {
      open: [],
      close: [],
      message: [],
      error: [],
      reconnect: []
    };
    
    // 订阅的主题
    this.subscriptions = new Set();
    
    // 自动连接
    if (this.options.autoConnect !== false) {
      this.connect();
    }
  }
  
  // 连接WebSocket
  connect() {
    if (this.isConnecting || this.isConnected) {
      return;
    }
    
    this.isConnecting = true;
    
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = (event) => {
        this.isConnecting = false;
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        console.log('WebSocket连接已建立');
        
        // 重新订阅之前的主题
        this.resubscribe();
        
        // 启动心跳
        this.startHeartbeat();
        
        // 触发open事件
        this.triggerEvent('open', event);
      };
      
      this.ws.onclose = (event) => {
        this.isConnecting = false;
        this.isConnected = false;
        
        console.log('WebSocket连接已关闭:', event.code, event.reason);
        
        // 停止心跳
        this.stopHeartbeat();
        
        // 触发close事件
        this.triggerEvent('close', event);
        
        // 尝试重连
        this.scheduleReconnect();
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('解析WebSocket消息失败:', error);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        this.triggerEvent('error', error);
      };
      
    } catch (error) {
      console.error('创建WebSocket连接失败:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }
  
  // 断开连接
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnecting = false;
    this.isConnected = false;
  }
  
  // 发送消息
  send(type, data = {}) {
    if (!this.isConnected) {
      console.warn('WebSocket未连接，无法发送消息');
      return false;
    }
    
    try {
      const message = {
        type,
        data,
        timestamp: Date.now()
      };
      
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('发送WebSocket消息失败:', error);
      return false;
    }
  }
  
  // 订阅主题
  subscribe(topic) {
    if (this.subscriptions.has(topic)) {
      return;
    }
    
    this.subscriptions.add(topic);
    
    if (this.isConnected) {
      this.send('subscribe', { topic });
    }
  }
  
  // 取消订阅主题
  unsubscribe(topic) {
    if (!this.subscriptions.has(topic)) {
      return;
    }
    
    this.subscriptions.delete(topic);
    
    if (this.isConnected) {
      this.send('unsubscribe', { topic });
    }
  }
  
  // 重新订阅之前的主题
  resubscribe() {
    this.subscriptions.forEach(topic => {
      this.send('subscribe', { topic });
    });
  }
  
  // 处理接收到的消息
  handleMessage(data) {
    // 触发message事件
    this.triggerEvent('message', data);
    
    // 根据消息类型进行特殊处理
    switch (data.type) {
      case 'traffic_data':
        this.handleTrafficData(data.data);
        break;
      case 'proxy_health':
        this.handleProxyHealth(data.data);
        break;
      case 'system_performance':
        this.handleSystemPerformance(data.data);
        break;
      case 'heartbeat':
        this.handleHeartbeat(data.data);
        break;
      case 'pong':
        this.handlePong(data.data);
        break;
      default:
        console.log('收到未知类型的消息:', data);
    }
  }
  
  // 处理流量数据
  handleTrafficData(data) {
    // 这里可以添加流量数据的特殊处理逻辑
    console.log('收到流量数据:', data);
  }
  
  // 处理代理健康数据
  handleProxyHealth(data) {
    // 这里可以添加代理健康数据的特殊处理逻辑
    console.log('收到代理健康数据:', data);
  }
  
  // 处理系统性能数据
  handleSystemPerformance(data) {
    // 这里可以添加系统性能数据的特殊处理逻辑
    console.log('收到系统性能数据:', data);
  }
  
  // 处理心跳
  handleHeartbeat(data) {
    // 响应心跳
    this.send('ping');
  }
  
  // 处理pong响应
  handlePong(data) {
    // 心跳响应处理
    console.log('收到心跳响应:', data);
  }
  
  // 启动心跳
  startHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }
    
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send('ping');
      }
    }, this.options.heartbeatInterval);
  }
  
  // 停止心跳
  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
  
  // 安排重连
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error('达到最大重连次数，停止重连');
      return;
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    
    this.reconnectAttempts++;
    const delay = this.options.reconnectInterval * this.reconnectAttempts;
    
    console.log(`${delay}ms后尝试重连 (第${this.reconnectAttempts}次)`);
    
    this.reconnectTimer = setTimeout(() => {
      this.triggerEvent('reconnect', { attempt: this.reconnectAttempts });
      this.connect();
    }, delay);
  }
  
  // 添加事件监听器
  on(event, handler) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].push(handler);
    }
  }
  
  // 移除事件监听器
  off(event, handler) {
    if (this.eventHandlers[event]) {
      const index = this.eventHandlers[event].indexOf(handler);
      if (index > -1) {
        this.eventHandlers[event].splice(index, 1);
      }
    }
  }
  
  // 触发事件
  triggerEvent(event, data) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`事件处理器错误 (${event}):`, error);
        }
      });
    }
  }
  
  // 获取连接状态
  getConnectionState() {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      subscriptions: Array.from(this.subscriptions)
    };
  }
  
  // 获取统计信息
  getStats() {
    return {
      url: this.url,
      connectionState: this.getConnectionState(),
      options: this.options
    };
  }
}

// 创建默认的WebSocket客户端实例
const createWebSocketClient = (url, options) => {
  return new WebSocketClient(url, options);
};

// 导出
export default WebSocketClient;
export { createWebSocketClient };
