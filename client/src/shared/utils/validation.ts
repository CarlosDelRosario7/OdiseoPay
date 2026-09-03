export function validateEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}

export function validatePhone(value: string) {
  return /^[0-9()\-\s+]{8,15}$/.test(value.trim())
}

export function validatePassword(value: string) {
  return value.trim().length >= 8
}

export function formatCurrency(value: number) {
  return new Intl.NumberFormat('es-DO', {
    style: 'currency',
    currency: 'DOP',
  }).format(value)
}
