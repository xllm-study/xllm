import { Outlet, ScrollRestoration } from "react-router";
import s from "./Layout.module.scss";
import { TopNav } from "./TopNav";
import { CommandMenu } from "../CommandMenu/CommandMenu";
import { InitialStateProvider } from "../../state/InitialStateProvider";

export function StudyContext() {
  return (
    <InitialStateProvider>
      <ScrollRestoration />

      <TopNav />
      <main className={s.main}>
        <Outlet />
      </main>
      <CommandMenu />
    </InitialStateProvider>
  );
}
