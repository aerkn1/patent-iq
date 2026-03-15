import type { Variants } from "motion/react"

const EASE_OUT: [number, number, number, number] = [0.16, 1, 0.3, 1]

export const tabVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit:    { opacity: 0 },
}
export const tabTransition = { duration: 0.18, ease: EASE_OUT }

export const cardContainerVariants: Variants = {
  hidden:  {},
  visible: { transition: { staggerChildren: 0.06 } },
}
export const cardItemVariants: Variants = {
  hidden:  { opacity: 0, y: 6 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.28, ease: EASE_OUT } },
}
