import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import userReducer from './slices/userSlice';
import trafficReducer from './slices/trafficSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    users: userReducer,
    traffic: trafficReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
