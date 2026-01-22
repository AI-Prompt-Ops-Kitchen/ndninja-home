import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,  // Include cookies for session auth
})

export default api
