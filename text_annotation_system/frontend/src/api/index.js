import axios from 'axios'

const http = axios.create({ baseURL: '/api' })

export default {
  schemes: {
    list: () => http.get('/schemes'),
    get: (id) => http.get(`/schemes/${id}`),
    create: (data) => http.post('/schemes', data),
    update: (id, data) => http.put(`/schemes/${id}`, data),
    delete: (id) => http.delete(`/schemes/${id}`),
    exportScheme: (id) => http.post(`/schemes/${id}/export`, null, { responseType: 'blob' }),
    importScheme: (file) => {
      const form = new FormData()
      form.append('file', file)
      return http.post('/schemes/import', form)
    },
  },
  files: {
    upload: (file) => {
      const form = new FormData()
      form.append('file', file)
      return http.post('/files/upload', form)
    },
    preview: (id, n = 5) => http.get(`/files/${id}/preview`, { params: { n } }),
    columns: (id) => http.get(`/files/${id}/columns`),
  },
  tasks: {
    list: () => http.get('/tasks'),
    get: (id) => http.get(`/tasks/${id}`),
    create: (data) => http.post('/tasks', data),
    terminate: (id) => http.post(`/tasks/${id}/terminate`),
    delete: (id) => http.delete(`/tasks/${id}`),
    download: (id) => http.get(`/tasks/${id}/download`, { responseType: 'blob' }),
  },
  config: {
    status: () => http.get('/config/status'),
    set: (data) => http.post('/config/set', data),
    test: (data) => http.post('/config/test', data),
  },
  system: {
    shutdown: () => http.post('/system/shutdown'),
  },
}
