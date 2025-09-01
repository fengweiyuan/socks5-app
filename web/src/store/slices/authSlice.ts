import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { message } from 'antd';
import { authAPI } from '../../api/auth';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  status: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  token: localStorage.getItem('token'),
  user: null,
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { username: string; password: string }) => {
    const response = await authAPI.login(credentials);
    localStorage.setItem('token', response.token);
    return response;
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async () => {
    await authAPI.logout();
    localStorage.removeItem('token');
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.token = action.payload.token;
        state.user = action.payload.user;
        message.success('登录成功');
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '登录失败';
        message.error(state.error);
      })
      .addCase(logout.fulfilled, (state) => {
        state.token = null;
        state.user = null;
        message.success('已退出登录');
      });
  },
});

export const { clearError } = authSlice.actions;
export default authSlice.reducer;
