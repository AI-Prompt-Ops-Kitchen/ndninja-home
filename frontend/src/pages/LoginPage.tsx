import { useLocation } from 'react-router-dom'
import { LoginForm } from '../components/auth/LoginForm'

export function LoginPage() {
  const location = useLocation()
  const message = location.state?.message

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Sage Mode</h1>
          <p className="mt-2 text-gray-600">Sign in to your account</p>
        </div>

        {message && (
          <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
            {message}
          </div>
        )}

        <div className="bg-white p-8 rounded-lg shadow-md">
          <LoginForm />
        </div>
      </div>
    </div>
  )
}
