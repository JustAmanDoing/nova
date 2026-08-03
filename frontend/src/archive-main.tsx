import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import ProjectArchiveApp from "./ProjectArchiveApp";
import "./archive.css";
import "./chat.css";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ProjectArchiveApp />
  </StrictMode>,
);
