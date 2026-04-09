import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema } from '../../schemas/authSchema';
import { Input, Alert } from '../ui/index';
import { useState } from 'react';
import { User, KeyRound, ArrowRight } from 'lucide-react';

export default function LoginForm({ onSubmit, loading = false, onSwitchMode }) {
  const [errorAlert, setErrorAlert] = useState('');
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(loginSchema),
    mode: 'onSubmit',
    defaultValues: {
      username: '',
      password: '',
    },
  });

  const onSubmitHandler = async (data) => {
    try {
      setErrorAlert('');
      await onSubmit(data);
    } catch (error) {
      setErrorAlert(error.message || 'Login failed. Please try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmitHandler)} className="w-full space-y-5">
      {errorAlert && (
        <Alert
          variant="error"
          message={errorAlert}
          onClose={() => setErrorAlert('')}
        />
      )}

      <div className="space-y-2">
        <label className="px-1 text-xs font-bold uppercase tracking-[0.12em] text-[#07376a]">Username</label>
        <Input
          icon={User}
          placeholder="rit_student_id"
          error={errors.username?.message}
          {...register('username')}
          disabled={loading}
          className="rounded-lg border border-[#d5dde6] bg-white/95 text-[#191c1e] placeholder:text-[#737783]/70 shadow-sm focus:border-[#07376a]/30 focus:ring-2 focus:ring-[#07376a]/20"
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between px-1">
          <label className="text-xs font-bold uppercase tracking-[0.12em] text-[#07376a]">Access Key</label>
          <button
            type="button"
            onClick={onSwitchMode}
            className="text-xs font-semibold text-[#505f76] hover:text-[#07376a]"
          >
            Request Access?
          </button>
        </div>
        <Input
          type="password"
          icon={KeyRound}
          placeholder="••••••••"
          error={errors.password?.message}
          {...register('password')}
          disabled={loading}
          className="rounded-lg border border-[#d5dde6] bg-white/95 text-[#191c1e] placeholder:text-[#737783]/70 shadow-sm focus:border-[#07376a]/30 focus:ring-2 focus:ring-[#07376a]/20"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-br from-[#07376a] to-[#3a5f94] py-3.5 font-astro-headline text-sm font-extrabold text-white shadow-[0_12px_24px_rgba(7,55,106,0.15)] transition-all duration-200 hover:scale-[1.01] disabled:opacity-60"
      >
        {loading ? 'Signing In...' : 'Login'}
        {!loading && <ArrowRight size={18} />}
      </button>

      <div className="pt-2 text-center text-xs text-[#505f76]">
        New to AstroBot?{' '}
        <button type="button" onClick={onSwitchMode} className="font-bold text-[#07376a] hover:underline">
          Create account
        </button>
      </div>
    </form>
  );
}
