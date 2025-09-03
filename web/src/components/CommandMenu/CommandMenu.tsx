import { DialogDescription, DialogTitle } from "@radix-ui/react-dialog";
import {
  ArrowLeftIcon,
  DownloadIcon,
  HomeIcon,
  InputIcon,
  KeyboardIcon,
  ListBulletIcon,
  Pencil1Icon,
  PersonIcon,
  ResetIcon,
} from "@radix-ui/react-icons";
import { ScrollArea, Spinner } from "@radix-ui/themes";
import { useQuery } from "@tanstack/react-query";
import { Command } from "cmdk";
import { customAlphabet } from "nanoid";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import {
  downloadJSON,
  exportToJSON,
  usePatientsState,
} from "../../state/patientsStore";
import { trpc } from "../../utils/trpc";
import "./CommandMenu.scss"; // Ensure you have the styles for cmdk

export const CommandMenu = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [submenu, setSubmenu] = useState<"events" | "patients">();
  const patients = usePatientsState((s) => s.patientValues);
  const resetState = usePatientsState((s) => s.resetState);
  const acceptValue = usePatientsState((s) => s.acceptValue);
  const [searchString, setSearchString] = useState("");
  const { mrn } = useParams();

  const eventsQuery = useQuery(
    trpc.listEvents.queryOptions(undefined, {
      enabled: submenu === "events",
    }),
  );

  const handleExport = () => {
    downloadJSON(JSON.stringify(usePatientsState.getState().patientValues));
    setOpen(false);
  };

  // Toggle the menu when ⌘K is pressed
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const handleAcceptAllValues = () => {
    console.log("Accepting all values");
    Object.entries(patients).forEach(([mrn, patient]) => {
      console.log("Accepting all values for", mrn);
      Object.entries(patient.findings).forEach(([varID]) => {
        console.log("Accepting value for", mrn, varID);
        acceptValue(mrn, varID);
      });
    });
    setOpen(false);
  };

  const acceptAllForCurrentPatient = async () => {
    if (!mrn) return;

    const patient = patients[mrn];
    if (!patient) return;

    const findings = Object.entries(patient.findings);

    // iterate over each finding, but wait 10ms between each:
    for (const [varID] of findings) {
      await new Promise((resolve) => setTimeout(resolve, 10));
      acceptValue(mrn, varID);
    }
  };

  return (
    <Command.Dialog
      open={open}
      onOpenChange={(o) => {
        setSubmenu(undefined);
        if (submenu === undefined) {
          setOpen(o);
        }
      }}
      onKeyDown={(e) => {
        // Escape goes to previous page
        // Backspace goes to previous page when search is empty
        if (e.key === "Backspace" && !searchString) {
          e.preventDefault();
          setSubmenu(undefined);
        }
      }}
      label="Global Command Menu"
      container={document.getElementById("portalcontainer")!}
    >
      <DialogTitle hidden={true}></DialogTitle>
      <DialogDescription hidden={true}></DialogDescription>
      <Command.Input
        value={searchString}
        onValueChange={setSearchString}
        hidden={submenu == "events"}
        placeholder="Type a command or search..."
      />
      <Command.List>
        {submenu === undefined && (
          <>
            <Command.Empty>No results found.</Command.Empty>
            <Command.Item
              onSelect={() => {
                navigate("/patient");
              }}
            >
              <InputIcon height={16} width={16} /> Manual Labeling
            </Command.Item>
            <Command.Item
              onSelect={() => {
                const alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
                const nanoid = customAlphabet(alphabet, 7);
                const key = nanoid();

                navigator.clipboard.writeText(key).then(() => {
                  setOpen(false);
                });
              }}
            >
              <KeyboardIcon height={16} width={16} /> Generate Participant Token
            </Command.Item>
            <Command.Item
              onSelect={() => {
                navigate("/");
                setOpen(false);
              }}
            >
              <HomeIcon height={16} width={16} /> Home
            </Command.Item>
            <Command.Item onSelect={() => setSubmenu("events")}>
              <ListBulletIcon height={16} width={16} /> Show Events...
            </Command.Item>
            <Command.Item onSelect={handleExport}>
              <DownloadIcon height={16} width={16} /> Export Data
            </Command.Item>
            <Command.Item
              onSelect={() => {
                setSubmenu("patients");
                setSearchString("");
              }}
            >
              <PersonIcon height={16} width={16} /> Go to Patient...
            </Command.Item>
            <Command.Item
              onSelect={() => {
                resetState();
              }}
            >
              <ResetIcon height={16} width={16} /> Reset State
            </Command.Item>

            <Command.Item onSelect={handleAcceptAllValues}>
              <Pencil1Icon height={16} width={16} /> Accept all Values
            </Command.Item>

            <Command.Item onSelect={acceptAllForCurrentPatient}>
              <Pencil1Icon height={16} width={16} /> Accept Values for Current Patient ({mrn})
            </Command.Item>
          </>
        )}

        {submenu === "patients" &&
          Object.keys(patients).map((mrn) => (
            <Command.Item
              key={mrn}
              onSelect={() => navigate("/patient/" + mrn)}
            >
              {mrn}
            </Command.Item>
          ))}
      </Command.List>

      {submenu == "events" && (
        <>
          <button
            className="p-4 flex items-center gap-2 text-xs text-gray-600 hover:bg-[#f8f8f8] w-full cursor-pointer"
            onClick={() => setSubmenu(undefined)}
          >
            <ArrowLeftIcon height={16} width={16} />
            Back
          </button>
          <ScrollArea
            className="p-4 pt-0 font-mono text-sm"
            type="auto"
            scrollbars="vertical"
            style={{ height: 280 }}
          >
            {eventsQuery.isLoading && <Spinner />}
            {eventsQuery.data && eventsQuery.data.length === 0 && (
              <div className="text-gray-500">No events found.</div>
            )}
            {eventsQuery.data &&
              eventsQuery.data.map((e) => (
                <div key={e.id}>
                  <span className="text-gray-400">{e.timestamp}</span> <span />{" "}
                  {e.type}
                </div>
              ))}
          </ScrollArea>
        </>
      )}
    </Command.Dialog>
  );
};
