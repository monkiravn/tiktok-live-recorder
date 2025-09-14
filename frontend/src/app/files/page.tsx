"use client";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatBytes } from "@/lib/utils";
import type { RecordingFile } from "@/lib/types";
import { Suspense, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { Copy, File, Filter, Search } from "lucide-react";

function FilesView() {
  const sp = useSearchParams();
  const router = useRouter();
  const { toast } = useToast();

  const page = Number(sp.get("page") || 1);
  const page_size = Number(sp.get("page_size") || 20);
  const room_id = sp.get("room_id") || "";
  const url = sp.get("url") || "";

  const { data, isLoading, error } = useQuery({
    queryKey: ["files", { page, page_size, room_id, url }],
    queryFn: () =>
      api.files.list({
        room_id: room_id || undefined,
        url: url || undefined,
        page,
        limit: page_size,
      }),
    placeholderData: keepPreviousData,
  });

  const totalPages = useMemo(
    () => (data ? Math.max(1, Math.ceil(data.total / data.limit)) : 1),
    [data]
  );

  function setParam(k: string, v: string | number | null) {
    const newUrl = new URL(window.location.href);
    if (v === null || v === "" || v === 0) {
      newUrl.searchParams.delete(k);
    } else {
      newUrl.searchParams.set(k, String(v));
    }
    if (k !== "page") {
      newUrl.searchParams.set("page", "1"); // Reset to first page when filtering
    }
    router.push(newUrl.pathname + newUrl.search);
  }

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast({ title: `${label} copied to clipboard` });
    } catch (error) {
      toast({
        title: "Copy failed",
        description: "Could not copy to clipboard",
        variant: "destructive",
      });
    }
  };

  const LoadingRows = () => (
    <>
      {Array(5)
        .fill(0)
        .map((_, i) => (
          <TableRow key={i}>
            <TableCell>
              <Skeleton className="h-4 w-32" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-4 w-16" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-4 w-24" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-4 w-64" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-8 w-8" />
            </TableCell>
          </TableRow>
        ))}
    </>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Files</h1>
        <Badge variant="secondary">
          {data ? `${data.total} files` : "Loading..."}
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="room_id">Room ID</Label>
              <Input
                id="room_id"
                placeholder="Filter by room ID"
                value={room_id}
                onChange={(e) => setParam("room_id", e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="url">URL</Label>
              <Input
                id="url"
                placeholder="Filter by URL"
                value={url}
                onChange={(e) => setParam("url", e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="page_size">Page Size</Label>
              <Input
                id="page_size"
                type="number"
                min="1"
                max="200"
                value={page_size}
                onChange={(e) =>
                  setParam("page_size", parseInt(e.target.value) || 20)
                }
              />
            </div>
          </div>
          <div>
            <Button
              onClick={() => setParam("page", 1)}
              className="w-full md:w-auto"
            >
              <Search className="h-4 w-4 mr-2" />
              Apply Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {error ? (
            <div className="text-center py-8">
              <p className="text-destructive">Failed to load files</p>
              <p className="text-sm text-muted-foreground mt-1">
                {error instanceof Error ? error.message : "Unknown error"}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Modified</TableHead>
                  <TableHead>Path</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <LoadingRows />
                ) : data?.files?.length ? (
                  data.files.map((item: RecordingFile) => (
                    <TableRow key={item.file_path}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <File className="h-4 w-4 text-muted-foreground" />
                          <span className="break-all">{item.filename}</span>
                        </div>
                      </TableCell>
                      <TableCell>{formatBytes(item.file_size)}</TableCell>
                      <TableCell>
                        {new Date(item.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <code className="text-xs bg-muted rounded px-2 py-1 break-all">
                          {item.file_path}
                        </code>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            copyToClipboard(item.file_path, "File path")
                          }
                          className="h-8 w-8 p-0"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8">
                      <div className="text-muted-foreground">
                        <File className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No files found</p>
                        <p className="text-sm mt-1">
                          Try adjusting your filters
                        </p>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {data && data.total > 0 && (
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {(data.page - 1) * data.limit + 1} to{" "}
                {Math.min(data.page * data.limit, data.total)} of{" "}
                {data.total} files
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setParam("page", page - 1)}
                >
                  Previous
                </Button>
                <div className="flex items-center px-3 text-sm">
                  Page {page} of {totalPages}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setParam("page", page + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function FilesPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-6">
          <Skeleton className="h-8 w-32" />
          <Card>
            <CardContent className="p-6">
              <div className="space-y-4">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
              </div>
            </CardContent>
          </Card>
        </div>
      }
    >
      <FilesView />
    </Suspense>
  );
}
