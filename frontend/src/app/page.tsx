import ConfigPanel from "@/components/ConfigPanel";
import Dashboard from "@/components/Dashboard";

export default function Home() {
  return (
    <main className="flex h-screen">
      <ConfigPanel />
      <Dashboard />
    </main>
  );
}
