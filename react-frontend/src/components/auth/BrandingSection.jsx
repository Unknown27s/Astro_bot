import { Rocket, Sparkles } from 'lucide-react';

export default function BrandingSection() {
  return (
    <div className="flex flex-col items-center text-center">
      <div className="mb-6 flex h-28 w-28 items-center justify-center rounded-full border border-white/50 bg-white/70 p-3 shadow-[0_20px_40px_rgba(7,55,106,0.06)] backdrop-blur-sm">
        <div className="relative">
          <Rocket size={54} className="text-[#07376a]" strokeWidth={2.2} />
          <div className="absolute -right-1 -top-1 h-4 w-4 rounded-full bg-[#b7eaff]" />
        </div>
      </div>

      <h1 className="font-astro-headline text-5xl font-extrabold tracking-tight text-[#07376a]">AstroBot</h1>
      <p className="mt-2 text-xs font-semibold uppercase tracking-[0.35em] text-[#505f76]">Academic Concierge</p>

      <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-[#07376a]/20 bg-white/60 px-3 py-1 text-[11px] font-semibold text-[#07376a]">
        <Sparkles size={12} />
        Secure Institutional Login
      </div>

      <p className="mt-4 text-sm text-[#505f76]">Access your campus assistant workspace</p>
    </div>
  );
}
