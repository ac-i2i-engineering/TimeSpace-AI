import { useState, useEffect } from "react";

interface SSEData<T> {
   data: T | null;
   error: Error | null;
   setQuery: React.Dispatch<React.SetStateAction<string>>;
}

function useSSE<T>(url: string): SSEData<T> {
   const [data, setData] = useState<T | null>(null);
   const [error, setError] = useState<Error | null>(null);
   const [query, setQuery] = useState<string>(url);

   useEffect(() => {
      const eventSource = new EventSource(query);

      eventSource.onmessage = (event) => setData(event.data);

      eventSource.onerror = (err) => eventSource.close();

      return () => eventSource.close();
   }, [query]);

   return { data, error, setQuery };
}

export default useSSE;
