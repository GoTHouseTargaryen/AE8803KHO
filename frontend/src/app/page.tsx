"use client";

import dynamic from "next/dynamic";

const ConfigPanel = dynamic(() => import("@/components/ConfigPanel"), { ssr: false });
const Dashboard = dynamic(() => import("@/components/Dashboard"), { ssr: false });

export default function Home() {
  return (
    <main className="flex h-screen">
      <ConfigPanel />
      <Dashboard />
    </main>
  );
}
