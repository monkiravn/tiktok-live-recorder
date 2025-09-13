import "@testing-library/jest-dom";
import { vi, afterEach } from "vitest";

// Mock Next.js router
vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/"),
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  })),
  useSearchParams: vi.fn(() => new URLSearchParams()),
}));

// Mock fetch globally
global.fetch = vi.fn();

// Setup cleanup after each test
import { cleanup } from "@testing-library/react";
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
