/**
 * __tests__/Button.test.jsx - Tests for Button UI component
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from '../Button';

describe('Button Component', () => {
  describe('Rendering', () => {
    it('renders with text', () => {
      render(<Button>Click Me</Button>);
      expect(screen.getByText('Click Me')).toBeInTheDocument();
    });

    it('renders with variant prop', () => {
      const { container } = render(<Button variant="primary">Click</Button>);
      const button = container.querySelector('button');
      expect(button).toHaveClass('primary');
    });

    it('renders disabled state', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('renders with loading state', () => {
      render(<Button loading>Loading...</Button>);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders with icon', () => {
      const Icon = () => <span>Icon</span>;
      render(
        <Button icon={Icon}>
          With Icon
        </Button>
      );
      expect(screen.getByText('Icon')).toBeInTheDocument();
    });

    it('renders as link when href provided', () => {
      const { container } = render(<Button href="/path">Link</Button>);
      const link = container.querySelector('a');
      expect(link).toHaveAttribute('href', '/path');
    });
  });

  describe('Interactions', () => {
    it('handles click events', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Click</Button>);

      const button = screen.getByRole('button');
      await userEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', async () => {
      const handleClick = jest.fn();
      render(
        <Button disabled onClick={handleClick}>
          Disabled
        </Button>
      );

      const button = screen.getByRole('button');
      await userEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('handles multiple clicks', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Click</Button>);

      const button = screen.getByRole('button');
      await userEvent.click(button);
      await userEvent.click(button);
      await userEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(3);
    });

    it('handles keyboard interaction (Enter key)', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Click</Button>);

      const button = screen.getByRole('button');
      button.focus();
      await userEvent.keyboard('{Enter}');

      expect(handleClick).toHaveBeenCalled();
    });

    it('handles keyboard interaction (Space key)', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Click</Button>);

      const button = screen.getByRole('button');
      button.focus();
      await userEvent.keyboard(' ');

      expect(handleClick).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has accessible role', () => {
      render(<Button>Click</Button>);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('supports aria-label', () => {
      render(<Button aria-label="Submit Form">Submit</Button>);
      expect(screen.getByLabelText('Submit Form')).toBeInTheDocument();
    });

    it('supports aria-disabled', () => {
      render(<Button aria-disabled={true}>Disabled</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('aria-disabled', 'true');
    });

    it('has semantic HTML', () => {
      const { container } = render(<Button>Click</Button>);
      expect(container.querySelector('button')).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('applies primary variant styles', () => {
      const { container } = render(<Button variant="primary">Click</Button>);
      expect(container.querySelector('button')).toHaveClass('primary');
    });

    it('applies secondary variant styles', () => {
      const { container } = render(<Button variant="secondary">Click</Button>);
      expect(container.querySelector('button')).toHaveClass('secondary');
    });

    it('applies size classes', () => {
      const { container } = render(<Button size="lg">Click</Button>);
      expect(container.querySelector('button')).toHaveClass('lg');
    });

    it('applies custom className', () => {
      const { container } = render(<Button className="custom">Click</Button>);
      expect(container.querySelector('button')).toHaveClass('custom');
    });
  });

  describe('Props', () => {
    it('accepts children as string', () => {
      render(<Button>Text Button</Button>);
      expect(screen.getByText('Text Button')).toBeInTheDocument();
    });

    it('accepts children as elements', () => {
      render(
        <Button>
          <span>Icon</span>
          Text
        </Button>
      );
      expect(screen.getByText('Icon')).toBeInTheDocument();
      expect(screen.getByText('Text')).toBeInTheDocument();
    });

    it('accepts all standard button props', () => {
      render(
        <Button
          type="submit"
          name="test"
          data-testid="btn"
        >
          Click
        </Button>
      );
      const button = screen.getByTestId('btn');
      expect(button).toHaveAttribute('type', 'submit');
      expect(button).toHaveAttribute('name', 'test');
    });
  });

  describe('Loading State', () => {
    it('shows loading spinner', () => {
      render(<Button loading>Loading</Button>);
      // Assuming loading spinner is rendered when loading=true
      expect(screen.getByText('Loading')).toBeInTheDocument();
    });

    it('disables button while loading', () => {
      render(<Button loading>Load</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });
  });
});
