// 类名合并工具函数 (类似 clsx + tailwind-merge)
export function cn(...classes) {
    return classes.filter(Boolean).join(' ')
}
