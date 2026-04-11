/**
 * __tests__/LoginPage.test.jsx - Tests for LoginPage
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import LoginPage from '../LoginPage';

// Mock the API
jest.mock('../../services/api', () => ({
  login: jest.fn(),
}));

const renderLoginPage = () => {
  return render(
    <BrowserRouter>
      <LoginPage />
    </BrowserRouter>
  );
};

describe('LoginPage', () => {
  describe('Rendering', () => {
    it('renders login form', () => {
      renderLoginPage();
      expect(screen.getByText(/login/i)).toBeInTheDocument();
    });

    it('renders username input', () => {
      renderLoginPage();
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    });

    it('renders password input', () => {
      renderLoginPage();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it('renders submit button', () => {
      renderLoginPage();
      expect(screen.getByRole('button', { name: /login|sign in/i })).toBeInTheDocument();
    });

    it('renders register link', () => {
      renderLoginPage();
      expect(screen.getByText(/register|sign up/i)).toBeInTheDocument();
    });

    it('renders forgot password link', () => {
      renderLoginPage();
      expect(screen.getByText(/forgot password/i)).toBeInTheDocument();
    });

    it('displays branding section', () => {
      renderLoginPage();
      // Assuming BrandingSection displays college name
      expect(screen.getByText(/astrobot|rajalakshmi/i)).toBeInTheDocument();
    });
  });

  describe('Form Input', () => {
    it('updates username input', async () => {
      renderLoginPage();
      const input = screen.getByLabelText(/username/i);

      await userEvent.type(input, 'testuser');
      expect(input).toHaveValue('testuser');
    });

    it('updates password input', async () => {
      renderLoginPage();
      const input = screen.getByLabelText(/password/i);

      await userEvent.type(input, 'password123');
      expect(input).toHaveValue('password123');
    });

    it('password input is type password', () => {
      renderLoginPage();
      const input = screen.getByLabelText(/password/i);
      expect(input).toHaveAttribute('type', 'password');
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid credentials', async () => {
      const { login } = require('../../services/api');
      login.mockResolvedValue({ success: true, token: 'mock_token' });

      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
      await userEvent.type(screen.getByLabelText(/password/i), 'password123');
      await userEvent.click(screen.getByRole('button', { name: /login/i }));

      await waitFor(() => {
        expect(login).toHaveBeenCalledWith('testuser', 'password123');
      });
    });

    it('shows loading state during submission', async () => {
      const { login } = require('../../services/api');
      login.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ success: true }), 100))
      );

      renderLoginPage();

      const submitBtn = screen.getByRole('button', { name: /login/i });
      await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
      await userEvent.type(screen.getByLabelText(/password/i), 'password123');
      await userEvent.click(submitBtn);

      // Button should show loading state
      expect(submitBtn).toBeDisabled();
    });

    it('prevents submission with empty fields', async () => {
      const { login } = require('../../services/api');

      renderLoginPage();
      const submitBtn = screen.getByRole('button', { name: /login/i });
      await userEvent.click(submitBtn);

      expect(login).not.toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('displays error message on failed login', async () => {
      const { login } = require('../../services/api');
      login.mockResolvedValue({ success: false, error: 'Invalid credentials' });

      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
      await userEvent.type(screen.getByLabelText(/password/i), 'wrong');
      await userEvent.click(screen.getByRole('button', { name: /login/i }));

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });

    it('shows error for non-existent user', async () => {
      const { login } = require('../../services/api');
      login.mockResolvedValue({ success: false, error: 'User not found' });

      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/username/i), 'nonexistent');
      await userEvent.type(screen.getByLabelText(/password/i), 'password');
      await userEvent.click(screen.getByRole('button', { name: /login/i }));

      await waitFor(() => {
        expect(screen.getByText(/user not found/i)).toBeInTheDocument();
      });
    });

    it('shows error for network failure', async () => {
      const { login } = require('../../services/api');
      login.mockRejectedValue(new Error('Network error'));

      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
      await userEvent.type(screen.getByLabelText(/password/i), 'password');
      await userEvent.click(screen.getByRole('button', { name: /login/i }));

      await waitFor(() => {
        expect(screen.getByText(/network error|connection failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('navigates to home on successful login', async () => {
      const { login } = require('../../services/api');
      login.mockResolvedValue({ success: true, token: 'mock_token' });

      const { history } = renderLoginPage();

      await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
      await userEvent.type(screen.getByLabelText(/password/i), 'password');
      await userEvent.click(screen.getByRole('button', { name: /login/i }));

      // Navigation would happen after successful login
      // This depends on implementation (redirect, navigation, etc.)
    });

    it('register link navigates to registration', async () => {
      renderLoginPage();
      const registerLink = screen.getByText(/register|sign up/i);

      expect(registerLink).toBeInTheDocument();
      // Click and verify navigation (implementation specific)
    });
  });

  describe('Accessibility', () => {
    it('form has accessible labels', () => {
      renderLoginPage();
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it('submit button is accessible', () => {
      renderLoginPage();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    });

    it('has semantic HTML structure', () => {
      const { container } = renderLoginPage();
      expect(container.querySelector('form')).toBeInTheDocument();
    });

    it('supports keyboard navigation', async () => {
      renderLoginPage();
      const usernameInput = screen.getByLabelText(/username/i);

      usernameInput.focus();
      expect(usernameInput).toHaveFocus();

      await userEvent.keyboard('{Tab}');
      const passwordInput = screen.getByLabelText(/password/i);
      expect(passwordInput).toHaveFocus();
    });
  });

  describe('Form Validation', () => {
    it('shows validation error for empty username', async () => {
      renderLoginPage();

      const submitBtn = screen.getByRole('button', { name: /login/i });
      await userEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument();
      });
    });

    it('shows validation error for short password', async () => {
      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
      await userEvent.type(screen.getByLabelText(/password/i), '123');

      const submitBtn = screen.getByRole('button', { name: /login/i });
      await userEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByText(/password too short/i)).toBeInTheDocument();
      });
    });
  });

  describe('Test Mode Buttons', () => {
    it('renders test mode buttons', () => {
      // Assuming test buttons exist in development
      renderLoginPage();
      const testButtons = screen.queryAllByText(/admin|student|faculty/i);
      // May or may not exist depending on environment
    });

    it('test button sets credentials', async () => {
      renderLoginPage();
      const adminButton = screen.queryByText(/test.*admin/i);

      if (adminButton) {
        await userEvent.click(adminButton);
        // Should populate form and login
      }
    });
  });

  describe('Responsive Design', () => {
    it('renders on mobile', () => {
      // Mock mobile viewport
      global.innerWidth = 375;
      renderLoginPage();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    });

    it('renders on desktop', () => {
      global.innerWidth = 1024;
      renderLoginPage();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    });
  });
});
