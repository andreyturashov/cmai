import React, { useEffect, useMemo } from 'react';
import { $getRoot, $createParagraphNode } from 'lexical';
import { HeadingNode, QuoteNode } from '@lexical/rich-text';
import { ListItemNode, ListNode } from '@lexical/list';
import { CodeHighlightNode, CodeNode, registerCodeHighlighting } from '@lexical/code';
import { LinkNode } from '@lexical/link';
import {
  $convertFromMarkdownString,
  $convertToMarkdownString,
  TRANSFORMERS,
} from '@lexical/markdown';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import { MarkdownShortcutPlugin } from '@lexical/react/LexicalMarkdownShortcutPlugin';
import { LinkPlugin } from '@lexical/react/LexicalLinkPlugin';
import { ListPlugin } from '@lexical/react/LexicalListPlugin';
import { LexicalErrorBoundary } from '@lexical/react/LexicalErrorBoundary';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-javascript';

const editorTheme = {
  paragraph: 'lexical-answer-paragraph',
  quote: 'lexical-answer-quote',
  heading: {
    h1: 'lexical-answer-heading lexical-answer-heading-h1',
    h2: 'lexical-answer-heading lexical-answer-heading-h2',
    h3: 'lexical-answer-heading lexical-answer-heading-h3',
  },
  list: {
    ul: 'lexical-answer-list lexical-answer-list-ul',
    ol: 'lexical-answer-list lexical-answer-list-ol',
    listitem: 'lexical-answer-list-item',
  },
  text: {
    bold: 'lexical-answer-bold',
    italic: 'lexical-answer-italic',
    underline: 'lexical-answer-underline',
    strikethrough: 'lexical-answer-strikethrough',
    code: 'lexical-answer-inline-code',
  },
  link: 'lexical-answer-link',
  code: 'lexical-answer-code',
  codeHighlight: {
    atrule: 'token keyword',
    attr: 'token attr-name',
    boolean: 'token boolean',
    builtin: 'token builtin',
    cdata: 'token comment',
    char: 'token string',
    class: 'token class-name',
    'class-name': 'token class-name',
    comment: 'token comment',
    constant: 'token constant',
    deleted: 'token deleted',
    doctype: 'token comment',
    entity: 'token operator',
    function: 'token function',
    important: 'token variable',
    inserted: 'token inserted',
    keyword: 'token keyword',
    namespace: 'token variable',
    number: 'token number',
    operator: 'token operator',
    prolog: 'token comment',
    property: 'token property',
    punctuation: 'token punctuation',
    regex: 'token regex',
    selector: 'token selector',
    string: 'token string',
    symbol: 'token symbol',
    tag: 'token tag',
    url: 'token operator',
    variable: 'token variable',
  },
};

function Placeholder() {
  return <div className="lexical-answer-placeholder">Write your answer here</div>;
}

function CodeHighlightingPlugin() {
  const [editor] = useLexicalComposerContext();

  useEffect(() => registerCodeHighlighting(editor), [editor]);

  return null;
}

export default function RichAnswerEditor({ value = '', onChange, ariaLabel = 'Your Answer' }) {
  const initialConfig = useMemo(
    () => ({
      namespace: 'RichAnswerEditor',
      theme: editorTheme,
      onError(error) {
        throw error;
      },
      nodes: [
        HeadingNode,
        QuoteNode,
        ListNode,
        ListItemNode,
        LinkNode,
        CodeNode,
        CodeHighlightNode,
      ],
      editorState: () => {
        if (value.trim()) {
          $convertFromMarkdownString(value, TRANSFORMERS);
          return;
        }

        const root = $getRoot();
        root.clear();
        root.append($createParagraphNode());
      },
    }),
    [value],
  );

  return (
    <LexicalComposer initialConfig={initialConfig}>
      <div className="lexical-answer-shell">
        <RichTextPlugin
          contentEditable={
            <ContentEditable
              className="lexical-answer-input"
              aria-label={ariaLabel}
              role="textbox"
              aria-multiline="true"
              spellCheck={true}
            />
          }
          placeholder={<Placeholder />}
          ErrorBoundary={LexicalErrorBoundary}
        />
        <HistoryPlugin />
        <ListPlugin />
        <LinkPlugin />
        <CodeHighlightingPlugin />
        <MarkdownShortcutPlugin transformers={TRANSFORMERS} />
        <OnChangePlugin
          onChange={(editorState) => {
            editorState.read(() => {
              onChange?.($convertToMarkdownString(TRANSFORMERS));
            });
          }}
        />
      </div>
      <p className="answer-editor-hint">
        Supports markdown shortcuts for bold, lists, links, and inline or fenced code blocks.
      </p>
    </LexicalComposer>
  );
}
