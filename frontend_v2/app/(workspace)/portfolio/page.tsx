import { PortfolioEntrySearch } from "@/components/portfolio/portfolio-entry-search";
import { PageShell } from "@/components/ui/page-shell";

export default function PortfolioPage() {
  return (
    <PageShell
      eyebrow="Portfolio"
      title="Portfolio intelligence workspace"
      description="Search a harmonized owner to open the enterprise portfolio surface with ranking, technology, citation, and forecast drilldowns."
    >
      <PortfolioEntrySearch />
    </PageShell>
  );
}
