export function ColoredRatio({
  coloredText,
  label,
  scale,
  color,
}: {
  coloredText: string;
  label: string;
  scale: number;
  color?: string;
}) {
  return (
    <p>
      <span
        style={{
          color: scale > 0.7 ? "#008A23" : "#BF3D00",
        }}
      >
        {coloredText}
      </span>{" "}
      <span style={{ color: color }}>{label}</span>
    </p>
  );
}
