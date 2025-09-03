import { IconButton, Select, TextField } from "@radix-ui/themes";
import { Cross1Icon, PlusIcon } from "@radix-ui/react-icons";
import s from "./Input.module.scss";
import { VariableType, VariableValue } from "../../../shared/types";

export const Input = ({
  definition,
  value,
  disabled,
  setCorrectedValue,
}: {
  definition: VariableType;
  value: VariableValue;
  disabled?: boolean;
  setCorrectedValue: (value: VariableValue) => void;
}) => {
  if (definition.type != "list")
    return (
      <SingleElement
        definition={definition}
        value={value}
        disabled={disabled}
        setCorrectedValue={setCorrectedValue}
      />
    );

  const uiValue = value == null || value === undefined ? [] : value;

  if (!Array.isArray(uiValue)) {
    console.error(
      "Expected value to be an array for list type, but got:",
      uiValue,
    );
    return <div>Value error: expected List</div>;
  }

  const addElement = () => {
    if (definition.value.type === "string") {
      setCorrectedValue([...uiValue, ""]);
    } else if (definition.value.type === "enum") {
      // add a new element with an enum value not already in the list
      const newValue = definition.value.values.find(
        (v) => !uiValue.includes(v),
      );
      if (!newValue) return;
      setCorrectedValue([...uiValue, newValue]);
    } else if (definition.value.type === "object") {
      const fx = uiValue;
      setCorrectedValue([...uiValue, {}]);
    }
  };

  const removeElement = (index: number) => {
    const newValue = [...uiValue];
    newValue.splice(index, 1);
    setCorrectedValue(newValue);
  };

  const updateElement = (index: number, newValue: VariableValue) => {
    if (uiValue.includes(newValue)) return;
    let newList = [...uiValue];
    newList[index] = newValue;
    setCorrectedValue(newList);
  };

  return (
    <div className="flex gap-2 items-center">
      {uiValue.map((v, i) => (
        <div
          key={i}
          className={`flex bg-[#e8e8e8] items-center  rounded-md  ${definition.value.type === "object" ? "p-2" : ""}`}
        >
          <SingleElement
            definition={definition.value}
            value={v}
            disabled={disabled}
            setCorrectedValue={(v) => {
              updateElement(i, v);
            }}
          />

          <IconButton
            data-hidden={disabled}
            onClick={() => removeElement(i)}
            className={s.removeFromListBtn}
            variant="soft"
            size="2"
            disabled={disabled}
          >
            <Cross1Icon />
          </IconButton>
        </div>
      ))}
      <IconButton
        style={{
          display: disabled ? "none" : undefined,
        }}
        disabled={disabled}
        onClick={addElement}
      >
        <PlusIcon />
      </IconButton>
    </div>
  );
};

export const SingleElement = ({
  definition,
  value,
  disabled,
  setCorrectedValue,
}: {
  definition: VariableType;
  value: VariableValue;
  disabled?: boolean;
  setCorrectedValue: (value: VariableValue) => void;
}) => {
  switch (definition.type) {
    case "enum":
      return (
        <Select.Root
          value={value ? (value as string) : "none"}
          disabled={disabled}
          onValueChange={(v) => setCorrectedValue(v === "none" ? null : v)}
        >
          <Select.Trigger />
          <Select.Content position="popper">
            {definition.values.map((v) => (
              <Select.Item value={v} key={v}>
                {v}
              </Select.Item>
            ))}
            <Select.Item value="none">none</Select.Item>
          </Select.Content>
        </Select.Root>
      );
    case "string":
      return (
        <TextField.Root
          className="min-w-[120px]"
          disabled={disabled}
          variant="surface"
          placeholder="Unknown"
          value={(value as string | undefined) ?? ""}
          onChange={(e) => setCorrectedValue(e.target.value)}
        />
      );
    case "bool":
      return (
        <Select.Root
          value={value ? "true" : "false"}
          disabled={disabled}
          onValueChange={(v) => setCorrectedValue(v === "true")}
        >
          <Select.Trigger />
          <Select.Content>
            <Select.Item value="true">true</Select.Item>
            <Select.Item value="false">false</Select.Item>
          </Select.Content>
        </Select.Root>
      );

    case "object":
      const uiValue =
        value == null || value === undefined
          ? {}
          : (value as { [key: string]: VariableValue });

      return (
        <div className="flex gap-2">
          {definition.values.map((v) => (
            <div key={v.name}>
              <div className="font-medium text-sm text-[#5B5B5B]">{v.name}</div>
              <SingleElement
                key={v.name}
                value={uiValue[v.name as string] ?? null}
                definition={v.value}
                setCorrectedValue={(corr) => {
                  setCorrectedValue({ ...uiValue, [v.name]: corr });
                }}
                disabled={disabled}
              />
            </div>
          ))}
        </div>
      );

    default:
      return <span className="text-red-700">TODO!!</span>;
  }
};
