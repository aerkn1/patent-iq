import { PublicationWorkspaceLazy } from "@/components/publication/publication-workspace-lazy";

type PublicationDynamicPageProps = {
  params: Promise<{
    publicationId: string;
  }>;
};

export default async function PublicationDynamicPage({ params }: PublicationDynamicPageProps) {
  const { publicationId } = await params;

  return <PublicationWorkspaceLazy publicationId={publicationId} />;
}
