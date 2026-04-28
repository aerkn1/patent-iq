export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }

  return `${(value * 100).toFixed(digits)}%`;
}

export function formatAdaptivePercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }

  const percent = value * 100;
  const absolute = Math.abs(percent);

  if (absolute === 0) {
    return "0.0%";
  }

  if (absolute >= 0.1) {
    return `${percent.toFixed(1)}%`;
  }

  if (absolute >= 0.01) {
    return `${percent.toFixed(2)}%`;
  }

  return "<0.01%";
}

export function formatDecimal(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }

  return value.toFixed(digits);
}

export function formatOrdinal(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }

  const rounded = Math.round(value);
  const absolute = Math.abs(rounded);
  const mod100 = absolute % 100;

  if (mod100 >= 11 && mod100 <= 13) {
    return `${rounded}th`;
  }

  switch (absolute % 10) {
    case 1:
      return `${rounded}st`;
    case 2:
      return `${rounded}nd`;
    case 3:
      return `${rounded}rd`;
    default:
      return `${rounded}th`;
  }
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }

  return new Intl.NumberFormat("en-US").format(value);
}
