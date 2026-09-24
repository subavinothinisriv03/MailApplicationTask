/** Sent Emails Page. */
"use client";

import React, { useEffect } from "react";
import { MailLayout } from "@/components/layout/MailLayout";
import { EmailList } from "@/components/email/EmailList";
import { useEmailStore } from "@/stores/emailStore";

export default function SentPage() {
  const { setCurrentFolder } = useEmailStore();

  useEffect(() => {
    setCurrentFolder("sent");
  }, [setCurrentFolder]);

  return (
    <MailLayout>
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">Sent Messages</h1>
        </div>
        <div className="flex-1 min-h-0">
          <EmailList title="Sent" />
        </div>
      </div>
    </MailLayout>
  );
}
