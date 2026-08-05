import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import LibrarianApp from "./LibrarianApp";
import "./styles.css";
import "./chat.css";
import "./librarian.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <LibrarianApp />
  </StrictMode>,
);
