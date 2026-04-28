import { PortfolioWorkspaceLazy } from "@/components/portfolio/portfolio-workspace-lazy";

type PortfolioDynamicPageProps = {
  params: Promise<{
    ownerId: string;
  }>;
};

export default async function PortfolioDynamicPage({ params }: PortfolioDynamicPageProps) {
  const { ownerId } = await params;

  return <PortfolioWorkspaceLazy ownerId={ownerId} />;
}
