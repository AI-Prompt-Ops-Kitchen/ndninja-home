import axios from 'axios';
import type {
  Standard,
  StandardDetail,
  StandardCombination,
  SOP,
  SOPDetail,
  AssemblyRequest,
  AssembledSOP,
  Token,
  User,
} from '../types';

const http = axios.create({ baseURL: '/api' });

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('roys_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

const api = {
  // Standards
  listStandards: () => http.get<Standard[]>('/standards').then((r) => r.data),
  getStandard: (id: string) => http.get<StandardDetail>(`/standards/${id}`).then((r) => r.data),
  listCombinations: () => http.get<StandardCombination[]>('/standards/combinations').then((r) => r.data),

  // SOPs
  listSOPs: () => http.get<SOP[]>('/sops').then((r) => r.data),
  getSOP: (id: string) => http.get<SOPDetail>(`/sops/${id}`).then((r) => r.data),

  // Assembly
  generate: (req: AssemblyRequest) => http.post<AssembledSOP>('/generate', req).then((r) => r.data),
  generateDocx: (req: AssemblyRequest) =>
    http.post('/generate/docx', req, { responseType: 'blob' }).then((r) => r.data as Blob),

  // Auth
  register: (email: string, password: string, fullName?: string, company?: string) =>
    http.post<User>('/auth/register', { email, password, full_name: fullName, company }).then((r) => r.data),
  login: (email: string, password: string) =>
    http.post<Token>('/auth/login', { email, password }).then((r) => r.data),
  me: () => http.get<User>('/auth/me').then((r) => r.data),

  // Admin
  adminStats: () => http.get<Record<string, number>>('/admin/stats').then((r) => r.data),

  // Health
  health: () => http.get<{ status: string }>('/health').then((r) => r.data),
};

export default api;
