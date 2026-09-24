/** Email Detail Page. */
"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { MailLayout } from "@/components/layout/MailLayout";
import { EmailDetail } from "@/components/email/EmailDetail";
import { useEmailStore } from "@/stores/emailStore";
import { Email } from "@/lib/types";
import { Loader2 } from "lucide-react";

export default function EmailDetailPage() {
  const params = useParams();
  const emailId = params?.id as string;
  const { selectEmailById, selectedEmail } = useEmailStore();
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState<Email | null>(null);

  useEffect(() => {
    if (!emailId) return;

    let isMounted = true;
    setLoading(true);

    selectEmailById(emailId).then((res) => {
      if (isMounted) {
        setEmail(res);
        setLoading(false);
      }
    });

    return () => {
      isMounted = false;
    };
  }, [emailId, selectEmailById]);

  return (
    <MailLayout>
      <div className="h-full flex flex-col">
        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="flex flex-col items-center space-y-2 text-zinc-400">
              <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
              <span className="text-xs">Loading email details...</span>
            </div>
          </div>
        ) : email ? (
          <EmailDetail email={email} />
        ) : (
          <div className="flex-1 flex items-center justify-center text-xs text-zinc-500">
            Email not found or has been deleted.
          </div>
        )}
      </div>
    </MailLayout>
  );
}
