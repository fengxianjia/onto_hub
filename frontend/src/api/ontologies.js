import request from './request'

export function getOntologies(params) {
    return request({
        url: '/api/ontologies',
        method: 'get',
        params
    })
}

export function getOntology(id) {
    return request({
        url: `/api/ontologies/${id}`,
        method: 'get'
    })
}

export function createOntology(data) {
    return request({
        url: '/api/ontologies',
        method: 'post',
        data,
        headers: { 'Content-Type': 'multipart/form-data' }
    })
}

export function addOntologyVersion(code, data) {
    return request({
        url: `/api/ontologies/${code}/versions`,
        method: 'post',
        data,
        headers: { 'Content-Type': 'multipart/form-data' }
    })
}

export function updateOntologySeries(code, data) {
    return request({
        url: `/api/ontologies/${code}`,
        method: 'patch',
        data
    })
}

export function deleteOntologyVersion(id) {
    return request({
        url: `/api/ontologies/${id}`,
        method: 'delete'
    })
}

export function deleteOntologySeries(code) {
    return request({
        url: `/api/ontologies/by-code/${code}`,
        method: 'delete'
    })
}

export function getOntologyVersions(code, params) {
    return request({
        url: `/api/ontologies/${code}/versions`,
        method: 'get',
        params
    })
}

export function getOntologyGraph(id) {
    return request({
        url: `/api/ontologies/${id}/graph`,
        method: 'get'
    })
}

export function compareOntologies(params) {
    return request({
        url: '/api/ontologies/compare',
        method: 'get',
        params
    })
}

export function activateOntology(id) {
    return request({
        url: `/api/ontologies/${id}/activate`,
        method: 'post'
    })
}

export function getFileContent(id, params) {
    return request({
        url: `/api/ontologies/${id}/files`,
        method: 'get',
        params
    })
}

export function reparseOntology(packageId, data) {
    return request({
        url: `/api/ontologies/packages/${packageId}/reparse`,
        method: 'post',
        data
    })
}

export function getOntologyEntities(id, params) {
    return request({
        url: `/api/ontologies/${id}/entities`,
        method: 'get',
        params
    })
}

export function getOntologyRelations(id, params) {
    return request({
        url: `/api/ontologies/${id}/relations`,
        method: 'get',
        params
    })
}
