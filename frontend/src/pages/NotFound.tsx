import { useLocation } from "react-router-dom";
import { useEffect } from "react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="border border-border bg-card px-8 py-10 text-center">
        <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-muted-foreground">Route miss</p>
        <h1 className="mt-3 text-4xl font-bold">404</h1>
        <p className="mt-3 text-sm text-muted-foreground">The requested frontend route does not exist.</p>
        <a
          href="/"
          className="mt-5 inline-flex border border-border bg-background px-4 py-2 font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground hover:text-foreground"
        >
          Return to protocols
        </a>
      </div>
    </div>
  );
};

export default NotFound;
