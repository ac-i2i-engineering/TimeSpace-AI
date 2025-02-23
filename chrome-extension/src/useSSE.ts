import { useState, useEffect } from "react";

interface SSEData<T> {
   data: T | null;
   error: Error | null;
}

function useSSE<T>(url: string): SSEData<T> {
   const [data, setData] = useState<T | null>(null);
   const [error, setError] = useState<Error | null>(null);

   useEffect(() => {
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => setData(event.data);

      eventSource.onerror = (err) => eventSource.close();

      return () => eventSource.close();
   }, [url]);

   return { data, error };
}

export default useSSE;
