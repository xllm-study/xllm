import { Outlet } from "react-router";
import { CommandMenu } from "./CommandMenu";

export function CommandMenuWrapper() {
  return (
    <>
      <Outlet />
      <CommandMenu />
    </>
  );
}
