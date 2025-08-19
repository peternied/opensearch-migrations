import { render, screen } from "@testing-library/react";
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

// Import pages after mocking
import HomePage from "@/app/page";
import LoadingPage from "@/app/loading/page";
import CreateSessionPage from "@/app/createSession/page";
import ViewSessionPage from "@/app/viewSession/page";
import AboutPage from "@/app/about/page";
import PlaygroundPage from "@/app/playground/page";
import WizardPage from "@/app/wizard/page";

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

describe("Route Accessibility Tests", () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
    mockSearchParams.get.mockReturnValue(null);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Home Page (/)", () => {
    it("should render without errors", () => {
      render(<HomePage />);
      expect(
        screen.getByText("Welcome to Migration Assistant"),
      ).toBeInTheDocument();
    });
  });

  describe("Loading Page (/loading)", () => {
    it("should render without errors", () => {
      render(<LoadingPage />);
      expect(
        screen.getByText("OpenSearch Migration Assistant"),
      ).toBeInTheDocument();
    });

    it("should show start migration wizard button when ready", () => {
      render(<LoadingPage />);
      expect(screen.getByTestId("start-migration-button")).toBeInTheDocument();
    });
  });

  describe("Create Session Page (/createSession)", () => {
    it("should render without errors", () => {
      render(<CreateSessionPage />);
      expect(screen.getByText("Create Migration Session")).toBeInTheDocument();
      expect(screen.getByTestId("create-session-button")).toBeInTheDocument();
    });
  });

  describe("View Session Page (/viewSession)", () => {
    it("should render without errors", () => {
      render(<ViewSessionPage />);
      expect(screen.getByText(/Migration Session/)).toBeInTheDocument();
    });

    it("should display session name from query parameters", () => {
      mockSearchParams.get.mockImplementation((key: string) =>
        key === "sessionName" ? "test-session" : null,
      );

      render(<ViewSessionPage />);
      expect(
        screen.getByText("Migration Session - test-session"),
      ).toBeInTheDocument();
    });
  });

  describe("About Page (/about)", () => {
    it("should render without errors", () => {
      render(<AboutPage />);
      expect(screen.getByText("About Migration Assistant")).toBeInTheDocument();
    });

    it("should contain external links", () => {
      render(<AboutPage />);
      const githubLinks = screen.getAllByRole("link");
      expect(githubLinks.length).toBeGreaterThan(0);
    });
  });

  describe("Playground Page (/playground)", () => {
    it("should render without errors", () => {
      render(<PlaygroundPage />);
      expect(screen.getByText("Transformation Playground")).toBeInTheDocument();
    });
  });

  describe("Wizard Page (/wizard)", () => {
    it("should render without errors", () => {
      render(<WizardPage />);
      expect(screen.getByText("Migration Wizard")).toBeInTheDocument();
    });

    it("should display 'No session specified' when no sessionName provided", () => {
      mockSearchParams.get.mockReturnValue(null);

      render(<WizardPage />);
      expect(
        screen.getByText("Session: No session specified"),
      ).toBeInTheDocument();
    });

    it("should display session name from query parameters", () => {
      mockSearchParams.get.mockImplementation((key: string) =>
        key === "sessionName" ? "my-test-session" : null,
      );

      render(<WizardPage />);
      expect(screen.getByText("Session: my-test-session")).toBeInTheDocument();
      expect(
        screen.getByText(/Selected session:.*my-test-session/),
      ).toBeInTheDocument();
    });

    it("should show coming soon message", () => {
      render(<WizardPage />);
      expect(screen.getByText(/Coming Soon:/)).toBeInTheDocument();
      expect(
        screen.getByText(/currently under development/),
      ).toBeInTheDocument();
    });
  });
});
