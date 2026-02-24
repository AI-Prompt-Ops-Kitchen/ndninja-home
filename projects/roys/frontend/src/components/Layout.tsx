import { Link, Outlet, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';

const NAV_ITEMS = [
  { path: '/', label: 'Home' },
  { path: '/catalog', label: 'Catalog' },
  { path: '/generate', label: 'Generate' },
  { path: '/admin', label: 'Admin' },
];

export default function Layout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-navy-50 text-navy-950">
      <header className="bg-white border-b border-navy-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="text-xl font-bold text-primary">
              ROYS
            </Link>
            <nav className="flex items-center gap-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    location.pathname === item.path
                      ? 'bg-navy-100 text-primary'
                      : 'text-navy-600 hover:text-primary hover:bg-navy-50',
                  )}
                >
                  {item.label}
                </Link>
              ))}
              <Link
                to="/login"
                className="ml-4 px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary-light transition-colors"
              >
                Sign In
              </Link>
            </nav>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-navy-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center text-navy-500 text-sm">
          Roystonea Systems &copy; {new Date().getFullYear()}
        </div>
      </footer>
    </div>
  );
}
