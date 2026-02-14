import axios from 'axios'
import { showMessage, message } from '../utils/message.js'

// Create axios instance
const service = axios.create({
    baseURL: '/onto_hub', // Base URL for the application
    timeout: 60000 // Request timeout
})

// Request interceptor
service.interceptors.request.use(
    config => {
        // You can add token here if needed in the future
        // const token = getToken()
        // if (token) {
        //   config.headers['Authorization'] = 'Bearer ' + token
        // }
        return config
    },
    error => {
        console.error('Request error:', error)
        return Promise.reject(error)
    }
)

// Response interceptor
service.interceptors.response.use(
    response => {
        // Return the response directly to access headers if needed, 
        // or return response.data if you want to unwrap it here.
        // For now, let's keep it consistent with existing usage which expects res.data
        return response
    },
    error => {
        console.error('Response error:', error)
        // Unified error handling
        const errorMessage = message.getErrorMessage(error, '请求失败')
        // Optionally show message here or let component handle it
        // showMessage(errorMessage, 'error') 
        return Promise.reject(error)
    }
)

export default service
