import { Settings } from "lucide-react";
import { PlaceholderState } from "@/components/dashboard/placeholder-state";

export default function SettingsPage() {
  return (
    <PlaceholderState
      icon={Settings}
      title="Settings"
      description="Account, notification, and audit-scheduling preferences will be configurable here in a future phase."
    />
  );
}
