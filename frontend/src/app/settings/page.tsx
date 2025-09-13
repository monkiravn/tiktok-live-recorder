"use client";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { Settings, Palette, Clock, Globe, Save } from "lucide-react";

export default function SettingsPage() {
  const { toast } = useToast();
  const [settings, setSettings] = useState({
    theme: "light",
    timezone: "Asia/Ho_Chi_Minh",
    language: "vi",
    dateFormat: "DD/MM/YYYY HH:mm",
  });

  const handleSave = () => {
    // In a real app, this would save to localStorage or send to API
    localStorage.setItem("app-settings", JSON.stringify(settings));
    toast({ title: "Settings saved successfully" });
  };

  const handleReset = () => {
    setSettings({
      theme: "light",
      timezone: "Asia/Ho_Chi_Minh",
      language: "vi",
      dateFormat: "DD/MM/YYYY HH:mm",
    });
    toast({ title: "Settings reset to defaults" });
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-muted-foreground">
          Customize your dashboard experience and preferences.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Appearance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Theme</Label>
            <Select
              value={settings.theme}
              onValueChange={(value) =>
                setSettings((prev) => ({ ...prev, theme: value }))
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground mt-1">
              Choose your preferred color theme
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Date & Time
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Timezone</Label>
            <Select
              value={settings.timezone}
              onValueChange={(value) =>
                setSettings((prev) => ({ ...prev, timezone: value }))
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Asia/Ho_Chi_Minh">
                  Ho Chi Minh City (UTC+7)
                </SelectItem>
                <SelectItem value="UTC">UTC</SelectItem>
                <SelectItem value="America/New_York">
                  New York (UTC-5)
                </SelectItem>
                <SelectItem value="Europe/London">London (UTC+0)</SelectItem>
                <SelectItem value="Asia/Tokyo">Tokyo (UTC+9)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Date Format</Label>
            <Select
              value={settings.dateFormat}
              onValueChange={(value) =>
                setSettings((prev) => ({ ...prev, dateFormat: value }))
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DD/MM/YYYY HH:mm">
                  DD/MM/YYYY HH:mm
                </SelectItem>
                <SelectItem value="MM/DD/YYYY HH:mm">
                  MM/DD/YYYY HH:mm
                </SelectItem>
                <SelectItem value="YYYY-MM-DD HH:mm">
                  YYYY-MM-DD HH:mm
                </SelectItem>
                <SelectItem value="DD MMM YYYY HH:mm">
                  DD MMM YYYY HH:mm
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground mt-1">
              Current time: {new Date().toLocaleString()}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Localization
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Language</Label>
            <Select
              value={settings.language}
              onValueChange={(value) =>
                setSettings((prev) => ({ ...prev, language: value }))
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="vi">Tiếng Việt</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
            <Badge variant="secondary" className="mt-2">
              Coming Soon: Full internationalization
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            System Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Version</span>
              <p className="font-mono">1.0.0</p>
            </div>
            <div>
              <span className="text-muted-foreground">Build</span>
              <p className="font-mono">2025.09.13</p>
            </div>
            <div>
              <span className="text-muted-foreground">Framework</span>
              <p>Next.js 14</p>
            </div>
            <div>
              <span className="text-muted-foreground">Node Version</span>
              <p className="font-mono">{process.version || "Unknown"}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Button onClick={handleSave} className="flex-1 sm:flex-none">
          <Save className="h-4 w-4 mr-2" />
          Save Settings
        </Button>
        <Button variant="outline" onClick={handleReset}>
          Reset to Defaults
        </Button>
      </div>
    </div>
  );
}
