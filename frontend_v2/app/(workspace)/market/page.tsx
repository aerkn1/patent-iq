import { MarketWorkspaceLazy } from "@/components/market/market-workspace-lazy";
import { PageShell } from "@/components/ui/page-shell";

export default function MarketPage() {
  return (
    <PageShell>
      <MarketWorkspaceLazy />
    </PageShell>
  );
}
