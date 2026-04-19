type RateCardProps = {
  currency: string;
  code: string;
  rate: string;
  hint: string;
};

export function RateCard({ currency, code, rate, hint }: RateCardProps) {
  return (
    <div className="rounded-panel border border-black/5 bg-white p-6 shadow-soft">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-3xl font-semibold text-ink">{currency}</p>
          <p className="mt-1 text-base uppercase tracking-[0.24em] text-black/40">{code}</p>
        </div>
        <span className="rounded-full bg-[#F5F7F4] px-4 py-2 text-sm text-black/55">{hint}</span>
      </div>
      <p className="font-display text-5xl font-semibold text-ink">{rate}</p>
    </div>
  );
}

