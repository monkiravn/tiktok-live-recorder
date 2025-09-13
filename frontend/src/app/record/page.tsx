"use client";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { api, type CreateRecordingRequest } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Play, Loader2 } from "lucide-react";

const schema = z
  .object({
    room_id: z.string().trim().optional().nullable(),
    url: z.string().trim().url().optional().nullable(),
    duration: z.coerce.number().int().min(1).optional().nullable(),
    proxy: z.string().trim().optional().nullable(),
    cookies: z.string().trim().optional().nullable(),
  })
  .refine((d) => (d.room_id && !d.url) || (d.url && !d.room_id), {
    message: "Cần nhập room_id hoặc url (chỉ một trong hai)",
    path: ["room_id"],
  });

type FormData = z.infer<typeof schema>;

export default function RecordNowPage() {
  const router = useRouter();
  const { toast } = useToast();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const recordMutation = useMutation({
    mutationFn: async (payload: CreateRecordingRequest) => {
      return await api.createRecording(payload);
    },
    onSuccess: (result) => {
      toast({
        title: "Recording started successfully",
        description: `Job ${result.task_id.slice(0, 8)}... has been created`,
      });
      router.push(`/jobs/${result.task_id}`);
    },
    onError: (error: any) => {
      toast({
        title: "Failed to start recording",
        description:
          error?.error_message || error?.message || "Unknown error occurred",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (values: FormData) => {
    const payload: CreateRecordingRequest = {
      room_id: values.room_id || undefined,
      url: values.url || undefined,
      duration: values.duration || undefined,
      options: {
        proxy: values.proxy || undefined,
        cookies: values.cookies || undefined,
      },
    };
    recordMutation.mutate(payload);
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold">Record Now</h1>
        <p className="text-muted-foreground">
          Start a new TikTok live recording. You can monitor the job status
          after submission.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Recording Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <Label htmlFor="room_id">Room ID</Label>
                <Input
                  id="room_id"
                  placeholder="123456789"
                  {...register("room_id")}
                />
                {errors.room_id && (
                  <p className="text-sm text-destructive mt-1">
                    {errors.room_id.message}
                  </p>
                )}
              </div>

              <div className="md:col-span-2">
                <Label htmlFor="url">URL (Alternative to Room ID)</Label>
                <Input
                  id="url"
                  placeholder="https://www.tiktok.com/@user/live"
                  {...register("url")}
                />
                {errors.url && (
                  <p className="text-sm text-destructive mt-1">
                    {errors.url.message}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="duration">Duration (seconds)</Label>
                <Input
                  id="duration"
                  type="number"
                  placeholder="1800"
                  {...register("duration", { valueAsNumber: true })}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Leave empty for unlimited duration
                </p>
                {errors.duration && (
                  <p className="text-sm text-destructive mt-1">
                    {errors.duration.message}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="proxy">Proxy (optional)</Label>
                <Input
                  id="proxy"
                  placeholder="http://user:pass@host:port"
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
                <p className="text-xs text-muted-foreground mt-1">
                  Path to cookies file for authenticated requests
                </p>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="submit"
                disabled={recordMutation.isPending}
                className="flex-1 md:flex-none"
              >
                {recordMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Starting Recording...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Start Recording
                  </>
                )}
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={() => router.push("/jobs")}
              >
                View Jobs
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
