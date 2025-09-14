"use client";
import { useParams } from "next/navigation";
import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Copy, ExternalLink, RefreshCw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const statusColors = {
  PENDING: "secondary",
  STARTED: "default",
  SUCCESS: "secondary",
  FAILURE: "destructive",
  RETRY: "secondary",
  REVOKED: "secondary",
} as const;

function StatusBadge({ status }: { status: string }) {
  const variant =
    statusColors[status as keyof typeof statusColors] || "secondary";
  return <Badge variant={variant}>{status}</Badge>;
}

function CopyableCode({ value, label }: { value: string; label?: string }) {
  const { toast } = useToast();

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(value);
    toast({ title: `${label || "Value"} copied to clipboard` });
  };

  return (
    <div className="flex items-center gap-2">
      <code className="text-xs bg-muted rounded px-2 py-1 font-mono">
        {value}
      </code>
      <Button
        variant="ghost"
        size="sm"
        onClick={copyToClipboard}
        className="h-6 w-6 p-0"
      >
        <Copy className="h-3 w-3" />
      </Button>
    </div>
  );
}

export default function JobDetailPage() {
  const params = useParams<{ task_id: string }>();
  const taskId = params.task_id;
  const qc = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["job", taskId],
    queryFn: () => api.jobs.get(taskId as string),
    refetchInterval: 3000,
  });

  // Stop polling when job reaches terminal state
  useEffect(() => {
    if (data) {
      const terminalStates = ["SUCCESS", "FAILURE", "REVOKED"];
      if (terminalStates.includes(data.status)) {
        qc.setQueryDefaults(["job", taskId], { refetchInterval: false });
      }
    }
  }, [data, qc, taskId]);

  const copyTaskId = async () => {
    await navigator.clipboard.writeText(taskId);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-6 w-20" />
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Array(4)
                .fill(0)
                .map((_, i) => (
                  <div key={i}>
                    <Skeleton className="h-4 w-20 mb-2" />
                    <Skeleton className="h-5 w-24" />
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/jobs">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <h1 className="text-2xl font-semibold">Job Detail</h1>
        </div>

        <Alert variant="destructive">
          <AlertDescription>
            Failed to load job details:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="ml-4"
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/jobs">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <h1 className="text-2xl font-semibold">Job Detail</h1>
        {data && <StatusBadge status={data.status} />}
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-1" />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Task ID
            <CopyableCode value={taskId} label="Task ID" />
          </CardTitle>
        </CardHeader>
      </Card>

      {data?.result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Execution Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm font-medium text-muted-foreground">
                    Return Code
                  </div>
                  <div className="font-mono text-lg mt-1">
                    {data.result.returncode}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">
                    Started At
                  </div>
                  <div className="mt-1">
                    {data.result.started_at
                      ? new Date(data.result.started_at).toLocaleString()
                      : "—"}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">
                    Ended At
                  </div>
                  <div className="mt-1">
                    {data.result.ended_at
                      ? new Date(data.result.ended_at).toLocaleString()
                      : "—"}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">
                    Duration
                  </div>
                  <div className="mt-1">
                    {data.result.started_at && data.result.ended_at
                      ? `${Math.round(
                          (new Date(data.result.ended_at).getTime() -
                            new Date(data.result.started_at).getTime()) /
                            1000
                        )}s`
                      : "—"}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {data.result.error_message && (
            <Alert variant="destructive">
              <AlertDescription>
                <strong>Error:</strong> {data.result.error_message}
              </AlertDescription>
            </Alert>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Output Files ({data.result.files.length})</CardTitle>
            </CardHeader>
            <CardContent>
              {data.result.files.length === 0 ? (
                <p className="text-muted-foreground">No files generated</p>
              ) : (
                <div className="space-y-2">
                  {data.result.files.map((filePath: string, index: number) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-muted rounded-md"
                    >
                      <code className="text-sm break-all">{filePath}</code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigator.clipboard.writeText(filePath)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {data.result.s3 && data.result.s3.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>S3 Uploads ({data.result.s3.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {data.result.s3.map((s3Info: any, index: number) => (
                    <div key={index} className="p-3 bg-muted rounded-md">
                      <pre className="text-sm">
                        {JSON.stringify(s3Info, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {data && !data.result && (
        <Alert>
          <AlertDescription>
            Job is {data.status.toLowerCase()}. Results will appear when
            execution completes.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
