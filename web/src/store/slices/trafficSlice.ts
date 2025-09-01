import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { message } from 'antd';
import api from '../../api/auth';

interface TrafficStats {
  totalBytesSent: number;
  totalBytesRecv: number;
  activeConnections: number;
  totalUsers: number;
  onlineUsers: number;
}

interface RealtimeTraffic {
  timestamp: string;
  bytesSent: number;
  bytesRecv: number;
  connections: number;
}

interface TrafficState {
  stats: TrafficStats | null;
  realtimeData: RealtimeTraffic[];
  loading: boolean;
  error: string | null;
}

const initialState: TrafficState = {
  stats: null,
  realtimeData: [],
  loading: false,
  error: null,
};

export const fetchTrafficStats = createAsyncThunk(
  'traffic/fetchStats',
  async () => {
    const response = await api.get('/traffic');
    return response.stats;
  }
);

export const fetchRealtimeTraffic = createAsyncThunk(
  'traffic/fetchRealtime',
  async () => {
    const response = await api.get('/traffic/realtime');
    return response.realtime_traffic;
  }
);

export const setBandwidthLimit = createAsyncThunk(
  'traffic/setBandwidthLimit',
  async ({ userId, limit, period }: { userId: number; limit: number; period?: string }) => {
    await api.post('/traffic/limit', { user_id: userId, limit, period });
    message.success('带宽限制设置成功');
  }
);

const trafficSlice = createSlice({
  name: 'traffic',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTrafficStats.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTrafficStats.fulfilled, (state, action) => {
        state.loading = false;
        state.stats = action.payload;
      })
      .addCase(fetchTrafficStats.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '获取流量统计失败';
        message.error(state.error);
      })
      .addCase(fetchRealtimeTraffic.fulfilled, (state, action) => {
        state.realtimeData = action.payload;
      })
      .addCase(fetchRealtimeTraffic.rejected, (state, action) => {
        state.error = action.error.message || '获取实时流量数据失败';
        message.error(state.error);
      });
  },
});

export const { clearError } = trafficSlice.actions;
export default trafficSlice.reducer;
