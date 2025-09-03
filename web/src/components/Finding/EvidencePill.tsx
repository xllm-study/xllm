import {
  ChevronRightIcon,
  Cross1Icon,
  FileTextIcon,
} from "@radix-ui/react-icons";
import { DataList, ScrollArea, Text, VisuallyHidden } from "@radix-ui/themes";
import { Dialog } from "radix-ui";
import { useMemo } from "react";
import { type Evidence } from "../../utils/data";
import s from "./Finding.module.scss";

export function EvidencePill({
  evidence,
  compact = false,
}: {
  evidence: Evidence;
  compact?: boolean;
}) {
  const highlightTextHtml = useMemo(() => {
    if (!evidence.citation) return evidence.source_note.text;
    const highlightedText = highlightSearchTerms(
      evidence.source_note.text,
      evidence.citation,
      "bg-[#75FF5285] text-[#003D00] px-1 py-1",
    );
    return highlightedText;
  }, [evidence.source_note.text, evidence.value]);

  const splitDate = evidence.source_note.date.split("-");
  const shortDate = splitDate[1] + "/" + splitDate[2];

  return (
    <Dialog.Root>
      <Dialog.Trigger
        asChild
        onClick={(e) => console.log("clicked", evidence.source_note_id)}
      >
        <div className={s.evidencePill}>
          {compact ? (
            <>{shortDate}</>
          ) : (
            <>
              <FileTextIcon />
              <div className={s.divider} />
              {evidence.source_note.date}
              <div className={s.divider} />
              <ChevronRightIcon />
            </>
          )}
        </div>
      </Dialog.Trigger>
      <Dialog.Portal container={document.getElementById("portalcontainer")}>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 data-[state=open]:animate-overlayShow" />
        <Dialog.Content className="flex flex-col fixed right-0 top-0 w-[90vw] max-w-[1000px] h-full rounded-l-md bg-white p-[25px] shadow-[var(--shadow-6)] focus:outline-none animate-slideIn">
          <VisuallyHidden>
            <Dialog.Title className="m-0 text-[17px] font-medium text-mauve12">
              View Note
            </Dialog.Title>
          </VisuallyHidden>

          <DataList.Root>
            <DataList.Item>
              <DataList.Label minWidth="88px">Note Date</DataList.Label>
              <DataList.Value>
                {new Date(
                  Date.parse(evidence.source_note.date),
                ).toLocaleDateString("en-US")}
              </DataList.Value>
            </DataList.Item>
          </DataList.Root>
          <ScrollArea
            className="flex-1 mt-4 pr-4"
            scrollbars="vertical"
            type="auto"
            size={"1"}
          >
            <Text size={"3"}>
              <div
                className="whitespace-pre-line"
                dangerouslySetInnerHTML={{ __html: highlightTextHtml }}
              />
            </Text>
          </ScrollArea>

          <Dialog.Close asChild>
            <button
              className="absolute right-2.5 top-2.5 inline-flex size-[25px] appearance-none items-center justify-center rounded-full text-violet11 bg-gray3 hover:bg-violet4 focus:shadow-[0_0_0_2px] focus:shadow-violet7 focus:outline-none"
              aria-label="Close"
            >
              <Cross1Icon />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function highlightSearchTerms(
  sourceString: string,
  searchString: string,
  highlightClass = "highlight",
) {
  // Return the source string as is if either parameter is invalid
  if (!sourceString || !searchString || searchString === "") {
    console.warn(
      "Invalid parameters provided to highlightSearchTerms function.",
    );
    return sourceString;
  }

  // Escape special characters in the search string for use in a regular expression
  const escapedSearchString = searchString.replace(
    /[.*+?^${}()|[\]\\]/g,
    "\\$&",
  );

  // log parameters as table
  // console.table({
  //   sourceString,
  //   searchString,
  // });

  // Create a regular expression to find all occurrences of the search string (case-insensitive)
  const regex = new RegExp(escapedSearchString, "gi");

  // Replace all occurrences with the highlighted version
  return sourceString.replace(regex, (match) => {
    return `<span class="${highlightClass}">${match}</span>`;
  });
}
