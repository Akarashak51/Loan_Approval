import { useAuth } from '../../hooks/useAuth';

export default function Profile() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-semibold text-brand-900 mb-6">Profile</h1>
      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3 text-sm">
        <div>
          <p className="text-slate-500">Full Name</p>
          <p className="text-slate-800 font-medium">{user.full_name}</p>
        </div>
        <div>
          <p className="text-slate-500">Email</p>
          <p className="text-slate-800 font-medium">{user.email}</p>
        </div>
        <div>
          <p className="text-slate-500">Role</p>
          <p className="text-slate-800 font-medium capitalize">{user.role.replace('_', ' ')}</p>
        </div>
        <div>
          <p className="text-slate-500">Member Since</p>
          <p className="text-slate-800 font-medium">{new Date(user.created_at).toLocaleDateString()}</p>
        </div>
      </div>
    </div>
  );
}
