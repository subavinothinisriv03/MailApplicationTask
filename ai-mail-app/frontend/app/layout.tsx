import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Mail App — Autonomous UI Assistant",
  description: "Production-ready AI-powered email web application where an AI assistant controls the user interface.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const storedTheme = localStorage.getItem('theme') || 'dark';
                const isDark = storedTheme === 'dark' || (storedTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                if (isDark) {
                  document.documentElement.classList.add('dark');
                } else {
                  document.documentElement.classList.remove('dark');
                }
              } catch (_) {}
            `,
          }}
        />
      </head>
      <body className="bg-background text-foreground font-sans antialiased overflow-hidden">
        {children}
      </body>
    </html>
  );
}
