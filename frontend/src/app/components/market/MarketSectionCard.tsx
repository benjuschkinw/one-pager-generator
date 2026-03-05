"use client";

interface Props {
  title: string;
  slideNumber: number;
  children: React.ReactNode;
}

export default function MarketSectionCard({ title, slideNumber, children }: Props) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200/80 overflow-hidden">
      <div className="px-5 py-3 bg-gray-50 border-b border-gray-100 flex items-center gap-2">
        <span className="text-xs font-mono text-gray-400 bg-gray-200 px-1.5 py-0.5 rounded">
          S{slideNumber}
        </span>
        <h3 className="text-sm font-semibold text-cc-dark">{title}</h3>
      </div>
      <div className="px-5 py-4 space-y-3">
        {children}
      </div>
    </div>
  );
}
