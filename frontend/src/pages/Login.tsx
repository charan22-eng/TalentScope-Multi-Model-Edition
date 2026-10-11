import React, { useState } from 'react';
import { LogIn } from 'lucide-react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await axios.post('http://localhost:8000/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      localStorage.setItem('token', response.data.access_token);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh]">
      <div className="w-full max-w-md p-8 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-border-color">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-full bg-primary-color flex items-center justify-center text-white mb-4">
            <LogIn size={24} />
          </div>
          <h2 className="text-2xl font-serif font-bold text-text-primary">Sign in to TalentScope</h2>
          <p className="text-text-secondary text-sm mt-2">Secure access for HR and Management</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1" htmlFor="email">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              className="w-full p-2 border border-border-color rounded focus:outline-none focus:ring-2 focus:ring-primary-color dark:bg-slate-700 dark:border-slate-600 dark:text-white"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@test.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              className="w-full p-2 border border-border-color rounded focus:outline-none focus:ring-2 focus:ring-primary-color dark:bg-slate-700 dark:border-slate-600 dark:text-white"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="p-3 bg-danger-color bg-opacity-10 text-danger-color rounded border border-danger-color text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full bg-primary-color hover:bg-primary-hover text-white font-medium py-2 px-4 rounded transition-colors"
          >
            Sign In
          </button>
        </form>
        
        <div className="mt-6 text-center text-xs text-text-secondary">
          <p>Local Demo: Use <strong>admin@test.com</strong> / <strong>admin</strong></p>
        </div>
      </div>
    </div>
  );
}
