import request from './request'

export function getWebhooks(params) {
    return request({
        url: '/api/webhooks',
        method: 'get',
        params
    })
}

export function createWebhook(data) {
    return request({
        url: '/api/webhooks',
        method: 'post',
        data
    })
}

export function updateWebhook(id, data) {
    return request({
        url: `/api/webhooks/${id}`,
        method: 'put',
        data
    })
}

export function deleteWebhook(id) {
    return request({
        url: `/api/webhooks/${id}`,
        method: 'delete'
    })
}

export function getWebhookLogs(id, params) {
    return request({
        url: `/api/webhooks/${id}/logs`,
        method: 'get',
        params
    })
}


export function getSubscriptionsByCode(code) {
    return request({
        url: `/api/webhooks/subscriptions/by-code/${code}`,
        method: 'get'
    })
}

export function manualPush(packageId, params) {
    return request({
        url: `/api/webhooks/push/${packageId}`,
        method: 'post',
        params
    })
}

export function getDeliveries(packageId) {
    return request({
        url: `/api/webhooks/deliveries/${packageId}`,
        method: 'get'
    })
}

export function testWebhook(data) {
    return request({
        url: '/api/webhooks/test/connection',
        method: 'post',
        data
    })
}
