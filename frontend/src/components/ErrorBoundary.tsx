import { Component, type ReactNode, type ErrorInfo } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  err: Error | null;
  info: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { err: null, info: null };

  static getDerivedStateFromError(err: Error): State {
    return { err, info: null };
  }

  componentDidCatch(err: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", err, info);
    this.setState({ err, info });
  }

  render() {
    if (!this.state.err) return this.props.children;
    return (
      <div
        style={{
          padding: 24,
          color: "#fecaca",
          background: "#1a1010",
          minHeight: "100vh",
          fontFamily: "JetBrains Mono, monospace",
          fontSize: 13,
          lineHeight: 1.6,
        }}
      >
        <h2 style={{ color: "#fca5a5", fontSize: 16, marginTop: 0 }}>
          💥 React a planté
        </h2>
        <pre
          style={{
            background: "#0e0808",
            padding: 14,
            borderRadius: 8,
            overflow: "auto",
            border: "1px solid #4a1f1f",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {String(this.state.err.message)}
          {"\n\n"}
          {String(this.state.err.stack)}
          {this.state.info?.componentStack && (
            <>
              {"\n\nComponent stack:\n"}
              {this.state.info.componentStack}
            </>
          )}
        </pre>
        <button
          style={{
            marginTop: 14,
            padding: "8px 14px",
            background: "#7f1d1d",
            color: "#fff",
            border: "1px solid #b91c1c",
            borderRadius: 6,
            cursor: "pointer",
            fontFamily: "inherit",
          }}
          onClick={() => location.reload()}
        >
          Recharger
        </button>
      </div>
    );
  }
}
