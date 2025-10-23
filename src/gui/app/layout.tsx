export const metadata = { title: "Temporal Order Demo" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "ui-sans-serif, system-ui" }}>
        <div style={{ maxWidth: 980, margin: "32px auto", padding: "0 16px" }}>
          <h1 style={{ margin: "0 0 16px" }}>🛒 Temporal Order Demo</h1>
          <p style={{ color: "#555", marginTop: 0 }}>
            Start an order and watch each step progress. Works with Temporal or a local simulator.
          </p>
          {children}
        </div>
      </body>
    </html>
  );
}
