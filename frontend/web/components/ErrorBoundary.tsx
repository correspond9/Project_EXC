"use client";

import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  section?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Sprint 10 — Error boundary wrapping major page sections.
 * Catches render errors and displays a user-friendly fallback instead of
 * crashing the entire page.
 */
export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In production you would send this to an error tracking service
    console.error(`[ErrorBoundary${this.props.section ? ` — ${this.props.section}` : ""}]`, error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div
          role="alert"
          aria-live="assertive"
          className="card"
          style={{
            padding: 24,
            textAlign: "center",
            border: "1px solid var(--accent-red)",
          }}
        >
          <p style={{ color: "var(--accent-red)", fontWeight: 600, marginBottom: 8 }}>
            Something went wrong{this.props.section ? ` in ${this.props.section}` : ""}.
          </p>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: 16 }}>
            {this.state.error?.message ?? "An unexpected error occurred."}
          </p>
          <button
            onClick={this.handleReset}
            aria-label="Retry loading this section"
            style={{
              padding: "6px 16px",
              borderRadius: 6,
              background: "var(--accent-blue)",
              color: "#fff",
              border: "none",
              cursor: "pointer",
              fontSize: "0.85rem",
            }}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
