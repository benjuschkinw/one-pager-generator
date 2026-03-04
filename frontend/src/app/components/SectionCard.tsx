"use client";

interface SectionCardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

export default function SectionCard({ title, children, className = "" }: SectionCardProps) {
  return (
    <div className={`bg-white rounded-lg border border-gray-200/80 shadow-sm overflow-hidden ${className}`}>
      <div className="bg-cc-dark px-4 py-2">
        <h3 className="text-xs font-semibold text-white uppercase tracking-wide">{title}</h3>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
