import axios from 'axios';

// Point to your backend gateway. Update BASE_URL when deploying.
const BASE_URL = 'http://10.0.2.2:80'; // Android emulator localhost

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  withCredentials: true,
});

export default api;
