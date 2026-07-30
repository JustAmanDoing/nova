import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import FocusApp from "./FocusApp";
import "./styles.css";
import "./chat.css";
import "./focus.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <FocusApp />
  </StrictMode>,
);
