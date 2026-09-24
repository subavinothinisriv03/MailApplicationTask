import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-zinc-950 text-white p-4">
      <h1 className="text-4xl font-bold text-blue-500 mb-2">404</h1>
      <h2 className="text-lg font-semibold mb-4">Page Not Found</h2>
      <p className="text-xs text-zinc-400 mb-6 max-w-sm text-center">
        The mail view you are looking for does not exist or has been moved.
      </p>
      <Link
        href="/inbox"
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl transition-all"
      >
        Return to Inbox
      </Link>
    </div>
  );
}
