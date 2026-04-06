"use client";

interface VehicleSelectorProps {
  title: string;
  vehicles: { name: string; nation: string }[];
  selected: string[];
  onChange: (names: string[]) => void;
}

export default function VehicleSelector({ title, vehicles, selected, onChange }: VehicleSelectorProps) {
  const toggle = (name: string) => {
    if (selected.includes(name)) {
      onChange(selected.filter((n) => n !== name));
    } else {
      onChange([...selected, name]);
    }
  };

  return (
    <div className="mb-4">
      <h3 className="text-sm font-semibold mb-2">{title}</h3>
      <div className="space-y-1">
        {vehicles.map((v) => (
          <label key={v.name} className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={selected.includes(v.name)} onChange={() => toggle(v.name)} className="rounded" />
            <span>{v.name}</span>
            <span className="text-gray-400 text-xs">({v.nation})</span>
          </label>
        ))}
      </div>
    </div>
  );
}
