import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="font-semibold text-brand-900">XAI Loan System</Link>
        <div className="flex items-center gap-4 text-sm">
          {user ? (
            <>
              <Link to="/apply" className="text-slate-600 hover:text-brand-700">Apply</Link>
              <Link to="/history" className="text-slate-600 hover:text-brand-700">History</Link>
              {(user.role === 'admin' || user.role === 'loan_officer') && (
                <Link to="/admin" className="text-slate-600 hover:text-brand-700">Admin</Link>
              )}
              <Link to="/profile" className="text-slate-600 hover:text-brand-700">{user.full_name}</Link>
              <button onClick={handleLogout} className="text-slate-500 hover:text-rejected">Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-slate-600 hover:text-brand-700">Login</Link>
              <Link to="/register" className="bg-brand-600 text-white px-3 py-1.5 rounded-md hover:bg-brand-700">
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
