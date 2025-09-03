import { Theme } from "@radix-ui/themes";
import "@radix-ui/themes/styles.css";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider, ScrollRestoration } from "react-router";
import LoginScreen from "./LoginScreen.tsx";
import { StudyContext } from "./components/Layout/Layout.tsx";
import { Patient } from "./components/Patient/Patient.tsx";
import "./index.css";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./utils/trpc.ts";
import { CommandMenuWrapper } from "./components/CommandMenu/CommandMenuWrapper.tsx";
import { XLLM_TEXT_LOGO } from "./utils/logo.tsx";
import { CompletePage } from "./pages/complete/complete.tsx";

const router = createBrowserRouter(
  [
    {
      path: "/",
      Component: CommandMenuWrapper,
      children: [
        {
          index: true,
          Component: LoginScreen,
          
        },
      ],
    },
    {
      Component: StudyContext,
      path: "/patient",
      children: [
        {
          index: true,
          element: <p>:)</p>,
        },
        {
          path: ":mrn",
          Component: Patient,
        },
      ],
    },
    {
      path: "/complete",
      Component: CommandMenuWrapper,
      children: [
        {
          index: true,
          Component: CompletePage,
        },
      ],
    },
  ],
  {},
);

console.log(XLLM_TEXT_LOGO);

createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <Theme hasBackground={false} accentColor="gray">
      <RouterProvider router={router}  />
      <div id="portalcontainer"></div>
    </Theme>
  </QueryClientProvider>,
);
