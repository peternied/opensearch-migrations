import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useRouter, useSearchParams } from "next/navigation";

// Mock Next.js navigation hooks
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

// Mock the API calls
jest.mock("@/generated/api", () => ({
  systemHealth: jest.fn(),
}));

// Mock site readiness functions
jest.mock("@/lib/site-readiness", () => ({
  getSiteReadiness: jest.fn(),
  setSiteReadiness: jest.fn(),
}));

import LoadingPage from "@/app/loading/page";

const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
  prefetch: jest.fn(),
};

const mockSearchParams = {
  get: jest.fn(),
  getAll: jest.fn(),
  has: jest.fn(),
  keys: jest.fn(),
  values: jest.fn(),
  entries: jest.fn(),
  forEach: jest.fn(),
  toString: jest.fn(),
};

describe("Navigation Flow Tests", () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
    mockSearchParams.get.mockReturnValue(null);
    jest.clearAllMocks();
  });

  describe("Loading Page Navigation", () => {
    it("should navigate to wizard when start migration button is clicked", async () => {
      render(<LoadingPage />);

      const startButton = screen.getByTestId("start-migration-button");
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(mockRouter.push).toHaveBeenCalledWith("/wizard");
      });
    });

    it("should show correct button text", () => {
      render(<LoadingPage />);
      const startButton = screen.getByTestId("start-migration-button");
      expect(startButton).toHaveTextContent("Start migration wizard");
    });
  });

  describe("Router Function Calls", () => {
    it("should call router.push with correct path", () => {
      render(<LoadingPage />);
      const startButton = screen.getByTestId("start-migration-button");

      fireEvent.click(startButton);

      expect(mockRouter.push).toHaveBeenCalledTimes(1);
      expect(mockRouter.push).toHaveBeenCalledWith("/wizard");
    });

    it("should not call other router methods", () => {
      render(<LoadingPage />);
      const startButton = screen.getByTestId("start-migration-button");

      fireEvent.click(startButton);

      expect(mockRouter.replace).not.toHaveBeenCalled();
      expect(mockRouter.back).not.toHaveBeenCalled();
      expect(mockRouter.forward).not.toHaveBeenCalled();
    });
  });

  describe("Button State Management", () => {
    it("should enable button when ready state is true", () => {
      render(<LoadingPage />);
      const startButton = screen.getByTestId("start-migration-button");
      expect(startButton).not.toBeDisabled();
    });

    it("should handle debug command interactions", () => {
      render(<LoadingPage />);

      // Test simulate loaded button
      const simulateLoadedBtn = screen.getByText("Simulate Loaded");
      expect(simulateLoadedBtn).toBeInTheDocument();

      fireEvent.click(simulateLoadedBtn);
      // The button should still be accessible after simulation
      const startButton = screen.getByTestId("start-migration-button");
      expect(startButton).toBeInTheDocument();
    });
  });
});
