export default function JobsPage() {
  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-semibold">Jobs</h1>
      <div className="rounded-md border p-4 text-sm text-gray-600">
        Danh sách jobs chưa có do Backend không cung cấp endpoint liệt kê. Bạn có thể truy cập trực tiếp một job qua URL /jobs/[task_id].
      </div>
    </div>
  )
}

