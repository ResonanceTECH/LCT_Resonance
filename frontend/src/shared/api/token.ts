const TOKEN_KEY = 'lct_access_token';

let memoryToken: string | null = null;

export const tokenStore = {
  get(): string | null {
    if (memoryToken) return memoryToken;
    memoryToken = sessionStorage.getItem(TOKEN_KEY);
    return memoryToken;
  },
  set(token: string) {
    memoryToken = token;
    sessionStorage.setItem(TOKEN_KEY, token);
  },
  clear() {
    memoryToken = null;
    sessionStorage.removeItem(TOKEN_KEY);
  },
};
