export const setToken = (token: string): void => {
  localStorage.setItem('df_token', token);
};

export const getToken = (): string | null => {
  return localStorage.getItem('df_token');
};

export const removeToken = (): void => {
  localStorage.removeItem('df_token');
};

export const isAuthenticated = (): boolean => {
  return !!getToken();
};
