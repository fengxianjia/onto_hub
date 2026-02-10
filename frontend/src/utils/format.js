/**
 * 统一时间格式化工具
 * 处理 UTC 时间字符串转换为本地时区显示
 */

/**
 * 格式化日期时间为本地字符串
 * @param {string} dateStr - 原始时间字符串 (通常为 UTC)
 * @returns {string} 格式化后的本地时间字符串
 */
export const formatDate = (dateStr) => {
    if (!dateStr) return '-'

    // 确保处理 UTC：如果字符串不带 Z 或时区偏移，增加 Z 提示 JS 引擎这是 UTC
    const utcDateStr = (dateStr.endsWith('Z') || dateStr.includes('+'))
        ? dateStr
        : `${dateStr}Z`

    const date = new Date(utcDateStr)

    // 检查无效日期
    if (isNaN(date.getTime())) return dateStr

    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    })
}

/**
 * 简单的日期格式化 (不含时间)
 */
export const formatDateOnly = (dateStr) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr.endsWith('Z') ? dateStr : `${dateStr}Z`)
    return date.toLocaleDateString('zh-CN')
}
