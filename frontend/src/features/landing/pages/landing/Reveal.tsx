import { useReveal } from './useReveal';

export default function Reveal({
  children,
  className = '',
  ...rest
}: React.HTMLAttributes<HTMLDivElement>) {
  const ref = useReveal<HTMLDivElement>();
  return (
    <div ref={ref} className={`reveal ${className}`.trim()} {...rest}>
      {children}
    </div>
  );
}
