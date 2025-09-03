import { CheckIcon, ListBulletIcon, ResetIcon } from "@radix-ui/react-icons";
import { Flex, ScrollArea, Select, Tooltip } from "@radix-ui/themes";
import { useCallback, useLayoutEffect, useMemo, useState } from "react";
import { useParams } from "react-router";
import { Finding, VariableValue } from "../../../shared/types";
import { TimelineIcon } from "../../assets/TimelineIcon";
import { Evidence, evidenceValueToString } from "../../utils/data";
import { useData } from "../../utils/queries";
import { useTrackEvent } from "../../utils/trackEvent";
import { EvidencePill } from "./EvidencePill";
import s from "./Finding.module.scss";
import { Input } from "./Input";

const FINDING_VIEW_MODES = {
  timeline: { label: "Timeline View", icon: <TimelineIcon /> },
  list: { label: "List View", icon: <ListBulletIcon /> },
} as const;

type FindingViewMode = keyof typeof FINDING_VIEW_MODES;

export function FindingElement({
  finding,
  accepted,
  acceptValue,
  correctedValue,
  setCorrectedValue,
  resetValue,
}: {
  finding: Finding;
  accepted: boolean;
  acceptValue: () => void;
  correctedValue?: VariableValue;
  setCorrectedValue: (value: VariableValue) => void;
  resetValue: () => void;
}) {
  const dataQuery = useData();
  const trackEvent = useTrackEvent();
  const { variableDefs } = dataQuery.data ?? {};
  const [viewMode, setViewMode] = useState<FindingViewMode>("timeline");
  const value = correctedValue === undefined ? finding.value : correctedValue;
  const modified = correctedValue !== undefined;
  if (!variableDefs) return <></>;
  const definition = variableDefs[finding.varId];
  const mrn = useParams().mrn;

  const handleAccept = () => {
    acceptValue();
    trackEvent({
      type: "accept_patient_value",
      meta: {
        patientId: mrn as string,
        variableId: finding.varId,
      },
    });
  };

  return (
    <div className={accepted ? "my-4" : "my-12"}>
      {!accepted && (
        <p style={{ fontWeight: 700, margin: 0 }}>
          <Tooltip content={finding.varId}>
            <span onClick={() => navigator.clipboard.writeText(finding.varId)}>
              {definition.name}
            </span>
          </Tooltip>

          <span className="text-gray-700 font-normal ml-4">
            {definition.description}
          </span>
        </p>
      )}



      <div className={s.value} data-accepted={accepted}>
        {accepted && (
          <div className="flex items-center gap-1 flex-shrink-0 mb-3">
            <Tooltip
              content={
                modified
                  ? "This value has been manually corrected."
                  : "The predicted value has been accepted."
              }
            >
              <div
                className={`h-[12px] w-[12px] rounded-full mr-2 ${modified ? "bg-[#9D6C00]" : "bg-[#008000]"}`}
              />
            </Tooltip>
            <p className={`font-bold`}>{definition.name}</p>
          </div>
        )}

        {accepted && <div style={{ flexGrow: 1 }} />}

        {!accepted && (
          <div className="b-3 pb-3">
            <button className={`${s.btn}`} onClick={handleAccept}>
              <CheckIcon />
            </button>
          </div>
        )}

        <ScrollArea
          dir="ltr"
          scrollbars="horizontal"
          type="auto"
          style={{
            flexShrink: 1,
            paddingBottom: 12,
          }}
        >
          <Input
            definition={definition.type}
            value={value}
            disabled={accepted}
            setCorrectedValue={setCorrectedValue}
          />
        </ScrollArea>

        <div className="flex gap-2 mb-3">

          {(modified || accepted) && (
            <button
              className={s.btn}
              data-variant="secondary"
              onClick={resetValue}
            >
              <ResetIcon />
            </button>
          )}
        </div>

        {/* <ColoredRatio
          coloredText={Math.round(finding.confidence * 100) + "%"}
          label="confident prediction"
          scale={finding.confidence}
          color="color(display-p3 0.2553 0.2553 0.2553)"
        /> */}

        {!accepted && <div style={{ flexGrow: 1 }} />}

        {!accepted && (
          <Select.Root
            value={viewMode}
            onValueChange={(v: FindingViewMode) => setViewMode(v)}
          >
            <Select.Trigger style={{ marginBottom: 12 }}>
              <Flex as="span" align="center" gap="2">
                {FINDING_VIEW_MODES[viewMode].icon}
                {FINDING_VIEW_MODES[viewMode].label}
              </Flex>
            </Select.Trigger>
            <Select.Content position="item-aligned">
              {Object.entries(FINDING_VIEW_MODES).map(([key, { label }]) => (
                <Select.Item value={key} key={key}>
                  {label}
                </Select.Item>
              ))}
            </Select.Content>
          </Select.Root>
        )}
      </div>

      {!accepted && (
        <div className={s.info}>
          {viewMode == "list" ? (
            <EvidenceListView finding={finding} />
          ) : (
            <EvidenceTimelineView finding={finding} />
          )}
        </div>
      )}
    </div>
  );
}

