import axios from 'axios';

// 从环境变量获取 API 地址，如果没有定义则默认使用 localhost
// 在生产环境中，应该在 .env 文件中设置 VITE_API_URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
export { API_BASE_URL };
