"use client";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { CreateWatcherRequest } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

const schema = z
  .object({
    room_id: z.string().trim().optional().nullable(),
    url: z.string().trim().url().optional().nullable(),
    poll_interval: z.coerce.number().int().min(10).default(60),
    proxy: z.string().trim().optional().nullable(),
    cookies: z.string().trim().optional().nullable(),
  })
  .refine((d) => (d.room_id && !d.url) || (d.url && !d.room_id), {
    message: "Cần nhập room_id hoặc url (chỉ một trong hai)",
    path: ["room_id"],
  });

type FormData = z.infer<typeof schema>;

export default function WatchersPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [deleteKey, setDeleteKey] = useState("");

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { poll_interval: 60 },
  });

  const createMutation = useMutation({
    mutationFn: async (payload: CreateWatcherRequest) => {
      const result = await api.watchers.create(payload);
      return result;
    },
    onSuccess: () => {
      toast({
        title: "Watcher created successfully",
        description: "The watcher has been added and will start monitoring.",
      });
      reset({
        room_id: "",
        url: "",
        poll_interval: 60,
        proxy: "",
        cookies: "",
      });
      // Invalidate any watcher-related queries
      queryClient.invalidateQueries({ queryKey: ["watchers"] });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create watcher",
        description:
          error?.error_message || error?.message || "Unknown error occurred",
        variant: "destructive",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (key: string) => {
      return await api.watchers.delete(key);
    },
    onSuccess: () => {
      toast({ title: "Watcher deleted successfully" });
      setDeleteKey("");
      queryClient.invalidateQueries({ queryKey: ["watchers"] });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to delete watcher",
        description:
          error?.error_message || error?.message || "Unknown error occurred",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (values: FormData) => {
    const payload: CreateWatcherRequest = {
      room_id: values.room_id || undefined,
      url: values.url || undefined,
      poll_interval: values.poll_interval,
    };
    createMutation.mutate(payload);
  };

  const handleDelete = () => {
    if (deleteKey.trim()) {
      deleteMutation.mutate(deleteKey.trim());
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <h1 className="text-2xl font-semibold">Watchers</h1>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Create Watcher
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="room_id">Room ID</Label>
                <Input
                  id="room_id"
                  placeholder="Enter room ID"
                  {...register("room_id")}
                />
                {errors.room_id && (
                  <p className="text-sm text-destructive mt-1">
                    {errors.room_id.message}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="url">URL</Label>
                <Input
                  id="url"
                  placeholder="Enter TikTok live URL"
                  {...register("url")}
                />
                {errors.url && (
                  <p className="text-sm text-destructive mt-1">
                    {errors.url.message}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="poll_interval">Poll Interval (seconds)</Label>
                <Input
                  id="poll_interval"
                  type="number"
                  min="10"
                  {...register("poll_interval", { valueAsNumber: true })}
                />
                {errors.poll_interval && (
                  <p className="text-sm text-destructive mt-1">
                    {errors.poll_interval.message}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="proxy">Proxy (optional)</Label>
                <Input
                  id="proxy"
                  placeholder="http://proxy:port"
                  {...register("proxy")}
                />
              </div>

              <div className="md:col-span-2">
                <Label htmlFor="cookies">Cookies Path (optional)</Label>
                <Input
                  id="cookies"
                  placeholder="/path/to/cookies.json"
                  {...register("cookies")}
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={createMutation.isPending}
              className="w-full md:w-auto"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating Watcher...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Watcher
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trash2 className="h-5 w-5" />
            Delete Watcher
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="delete_key">Watcher Key (room_id or url)</Label>
            <div className="flex gap-2">
              <Input
                id="delete_key"
                placeholder="Enter room_id or url to delete"
                value={deleteKey}
                onChange={(e) => setDeleteKey(e.target.value)}
                className="flex-1"
              />
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={!deleteKey.trim() || deleteMutation.isPending}
              >
                {deleteMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          <Alert>
            <AlertDescription>
              <strong>Note:</strong> The backend currently doesn't provide an
              API to list watchers, so you need to manually enter the room_id or
              url that was used to create the watcher.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  );
}
