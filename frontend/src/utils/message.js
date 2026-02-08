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
        <button class="confirm-btn px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-blue-500 text-white hover:brightness-110 transition-all">
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
