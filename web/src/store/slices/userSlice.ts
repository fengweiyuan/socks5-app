import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { message } from 'antd';
import api from '../../api/auth';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  status: string;
  bandwidthLimit: number;
  createdAt: string;
}

interface UserState {
  users: User[];
  loading: boolean;
  error: string | null;
}

const initialState: UserState = {
  users: [],
  loading: false,
  error: null,
};

export const fetchUsers = createAsyncThunk(
  'users/fetchUsers',
  async () => {
    const response = await api.get('/users');
    return response.users;
  }
);

export const createUser = createAsyncThunk(
  'users/createUser',
  async (userData: { username: string; password: string; email?: string; role?: string; bandwidthLimit?: number }) => {
    const response = await api.post('/users', userData);
    message.success('用户创建成功');
    return response.user;
  }
);

export const updateUser = createAsyncThunk(
  'users/updateUser',
  async ({ id, userData }: { id: number; userData: Partial<User> }) => {
    const response = await api.put(`/users/${id}`, userData);
    message.success('用户更新成功');
    return response.user;
  }
);

export const deleteUser = createAsyncThunk(
  'users/deleteUser',
  async (id: number) => {
    await api.delete(`/users/${id}`);
    message.success('用户删除成功');
    return id;
  }
);

const userSlice = createSlice({
  name: 'users',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = false;
        state.users = action.payload;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '获取用户列表失败';
        message.error(state.error);
      })
      .addCase(createUser.fulfilled, (state, action) => {
        state.users.push(action.payload);
      })
      .addCase(updateUser.fulfilled, (state, action) => {
        const index = state.users.findIndex(user => user.id === action.payload.id);
        if (index !== -1) {
          state.users[index] = action.payload;
        }
      })
      .addCase(deleteUser.fulfilled, (state, action) => {
        state.users = state.users.filter(user => user.id !== action.payload);
      });
  },
});

export const { clearError } = userSlice.actions;
export default userSlice.reducer;
