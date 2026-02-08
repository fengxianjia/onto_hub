// 动画配置 Composable
import { ref } from 'vue'

export const easeOut = [0.16, 1, 0.3, 1]

export const fadeInUp = {
    initial: { opacity: 0, y: 28 },
    enter: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 700,
            ease: easeOut
        }
    }
}

export const fadeIn = {
    initial: { opacity: 0 },
    enter: {
        opacity: 1,
        transition: {
            duration: 700,
            ease: easeOut
        }
    }
}

export const staggerContainer = {
    initial: {},
    enter: {
        transition: {
            staggerChildren: 100,
            delayChildren: 100
        }
    }
}

export function useAnimation() {
    return {
        fadeInUp,
        fadeIn,
        staggerContainer,
        easeOut
    }
}
