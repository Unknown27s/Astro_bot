import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { registerSchema } from '../../schemas/authSchema';
import { Input, Select, Alert } from '../ui/index';
import { useState } from 'react';
import { User, KeyRound, ArrowRight } from 'lucide-react';

export default function RegisterForm({ onSubmit, loading = false, onSwitchMode }) {
  const [errorAlert, setErrorAlert] = useState('');
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm({
    resolver: zodResolver(registerSchema),
    mode: 'onSubmit',
    defaultValues: {
      fullName: '',
      username: '',
      password: '',
      confirmPassword: '',
      role: 'student',
    },
  });

  const onSubmitHandler = async (data) => {
    try {
      setErrorAlert('');
      await onSubmit(data);
    } catch (error) {
      setErrorAlert(error.message || 'Registration failed. Please try again.');
    }
  };

  const roleValue = watch('role');

  return (
    <form onSubmit={handleSubmit(onSubmitHandler)} className="w-full space-y-4">
      {errorAlert && (
        <Alert
          variant="error"
          message={errorAlert}
          onClose={() => setErrorAlert('')}
        />
      )}

      <div className="space-y-2">
        <label className="px-1 text-xs font-bold uppercase tracking-[0.12em] text-[#07376a]">Full Name</label>
        <Input
          icon={User}
          placeholder="Enter your full name"
          error={errors.fullName?.message}
          {...register('fullName')}
          disabled={loading}
          className="rounded-lg border border-[#d5dde6] bg-white/95 text-[#191c1e] placeholder:text-[#737783]/70 shadow-sm focus:border-[#07376a]/30 focus:ring-2 focus:ring-[#07376a]/20"
        />
      </div>

      <div className="space-y-2">
        <label className="px-1 text-xs font-bold uppercase tracking-[0.12em] text-[#07376a]">Username</label>
        <Input
          placeholder="Choose a username"
          error={errors.username?.message}
          {...register('username')}
          disabled={loading}
          className="rounded-lg border border-[#d5dde6] bg-white/95 text-[#191c1e] placeholder:text-[#737783]/70 shadow-sm focus:border-[#07376a]/30 focus:ring-2 focus:ring-[#07376a]/20"
        />
      </div>

      <div className="space-y-2">
        <label className="px-1 text-xs font-bold uppercase tracking-[0.12em] text-[#07376a]">Role</label>
        <Select
          options={[
            { value: 'student', label: 'Student' },
            { value: 'faculty', label: 'Faculty' },
          ]}
          error={errors.role?.message}
          {...register('role')}
          disabled={loading}
          className="rounded-lg border border-[#d5dde6] bg-white/95 text-[#191c1e] shadow-sm focus:border-[#07376a]/30 focus:ring-2 focus:ring-[#07376a]/20"
        />
      </div>

      <div className="space-y-2">
        <label className="px-1 text-xs font-bold uppercase tracking-[0.12em] text-[#07376a]">Access Key</label>
        <Input
          type="password"
          icon={KeyRound}
          placeholder="Create a strong password"
          error={errors.password?.message}
          {...register('password')}
          disabled={loading}
          className="rounded-lg border border-[#d5dde6] bg-white/95 text-[#191c1e] placeholder:text-[#737783]/70 shadow-sm focus:border-[#07376a]/30 focus:ring-2 focus:ring-[#07376a]/20"
        />
      </div>

      <div className="space-y-2">
        <label className="px-1 text-xs font-bold uppercase tracking-[0.12em] text-[#07376a]">Confirm Key</label>
        <Input
          type="password"
          icon={KeyRound}
          placeholder="Re-enter your password"
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
          disabled={loading}
          className="rounded-lg border border-[#d5dde6] bg-white/95 text-[#191c1e] placeholder:text-[#737783]/70 shadow-sm focus:border-[#07376a]/30 focus:ring-2 focus:ring-[#07376a]/20"
        />
      </div>

      <div className="rounded-xl border border-[#d0e1fb] bg-[#f4f8ff] p-3 text-sm text-[#38485d]">
        <p className="flex items-center gap-2">
          <span>ℹ️</span>
          <span>
            {roleValue === 'student'
              ? 'Students can ask questions and access resources'
              : 'Faculty can manage content and reply to queries'}
          </span>
        </p>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-br from-[#07376a] to-[#3a5f94] py-3.5 font-astro-headline text-sm font-extrabold text-white shadow-[0_12px_24px_rgba(7,55,106,0.15)] transition-all duration-200 hover:scale-[1.01] disabled:opacity-60"
      >
        {loading ? 'Creating Account...' : 'Create Account'}
        {!loading && <ArrowRight size={18} />}
      </button>

      <div className="pt-2 text-center text-sm text-[#505f76]">
        Already have an account?{' '}
        <button
          type="button"
          onClick={onSwitchMode}
          className="font-bold text-[#07376a] hover:underline"
        >
          Sign in
        </button>
      </div>
    </form>
  );
}
