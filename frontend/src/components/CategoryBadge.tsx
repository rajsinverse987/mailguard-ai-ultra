"use client";

import { classNames, categoryColor } from "@/lib/utils";

export function CategoryBadge({ value }: { value: string }) {
  return (
    <span
      className={classNames(
        "text-xs px-2 py-0.5 rounded-md capitalize",
        categoryColor(value)
      )}
    >
      {value.replace("_", " ")}
    </span>
  );
}
