/**
 * 从扁平的文件列表构建树形结构
 * @param {Array} files 文件对象列表，每个对象需包含 file_path 属性
 * @returns {Array} 树形结构数组
 */
export const buildFileTreeFromList = (files) => {
    if (!files || files.length === 0) return null

    const root = {}

    files.forEach(file => {
        const pathParts = file.file_path.split('/')
        let current = root

        pathParts.forEach((part, i) => {
            if (i === pathParts.length - 1) {
                // 这是文件
                if (!current._files) current._files = []
                current._files.push({
                    name: part,
                    path: file.file_path,
                    type: 'file',
                    size: file.file_size
                })
            } else {
                // 这是目录
                if (!current[part]) current[part] = {}
                current = current[part]
            }
        })
    })

    // 将字典转换为列表
    const dictToList = (node, path = '') => {
        const result = []

        Object.keys(node).forEach(key => {
            if (key === '_files') return

            const dirPath = path ? `${path}/${key}` : key
            result.push({
                name: key,
                path: dirPath,
                type: 'directory',
                children: dictToList(node[key], dirPath)
            })
        })

        if (node._files) {
            result.push(...node._files)
        }

        return result.sort((a, b) => {
            if (a.type !== b.type) return a.type === 'file' ? 1 : -1
            return a.name.localeCompare(b.name)
        })
    }

    return dictToList(root)
}

/**
 * 获取本体状态对应的 UI 变体名称
 * @param {string} status 状态字符串
 * @returns {string} Badge 的 variant 名称
 */
export const getStatusVariant = (status) => {
    const map = {
        'READY': 'success',
        'PENDING': 'warning',
        'PROCESSING': 'info',
        'ERROR': 'danger'
    }
    return map[status] || 'default'
}
