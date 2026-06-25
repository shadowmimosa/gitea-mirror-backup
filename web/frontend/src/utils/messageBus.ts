type MessageHandler = (msg: string, type: 'error' | 'warning' | 'info') => void

let handler: MessageHandler | null = null

export function setMessageHandler(fn: MessageHandler) {
  handler = fn
}

export function showGlobalMessage(msg: string, type: 'error' | 'warning' | 'info' = 'error') {
  if (handler) {
    handler(msg, type)
  }
}
