import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type ReportMarkdownProps = {
  content: string;
};

export function ReportMarkdown({ content }: ReportMarkdownProps) {
  return (
    <div className="archive-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
