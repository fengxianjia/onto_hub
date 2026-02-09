// 消息提示工具
export const message = {
  success: (msg) => {
    showMessage(msg, 'success')
  },
  error: (msg) => {
    showMessage(msg, 'error')
  },
  warning: (msg) => {
    showMessage(msg, 'warning')
  },
  info: (msg) => {
    showMessage(msg, 'info')
  },
  // 提取并由业务码翻译错误信息
  getErrorMessage: (err, defaultMsg = '操作失败') => {
    if (!err) return defaultMsg

    // 1. 标准业务错误码映射 (优先)
    const codeMap = {
      'ONTOLOGY_ALREADY_EXISTS': '该本体编码已存在，请在列表操作列选择“更新版本”',
      'ONTOLOGY_NAME_ALREADY_EXISTS': '该本体名称已存在，请换一个名称',
      'ONTOLOGY_NOT_FOUND': '目标本体不存在，请刷新页面后重试',
      'TEMPLATE_NOT_FOUND': '所选解析模板不存在',
      'TEMPLATE_DUPLICATE': '该模板已存在',
      'TEMPLATE_NAME_DUPLICATE': '该模板名称已存在',
      'WEBHOOK_NOT_FOUND': '订阅配置不存在',
      'WEBHOOK_DUPLICATE': '该订阅地址已存在',
      'WEBHOOK_NAME_DUPLICATE': '该订阅名称已存在',
      'INVALID_FILE_FORMAT': '文件格式不支持，请上传标准的 ZIP 压缩包',
      'FILE_TOO_LARGE': '文件体积过大，请压缩后重新上传',
      'UNAUTHORIZED': '会话已过期，请重新登录',
      'FORBIDDEN': '权限不足，无法执行此操作',
      'RESOURCE_IN_USE': '该资源正在被其他模块使用，暂时无法删除',
      'VERSION_ACTIVE': '该版本当前处于激活状态，请先激活其他版本后再尝试删除',
      'INTERNAL_ERROR': '服务器遇到了点问题，请稍后重试或联系管理员'
    }

    // 优先读取后端定义的业务 code
    const businessCode = err.response?.data?.code
    if (businessCode && codeMap[businessCode]) {
      return codeMap[businessCode]
    }

    // 2. 兜底模糊匹配方案 (用于兼容非标准报错或旧接口)
    const fuzzyMap = {
      'already exists': '该资源已存在，请勿重复操作',
      'not found': '未找到相关资源',
      'Internal Server Error': '系统繁忙，请稍后再试'
    }

    const detail = err.response?.data?.detail
    if (detail) {
      if (typeof detail === 'string') {
        for (const [key, value] of Object.entries(fuzzyMap)) {
          if (detail.toLowerCase().includes(key.toLowerCase())) return value
        }
        return detail
      }

      if (Array.isArray(detail)) {
        // 美化 Pydantic 校验报错
        return '输入格式有误：' + detail.map(d => {
          const field = d.loc[d.loc.length - 1]
          return `${field}字段格式不正确`
        }).join('; ')
      }
    }

    const message = err.response?.data?.message || err.message || defaultMsg
    for (const [key, value] of Object.entries(fuzzyMap)) {
      if (message.toLowerCase().includes(key.toLowerCase())) return value
    }
    return message
  }
}

export function showMessage(msg, type) {
  const container = getOrCreateContainer()

  const messageEl = document.createElement('div')
  messageEl.className = `message-toast message-${type}`
  messageEl.textContent = msg

  container.appendChild(messageEl)

  // 淡入
  setTimeout(() => {
    messageEl.classList.add('show')
  }, 10)

  // 3秒后移除
  setTimeout(() => {
    messageEl.classList.remove('show')
    setTimeout(() => {
      container.removeChild(messageEl)
    }, 300)
  }, 3000)
}

function getOrCreateContainer() {
  let container = document.getElementById('message-container')
  if (!container) {
    container = document.createElement('div')
    container.id = 'message-container'
    container.className = 'fixed top-4 right-4 z-[9999] flex flex-col gap-2'
    document.body.appendChild(container)

    // 添加样式
    const style = document.createElement('style')
    style.textContent = `
      .message-toast {
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        font-size: 14px;
        font-weight: 500;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        min-width: 200px;
      }
      .message-toast.show {
        opacity: 1;
        transform: translateX(0);
      }
      .message-success {
        background: #10b981;
        color: white;
      }
      .message-error {
        background: #ef4444;
        color: white;
      }
      .message-warning {
        background: #f59e0b;
        color: white;
      }
      .message-info {
        background: #3b82f6;
        color: white;
      }
    `
    document.head.appendChild(style)
  }
  return container
}

// 确认对话框
export const confirm = (msg, title = '确认', options = {}) => {
  return new Promise((resolve, reject) => {
    const overlay = document.createElement('div')
    overlay.className = 'fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm'

    const dialog = document.createElement('div')
    dialog.className = 'bg-white rounded-2xl shadow-2xl p-6 max-w-md w-full mx-4'
    dialog.innerHTML = `
      <h3 class="text-lg font-semibold text-gray-900 mb-2">${title}</h3>
      <p class="text-gray-600 mb-6">${msg}</p>
      <div class="flex gap-3 justify-end">
        <button class="cancel-btn px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors">
          ${options.cancelButtonText || '取消'}
        </button>
        <button class="confirm-btn px-4 py-2 rounded-lg bg-gradient-to-r from-red-600 to-rose-500 text-white hover:brightness-110 transition-all shadow-md shadow-red-200">
          ${options.confirmButtonText || '确定'}
        </button>
      </div>
    `

    overlay.appendChild(dialog)
    document.body.appendChild(overlay)

    const cancelBtn = dialog.querySelector('.cancel-btn')
    const confirmBtn = dialog.querySelector('.confirm-btn')

    const cleanup = () => {
      overlay.classList.add('opacity-0')
      setTimeout(() => {
        document.body.removeChild(overlay)
      }, 200)
    }

    cancelBtn.onclick = () => {
      cleanup()
      reject('cancel')
    }

    confirmBtn.onclick = () => {
      cleanup()
      resolve()
    }

    overlay.onclick = (e) => {
      if (e.target === overlay) {
        cleanup()
        reject('cancel')
      }
    }
  })
}

// 导出别名
export const showConfirm = confirm
