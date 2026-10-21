import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { authApi } from '../../services/api';
import { AuthProvider } from '../../context/AuthContext';
import Login from './Login';

describe('Login flow', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it.each([
    ['client', '/', 'Applicant home'],
    ['admin', '/admin', 'Admin dashboard'],
  ] as const)('stores the token and routes a %s account to %s', async (role, path, destination) => {
    const user = {
      id: 7,
      email: 'person@example.test',
      full_name: 'Test Person',
      role,
      created_at: '2026-01-01T00:00:00',
    };
    const login = vi.spyOn(authApi, 'login').mockResolvedValue({
      token: 'test-jwt-token',
      user,
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<p>Applicant home</p>} />
            <Route path="/admin" element={<p>Admin dashboard</p>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: ' person@example.test ' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'correct-password' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Log In' }));

    expect(await screen.findByText(destination)).toBeTruthy();
    expect(login).toHaveBeenCalledWith({
      email: 'person@example.test',
      password: 'correct-password',
    });
    expect(localStorage.getItem('xai_loan_token')).toBe('test-jwt-token');
    expect(path).toBe(role === 'admin' ? '/admin' : '/');
  });
});
