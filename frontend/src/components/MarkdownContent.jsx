import React from 'react';
import Prism from 'prismjs';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function highlightCode(value, language) {
  if (!language || !Prism.languages[language]) {
    return value;
  }

  return Prism.highlight(value, Prism.languages[language], language);
}

export default function MarkdownContent({ content = '', className = '' }) {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className: codeClassName, children, ...props }) {
            const rawValue = String(children).replace(/\n$/, '');
            const languageMatch = /language-([\w-]+)/.exec(codeClassName || '');
            const language = languageMatch?.[1]?.toLowerCase();
            const isBlockCode = Boolean(language) || rawValue.includes('\n');

            if (!isBlockCode) {
              return (
                <code className="markdown-inline-code" {...props}>
                  {rawValue}
                </code>
              );
            }

            const highlighted = highlightCode(rawValue, language);
            return (
              <pre className="markdown-code-block">
                <code
                  className={language ? `language-${language}` : undefined}
                  dangerouslySetInnerHTML={{ __html: highlighted }}
                />
              </pre>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
