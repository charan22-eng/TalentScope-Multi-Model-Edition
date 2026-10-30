interface AuthResult {
  access_token: string;
  role?: string;
  token_type?: string;
}

let pendingAuthPromise: Promise<string> | null = null;

function isTokenExpired(token: string): boolean {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return true;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    const parsed = JSON.parse(jsonPayload) as { exp?: number };
    if (!parsed.exp) return false;
    return Date.now() >= (parsed.exp - 60) * 1000;
  } catch {
    return true;
  }
}

/**
 * Automatically ensures a valid admin token exists in localStorage.
 * Transparently logs in with the default admin account in the background
 * so that no user login screen or manual sign-in is required.
 */
export async function ensureAuthToken(forceRefresh = false): Promise<string> {
  if (!localStorage.getItem('user_role')) {
    localStorage.setItem('user_role', 'admin');
  }
  if (!localStorage.getItem('user_email')) {
    localStorage.setItem('user_email', 'admin@test.com');
  }

  const existingToken = localStorage.getItem('token');
  if (existingToken && !forceRefresh && !isTokenExpired(existingToken)) {
    return existingToken;
  }

  if (pendingAuthPromise && !forceRefresh) {
    return pendingAuthPromise;
  }

  pendingAuthPromise = (async () => {
    try {
      const apiOrigin = import.meta.env.VITE_API_ORIGIN || 'http://localhost:8000';
      const cleanOrigin = apiOrigin.replace(/\/$/, '');
      const body = new URLSearchParams();
      body.append('username', 'admin@test.com');
      body.append('password', 'admin');

      const response = await fetch(`${cleanOrigin}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      });

      if (response.ok) {
        const data = (await response.json()) as AuthResult;
        if (data.access_token) {
          localStorage.setItem('token', data.access_token);
          localStorage.setItem('user_role', data.role || 'admin');
          localStorage.setItem('user_email', 'admin@test.com');
          return data.access_token;
        }
      }
    } catch {
      // Auto-auth fetch failed, will retry on subsequent request
    } finally {
      pendingAuthPromise = null;
    }
    return localStorage.getItem('token') || '';
  })();

  return pendingAuthPromise;
}
