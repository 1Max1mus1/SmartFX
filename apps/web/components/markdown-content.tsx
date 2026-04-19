"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownContentProps = {
  content: string;
};

export function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <div className="space-y-4 text-base leading-8 text-black/75">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="mt-2 text-3xl font-semibold text-ink">{children}</h1>,
          h2: ({ children }) => <h2 className="mt-6 text-2xl font-semibold text-ink">{children}</h2>,
          h3: ({ children }) => <h3 className="mt-5 text-xl font-semibold text-ink">{children}</h3>,
          p: ({ children }) => <p className="leading-8 text-black/75">{children}</p>,
          ul: ({ children }) => <ul className="list-disc space-y-2 pl-6 text-black/75">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal space-y-2 pl-6 text-black/75">{children}</ol>,
          li: ({ children }) => <li>{children}</li>,
          table: ({ children }) => (
            <div className="overflow-x-auto">
              <table className="w-full border-separate border-spacing-0 overflow-hidden rounded-2xl border border-[#E6D39A]">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-white/70">{children}</thead>,
          tbody: ({ children }) => <tbody className="bg-white/35">{children}</tbody>,
          th: ({ children }) => <th className="border-b border-r border-[#E6D39A] px-4 py-3 text-left font-semibold last:border-r-0">{children}</th>,
          td: ({ children }) => <td className="border-b border-r border-[#E6D39A] px-4 py-3 last:border-r-0">{children}</td>,
          code: ({ children }) => <code className="rounded bg-white/65 px-1 py-0.5 text-[0.95em] text-ink">{children}</code>,
          pre: ({ children }) => <pre className="overflow-x-auto rounded-2xl bg-[#FFF9E8] p-4 text-sm leading-7 text-black/80">{children}</pre>,
          blockquote: ({ children }) => <blockquote className="border-l-4 border-[#D5B456] pl-4 text-black/65">{children}</blockquote>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
