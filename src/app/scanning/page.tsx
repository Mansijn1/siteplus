import { Suspense } from "react";
import type { Metadata } from "next";
import { ScanningExperience } from "@/components/scanning/scanning-experience";

export const metadata: Metadata = {
  title: "Scanning — WebRate AI",
  description: "Simulated website evaluation in progress.",
};

export default function ScanningPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-report-ruling" />}>
      <ScanningExperience />
    </Suspense>
  );
}
