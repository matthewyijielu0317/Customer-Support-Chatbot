import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useState } from 'react';
import { Eye, EyeOff, Mail, Lock, Loader2, AlertCircle } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  passcode: z.string().min(1, 'Passcode is required'),
});

type LoginFormInputs = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onLogin: (data: LoginFormInputs) => Promise<void>;
  isLoggingIn: boolean;
}

export function LoginForm({ onLogin, isLoggingIn }: LoginFormProps) {
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormInputs>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: 'matthewyijielu0317@gmail.com',
      passcode: '12345',
    },
  });

  const onSubmit = async (data: LoginFormInputs) => {
    setError(null);
    try {
      await onLogin(data);
    } catch (err) {
      setError('Invalid email or passcode. Please try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Error banner */}
      {error && (
        <div className="flex items-center space-x-3 p-4 bg-error-950/30 border border-error-800/50 rounded-xl animate-slide-down">
          <AlertCircle size={20} className="text-error-400 flex-shrink-0" />
          <p className="text-sm text-error-200">{error}</p>
        </div>
      )}

      {/* Email field */}
      <div className="space-y-2">
        <label htmlFor="email" className="block text-sm font-medium text-gray-300">
          Email Address
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Mail size={18} className="text-gray-400" />
          </div>
          <input
            id="email"
            type="email"
            autoComplete="email"
            {...register('email')}
            className={`block w-full pl-10 pr-4 py-3 bg-gray-700/50 border rounded-xl shadow-inner-soft placeholder-gray-400 text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200 ${
              errors.email 
                ? 'border-error-500 focus:ring-error-500' 
                : 'border-gray-600 hover:border-gray-500'
            }`}
            placeholder="Enter your email"
          />
        </div>
        {errors.email && (
          <p className="flex items-center space-x-1 text-sm text-error-400 animate-slide-up">
            <AlertCircle size={14} />
            <span>{errors.email.message}</span>
          </p>
        )}
      </div>

      {/* Passcode field */}
      <div className="space-y-2">
        <label htmlFor="passcode" className="block text-sm font-medium text-gray-300">
          Passcode
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Lock size={18} className="text-gray-400" />
          </div>
          <input
            id="passcode"
            type={showPassword ? 'text' : 'password'}
            autoComplete="current-password"
            {...register('passcode')}
            className={`block w-full pl-10 pr-12 py-3 bg-gray-700/50 border rounded-xl shadow-inner-soft placeholder-gray-400 text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200 ${
              errors.passcode 
                ? 'border-error-500 focus:ring-error-500' 
                : 'border-gray-600 hover:border-gray-500'
            }`}
            placeholder="Enter your passcode"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-300 transition-colors"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
        {errors.passcode && (
          <p className="flex items-center space-x-1 text-sm text-error-400 animate-slide-up">
            <AlertCircle size={14} />
            <span>{errors.passcode.message}</span>
          </p>
        )}
      </div>

      {/* Submit button */}
      <button
        type="submit"
        disabled={isLoggingIn}
        className="group relative w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-xl text-sm font-medium text-white bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-500 hover:to-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed shadow-soft hover:shadow-medium transition-all duration-200 overflow-hidden"
      >
        {/* Background animation */}
        <div className="absolute inset-0 bg-gradient-to-r from-primary-400/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
        
        {/* Button content */}
        <div className="relative flex items-center space-x-2">
          {isLoggingIn ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              <span>Signing in...</span>
            </>
          ) : (
            <span>Sign In</span>
          )}
        </div>
      </button>
    </form>
  );
}
