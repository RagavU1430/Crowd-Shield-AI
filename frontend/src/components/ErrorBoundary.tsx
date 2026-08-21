import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode; onReset?: () => void };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("CROWD-SHIELD dashboard error", error, info.componentStack);
  }

  private reset = () => {
    this.setState({ error: null });
    this.props.onReset?.();
  };

  render() {
    if (!this.state.error) return this.props.children;
    return <section className="recovery-panel" role="alert">
      <p className="eyebrow">SAFE RECOVERY</p>
      <h2>The dashboard could not display this analysis result.</h2>
      <p>{this.state.error.message}</p>
      <button onClick={this.reset}>RETURN TO UPLOAD</button>
    </section>;
  }
}
