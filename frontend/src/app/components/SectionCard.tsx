"use client";

interface SectionCardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

export default function SectionCard({ title, children, className = "" }: SectionCardProps) {
  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      <div className="bg-cc-dark text-white px-4 py-2 rounded-t-lg">
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
