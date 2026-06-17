"use client";

import { classNames, priorityColor } from "@/lib/utils";

export function PriorityBadge({ value }: { value: string }) {
  return (
    <span className={classNames("text-xs px-2 py-0.5 rounded-md border", priorityColor(value))}>
      {value.toUpperCase()}
    </span>
  );
}
