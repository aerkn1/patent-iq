"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import styles from "./direct-workspace-jump.module.css";

type DirectWorkspaceJumpProps = {
  title: string;
  description: string;
  placeholder: string;
  buttonLabel: string;
  ariaLabel: string;
  routePrefix: string;
};

export function DirectWorkspaceJump({
  title,
  description,
  placeholder,
  buttonLabel,
  ariaLabel,
  routePrefix,
}: DirectWorkspaceJumpProps) {
  const router = useRouter();
  const [value, setValue] = useState("");

  return (
    <section className={styles.panel}>
      <div className={styles.eyebrow}>Direct jump</div>
      <h2 className={styles.title}>{title}</h2>
      <p className={styles.description}>{description}</p>
      <form
        className={styles.form}
        onSubmit={(event) => {
          event.preventDefault();
          const next = value.trim();
          if (!next) {
            return;
          }
          router.push(`${routePrefix}/${encodeURIComponent(next)}`);
        }}
      >
        <input value={value} onChange={(event) => setValue(event.target.value)} placeholder={placeholder} aria-label={ariaLabel} />
        <button type="submit">{buttonLabel}</button>
      </form>
    </section>
  );
}
