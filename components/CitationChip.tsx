interface CitationChipProps {
  children: React.ReactNode;
}

export default function CitationChip({ children }: CitationChipProps) {
  return <span className="chip">{children}</span>;
}