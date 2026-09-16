export function getToken(): string {
  return new URLSearchParams(window.location.search).get('t') || '';
}

export function hasToken(): boolean {
  return getToken().length > 0;
}
