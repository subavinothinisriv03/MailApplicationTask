"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/inbox");
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-zinc-950 text-white">
      <div className="flex flex-col items-center space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
        <p className="text-xs text-zinc-400">Loading AI Mail App...</p>
      </div>
    </div>
  );
}
