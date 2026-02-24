import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      navigate('/');
    } catch {
      setError('Invalid email or password');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-16">
      <h2 className="text-2xl font-bold text-navy-900 text-center mb-6">Sign In</h2>
      <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded-xl border border-navy-200">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}
        <div>
          <label className="block text-sm font-medium text-navy-700 mb-1">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-2 border border-navy-200 rounded-lg"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-navy-700 mb-1">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2 border border-navy-200 rounded-lg"
            required
          />
        </div>
        <button
          type="submit"
          className="w-full py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary-light transition-colors"
        >
          Sign In
        </button>
      </form>
    </div>
  );
}
