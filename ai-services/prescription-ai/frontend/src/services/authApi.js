import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

/**
 * Register a new user
 * @param {string} name 
 * @param {string} email 
 * @param {string} password 
 * @returns {Promise<object>} The server response (access token)
 */
export const registerUser = async (name, email, password) => {
  const response = await client.post('/auth/register', { name, email, password });
  return response.data;
};

/**
 * Login an existing user
 * @param {string} email 
 * @param {string} password 
 * @returns {Promise<object>} The server response (access token)
 */
export const loginUser = async (email, password) => {
  const response = await client.post('/auth/login', { email, password });
  return response.data;
};
