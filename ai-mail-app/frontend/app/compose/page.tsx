/** Compose Email Page. */
"use client";

import React from "react";
import { MailLayout } from "@/components/layout/MailLayout";
import { ComposeForm } from "@/components/email/ComposeForm";

export default function ComposePage() {
  return (
    <MailLayout>
      <div className="h-full flex flex-col">
        <ComposeForm />
      </div>
    </MailLayout>
  );
}
