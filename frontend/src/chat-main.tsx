import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import ChatApp from "./ChatApp";
import "./styles.css";
import "./chat.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ChatApp />
  </StrictMode>,
);