export function EvidenceTimelineView({ finding }: { finding: Finding }) {
  const dataQuery = useData();

  const timelineNotes = useMemo(() => {
    const groupedByYear: { year: string; evidence: Evidence[] }[] = [];
    const uniqueValues = new Map<
      string,
      { originalValue: any; occurences: number }
    >();
    const evidenceByDate = [...finding.evidence].sort((a, b) => {
      if (!a.source_note) return 1;
      if (!b.source_note) return -1;
      return b.source_note.date.localeCompare(a.source_note.date);
    });

    evidenceByDate.forEach((e) => {
      if (!e.source_note) return;
      const year = e.source_note.date.slice(0, 4);
      const stringifiedValue = evidenceValueToString(e.value);

      uniqueValues.set(stringifiedValue, {
        originalValue: e.value,
        occurences: (uniqueValues.get(stringifiedValue)?.occurences || 0) + 1,
      });
      const existingGroup = groupedByYear.find((group) => group.year === year);
      if (existingGroup) {
        existingGroup.evidence.push(e);
      } else {
        groupedByYear.push({ year, evidence: [e] });
      }
    });

    const uniqueValuesArr = Array.from(uniqueValues.entries());

    // maps values to the order(top to bottom) in which they appear in the timeline
    let orderMap: {
      [value: string]: number;
    } = {};

    uniqueValuesArr.forEach((val, i) => {
      orderMap[val[0]] = i;
    });

    return {
      groupedByYear,
      uniqueValues: uniqueValuesArr,
      orderMap,
    };
  }, [finding]);

  const isObjectList = useMemo(() => {
    const def = dataQuery.data?.variableDefs[finding.varId];
    if (!def) return false;

    return def.type.type === "list" && def.type.value.type === "object";
  }, [dataQuery.data?.variableDefs, finding.varId]);

  return (
    <div
      style={
        {
          "--rowHeight": isObjectList ? "70px" : "40px",
          display: "grid",
          gridTemplateColumns: "max-content auto",
        } as React.CSSProperties
      }
    >
      <ScrollArea
        scrollbars="horizontal"
        type="hover"
        style={{ maxWidth: 550 }}
      >
        <div
          className="px-2"
        // ref={measuredRef}
        >
          {timelineNotes.uniqueValues.map(([key, info]) => (
            <FindingValueElement
              key={key}
              value={info.originalValue}
              occurences={info.occurences}
            />
          ))}
        </div>
      </ScrollArea>

      <ScrollArea
        scrollbars="horizontal"
        type="always"
        size={"1"}
        className={s.timelineScrollbar}
      >
        <div className="flex">
          {timelineNotes.groupedByYear.map((group) => (
            <div
              className={`flex flex-col justify-between px-[8px] py-[12px] ${s.timelineYear}`}
              key={group.year}
            >
              <div className="flex gap-[12px]">
                {group.evidence.map((e) => (
                  <div
                    key={e.source_note_id}
                    style={{
                      marginTop: `calc(${timelineNotes.orderMap[
                        e.value ? e.value.toString() : "unknown"
                      ]
                        } * var(--rowHeight))`,
                    }}
                  >
                    <EvidencePill evidence={e} compact />
                  </div>
                ))}
              </div>
              <div className={s.timelineYearLabel}>{group.year}</div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

function FindingValueElement({
  value,
  occurences,
}: {
  value: unknown;
  occurences: number;
}) {
  return (
    <div
      className="flex items-center "
      style={{
        height: "var(--rowHeight)",
        width: "max-content",
      }}
    >
      <FindingValue value={value} />
      <span className="text-[#5E5E5E]">({occurences})</span>
    </div>
  );
}

function FindingValue({
  value,
  isListItem,
}: {
  value: unknown;
  isListItem?: boolean;
}) {
  switch (typeof value) {
    case "string":
      return (
        <div
          className={
            "whitespace-pre" +
            (isListItem ? " px-2 py-1 bg-white rounded-sm" : "")
          }
          data-string
        >
          {value}
        </div>
      );
    case "number":
      return <div data-number>{value}</div>;
    case "boolean":
      return <div data-boolean>{value ? "true" : "false"}</div>;
    case "object":
      if (Array.isArray(value)) {
        return (
          <div className="flex gap-2 mr-1">
            {value.map((v, i) => (
              <FindingValue isListItem={true} key={i} value={v} />
            ))}
          </div>
        );
      } else if (value === null) {
        return <div>unknown</div>;
      } else {
        return <FindingValueObject object={value} />;
      }
  }
}

function FindingValueObject({
  object,
  isListItem,
}: {
  object: Object;
  isListItem?: boolean;
}) {
  return (
    <div className="flex gap-2 bg-white rounded-sm p-2">
      {Object.entries(object).map(([k, v]) => (
        <div className="flex flex-col" key={k}>
          <span className="text-[#5E5E5E] text-[12px]">{k}</span>
          <span className="text-[14px]">
            {typeof v === "string" ? v : JSON.stringify(v)}
          </span>
        </div>
      ))}
    </div>
  );
}

export function EvidenceListView({ finding }: { finding: Finding }) {
  const groupedNotes = useMemo(() => {
    const v = new Map<string, Evidence[]>();
    finding.evidence.forEach((f) => {
      const stringifiedValue = evidenceValueToString(f.value);
      if (v.has(stringifiedValue)) {
        v.get(stringifiedValue)!.push(f);
      } else {
        v.set(stringifiedValue, [f]);
      }
    });
    return Array.from(v, ([key, val]) => ({
      value: key,
      evidence: val,
    }));
  }, [finding]);

  return (
    <div className={s.evidence}>
      <div
        style={{
          flexDirection: "column",
          display: "grid",
          gap: "14px",
          gridTemplateColumns: "max-content auto",
          alignItems: "center",
        }}
      >
        {groupedNotes.map((valueGroup) => (
          <>
            <p>
              {valueGroup.value}{" "}
              <span className="text-[#5E5E5E]">
                ({valueGroup.evidence.length})
              </span>
            </p>
            <div className="flex gap-3 overflow-x-auto">
              {valueGroup.evidence.map((e) => (
                <EvidencePill evidence={e} />
              ))}
            </div>
          </>
        ))}
      </div>
    </div>
  );
}
