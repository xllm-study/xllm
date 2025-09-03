import * as React from "react";
import { SVGProps } from "react";

export const TimelineIcon = (props: SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={15}
    height={15}
    fill="none"
    {...props}
  >
    <circle cx={2} cy={10} r={1} fill="currentcolor" />
    <circle cx={8} cy={10} r={1} fill="currentcolor" />
    <circle cx={13} cy={5} r={1} fill="currentcolor" />
    <path stroke="currentcolor" strokeLinecap="round" d="M4.5 10h1M10 8l1-1" />
  </svg>
);
