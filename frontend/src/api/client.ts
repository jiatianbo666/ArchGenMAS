/** Axios 实例封装 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const client = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2分钟超时（LLM调用可能较慢）
  headers: { 'Content-Type': 'application/json' },
})

// 响应拦截器
client.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '网络请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default client
