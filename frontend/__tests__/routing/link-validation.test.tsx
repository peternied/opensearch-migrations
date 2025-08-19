import { render, screen } from "@testing-library/react";
import { useRouter, useSearchParams } from "next/navigation";

// Mock Next.js navigation hooks
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

import AboutPage from "@/app/about/page";
import ViewSessionPage from "@/app/viewSession/page";
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

describe("Link Validation Tests", () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
    mockSearchParams.get.mockReturnValue(null);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("External Links", () => {
    it("should have correct GitHub repository link", () => {
      render(<AboutPage />);
      const repoLink = screen.getByText("opensearch-project/opensearch-migration");
      expect(repoLink.closest("a")).toHaveAttribute(
        "href",
        "https://github.com/opensearch-project/opensearch-migrations",
      );
    });

    it("should have working external links in about page", () => {
      render(<AboutPage />);
      const links = screen.getAllByRole("link");
      
      // Should have multiple external links
      expect(links.length).toBeGreaterThan(1);
      
      // Check that GitHub links are present
      const githubLinks = links.filter(link => 
        link.getAttribute("href")?.includes("github.com")
      );
      expect(githubLinks.length).toBeGreaterThan(0);
    });
  });

  describe("Parameter Handling", () => {
    describe("ViewSession Page", () => {
      it("should handle missing sessionName parameter gracefully", () => {
        mockSearchParams.get.mockReturnValue(null);
        
        render(<ViewSessionPage />);
        expect(screen.getByText("Migration Session - ")).toBeInTheDocument();
      });

      it("should display sessionName when provided", () => {
        mockSearchParams.get.mockImplementation((key: string) =>
          key === "sessionName" ? "production-migration" : null,
        );
        
        render(<ViewSessionPage />);
        expect(
          screen.getByText("Migration Session - production-migration"),
        ).toBeInTheDocument();
      });

      it("should handle special characters in sessionName", () => {
        mockSearchParams.get.mockImplementation((key: string) =>
          key === "sessionName" ? "test-session_123" : null,
        );
        
        render(<ViewSessionPage />);
        expect(
          screen.getByText("Migration Session - test-session_123"),
        ).toBeInTheDocument();
      });
    });

    describe("Wizard Page", () => {
      it("should show default message when no sessionName", () => {
        mockSearchParams.get.mockReturnValue(null);
        
        render(<WizardPage />);
        expect(
          screen.getByText("Session: No session specified"),
        ).toBeInTheDocument();
      });

      it("should display sessionName in multiple places", () => {
        mockSearchParams.get.mockImplementation((key: string) =>
          key === "sessionName" ? "integration-test" : null,
        );
        
        render(<WizardPage />);
        expect(
          screen.getByText("Session: integration-test"),
        ).toBeInTheDocument();
        expect(
          screen.getByText(/Selected session:.*integration-test/),
        ).toBeInTheDocument();
      });

      it("should handle empty sessionName parameter", () => {
        mockSearchParams.get.mockImplementation((key: string) =>
          key === "sessionName" ? "" : null,
        );
        
        render(<WizardPage />);
        expect(
          screen.getByText("Session: No session specified"),
        ).toBeInTheDocument();
      });

      it("should not show selected session section when no sessionName", () => {
        mockSearchParams.get.mockReturnValue(null);
        
        render(<WizardPage />);
        
        // Should not show the "Selected session:" text
        expect(screen.queryByText(/Selected session:/)).not.toBeInTheDocument();
      });
    });
  });

  describe("URL Parameter Edge Cases", () => {
    it("should handle null parameter values", () => {
      mockSearchParams.get.mockReturnValue(null);
      
      expect(() => render(<ViewSessionPage />)).not.toThrow();
      expect(() => render(<WizardPage />)).not.toThrow();
    });

    it("should handle undefined parameter values", () => {
      mockSearchParams.get.mockReturnValue(undefined);
      
      expect(() => render(<ViewSessionPage />)).not.toThrow();
      expect(() => render(<WizardPage />)).not.toThrow();
    });

    it("should handle very long session names", () => {
      const longSessionName = "a".repeat(100);
      mockSearchParams.get.mockImplementation((key: string) =>
        key === "sessionName" ? longSessionName : null,
      );
      
      render(<ViewSessionPage />);
      expect(
        screen.getByText(`Migration Session - ${longSessionName}`),
      ).toBeInTheDocument();
    });
  });
});
