const hapticFeedback = (type: 'light' | 'medium' | 'heavy' = 'light') => {
  const pattern = type === 'heavy' ? [15, 10, 15] : type === 'medium' ? [10] : 5;
  try {
    navigator.vibrate?.(pattern);
  } catch {
    // vibrate не поддерживается
  }
};

const showAlert = (message: string) => {
  alert(message);
};

const openLink = (url: string) => {
  window.location.href = url;
};

export function useTelegram() {
  return {
    hapticFeedback,
    showAlert,
    openLink,
  };
}
