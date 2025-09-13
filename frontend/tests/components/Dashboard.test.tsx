import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import DashboardPage from "@/app/page";

// Mock the API
vi.mock("@/lib/api", () => ({
  api: {
    healthz: vi.fn(() => Promise.resolve("ok")),
    ready: vi.fn(() => Promise.resolve("ready")),
  },
}));

// Create a test wrapper with QueryClient
function createWrapper() {
  const testQueryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
      },
    },
  });

  return function TestWrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={testQueryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe("Dashboard Page", () => {
  it("renders dashboard title", async () => {
    const Wrapper = createWrapper();

    render(<DashboardPage />, { wrapper: Wrapper });

    expect(
      screen.getByRole("heading", { name: /dashboard/i })
    ).toBeInTheDocument();
  });

  it("shows health status chips", async () => {
    const Wrapper = createWrapper();

    render(<DashboardPage />, { wrapper: Wrapper });

    // Wait for the health checks to complete
    await waitFor(() => {
      expect(screen.getByText(/API:/)).toBeInTheDocument();
      expect(screen.getByText(/Workers:/)).toBeInTheDocument();
    });
  });

  it("shows metric cards", () => {
    const Wrapper = createWrapper();

    render(<DashboardPage />, { wrapper: Wrapper });

    expect(screen.getByText("Active Watchers")).toBeInTheDocument();
    expect(screen.getByText("Running Jobs")).toBeInTheDocument();
    expect(screen.getByText("Success 24h")).toBeInTheDocument();
    expect(screen.getByText("Failures 24h")).toBeInTheDocument();
  });
});
