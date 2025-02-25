import { useState } from "react";
/* import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg"; */
import "./App.css";
import Input from "./Input";
import { theme, ThemeProvider } from "./theme";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import useSSE from "./useSSE";

const queryClient = new QueryClient();

const App = () => (
   <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
         <Chat />
      </ThemeProvider>
   </QueryClientProvider>
);

const Chat = () => {
   const URL = "http://127.0.0.1:8000/stream?";

   const { data, error, setQuery } = useSSE<string>(URL);

   const messageToQuery = (message: string) => {
      let params = new URLSearchParams();
      params.append("message", message);
      setQuery(URL + params);
   };

   return (
      <>
         <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <h1 className="header transition" style={{ fontSize: data ? "2rem" : "auto" }}>
               TimeSpace
            </h1>
            <img src="timespace_logo.png" className="transition" style={{ height: data ? "3rem" : "4rem" }}></img>
         </div>
         <div style={{ flex: data ? 1 : 0 }} className="messages">
            <span style={{ opacity: data ? 1 : 0, maxHeight: data ? "999px" : 0 }} className="fade-in">
               {data}
            </span>
         </div>
         <Input onSend={messageToQuery} />
      </>
   );
};

export default App;
