import request from './request'

export function getTemplates(params) {
    return request({
        // Initial backend might have used trailing slash, ensuring compatibility
        url: '/api/templates/',
        method: 'get',
        params
    })
}

export function createTemplate(data) {
    return request({
        url: '/api/templates/',
        method: 'post',
        data
    })
}

export function updateTemplate(id, data) {
    return request({
        url: `/api/templates/${id}`,
        method: 'put',
        data
    })
}

export function deleteTemplate(id) {
    return request({
        url: `/api/templates/${id}`,
        method: 'delete'
    })
}
