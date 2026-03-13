import InteractiveSessionShell from '@/components/InteractiveSessionShell';

interface Props {
  params: {
    harness: string;
    id: string;
  };
}

export default function InteractiveSessionPage({ params }: Props) {
  return <InteractiveSessionShell harness={params.harness} artifactId={params.id} />;
}
