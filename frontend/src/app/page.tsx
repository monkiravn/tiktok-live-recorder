"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, CheckCircle } from "lucide-react";

function HealthChip({
  label,
  ok,
  loading,
}: {
  label: string;
  ok: boolean;
  loading?: boolean;
}) {
  if (loading) {
    return <Skeleton className="h-6 w-16" />;
  }

  return (
    <Badge variant={ok ? "default" : "destructive"} className="gap-1">
      {ok ? (
        <CheckCircle className="h-3 w-3" />
      ) : (
        <AlertCircle className="h-3 w-3" />
      )}
      {label}: {ok ? "OK" : "DOWN"}
    </Badge>
  );
}

function MetricCard({
  title,
  value,
  loading,
}: {
  title: string;
  value: string | number;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-12" />
        ) : (
          <div className="text-3xl font-bold">{value}</div>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const health = useQuery({
    queryKey: ["healthz"],
    queryFn: api.healthz,
    retry: 1,
    refetchInterval: 10000,
  });

  const ready = useQuery({
    queryKey: ["ready"],
    queryFn: api.ready,
    retry: 1,
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="flex gap-2">
          <HealthChip
            label="API"
            ok={health.isSuccess && health.data === "ok"}
            loading={health.isLoading}
          />
          <HealthChip
            label="Workers"
            ok={ready.isSuccess && ready.data === "ready"}
            loading={ready.isLoading}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard title="Active Watchers" value="—" />
        <MetricCard title="Running Jobs" value="—" />
        <MetricCard title="Success 24h" value="—" />
        <MetricCard title="Failures 24h" value="—" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Jobs per hour (placeholder)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-40 grid place-items-center text-muted-foreground">
            Chart coming soon
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
