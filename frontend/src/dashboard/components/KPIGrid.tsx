import StatCard from '@/components/ui/StatCard';

interface KPIItem {
  title: string;
  value: string;
  subtitle?: string;
}

interface KPIGridProps {
  items: KPIItem[];
}

export default function KPIGrid({ items }: KPIGridProps) {
  return (
    <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <StatCard key={item.title} title={item.title} value={item.value} subtitle={item.subtitle} />
      ))}
    </section>
  );
}
