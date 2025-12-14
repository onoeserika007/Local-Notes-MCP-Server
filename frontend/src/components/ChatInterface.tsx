import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, FileText, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  referencedNotes?: Array<{
    id: number;
    title: string;
    preview: string;
    similarity?: number;
  }>;
}

interface ChatInterfaceProps {
  className?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setIsStreaming(true);

    try {
      // 使用流式API
      const response = await fetch('http://localhost:8000/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage.content,
          top_k: 15,  // 增加到15条笔记
          stream: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8', { fatal: false });  // 添加容错处理

      if (!reader) {
        throw new Error('No response body');
      }

      let assistantMessage: Message = {
        role: 'assistant',
        content: '',
      };

      setMessages((prev) => [...prev, assistantMessage]);

      let buffer = '';  // 添加缓冲区处理不完整的行

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // 解码时保持流模式，避免截断多字节字符
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        // 按行处理，保留不完整的行
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';  // 保留最后一行（可能不完整）

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            
            if (data === '[DONE]') {
              setIsStreaming(false);
              break;
            }
            
            if (data.startsWith('[ERROR]')) {
              console.error('Stream error:', data);
              break;
            }

            // 追加内容
            if (data) {  // 只处理非空数据
              assistantMessage.content += data;
              setMessages((prev) => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1] = { ...assistantMessage };
                return newMessages;
              });
            }
          }
        }
      }
      
      // 处理剩余的buffer
      if (buffer && buffer.startsWith('data: ')) {
        const data = buffer.slice(6).trim();
        if (data && data !== '[DONE]' && !data.startsWith('[ERROR]')) {
          assistantMessage.content += data;
          setMessages((prev) => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = { ...assistantMessage };
            return newMessages;
          });
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '抱歉，发生了错误。请稍后再试。',
        },
      ]);
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex-1 flex justify-center">
        <div className="w-full max-w-4xl flex flex-col"></div>
        <div className={`flex flex-col h-full w-full bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/20 ${className}`}>
          {/* Header */}
          <div className="flex items-center justify-center gap-3 px-6 py-5 border-b border-gray-200/80 bg-white/90 backdrop-blur-sm shadow-sm">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-md">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              AI 智能助手
            </h2>
          </div>

          {/* Messages - 居中容器，更宽的布局 */}
          <div className="flex-1 overflow-y-auto w-full">
            <div className="max-w-5xl mx-auto px-6 py-8 w-full">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-gray-400 py-32">
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-8 shadow-xl">
                    <Sparkles className="w-12 h-12 text-white" />
                  </div>
                  <p className="text-2xl font-bold text-gray-700 mb-3">开始对话</p>
                  <p className="text-base text-gray-500">我会基于你的笔记内容智能回答问题</p>
                </div>
              )}

              <div className="space-y-8">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`rounded-3xl px-7 py-5 shadow-md ${
                        message.role === 'user'
                          ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white max-w-3xl'
                          : 'bg-white text-gray-800 border border-gray-200 max-w-4xl'
                      }`}
                    >
                        {message.role === 'assistant' ? (
                          <div className="prose prose-base max-w-none dark:prose-invert">
                            <ReactMarkdown
                              components={{
                                code({ node, inline, className, children, ...props }: any) {
                                  const match = /language-(\w+)/.exec(className || '');
                                  return !inline && match ? (
                                    <SyntaxHighlighter
                                      style={vscDarkPlus}
                                      language={match[1]}
                                      PreTag="div"
                                      {...props}
                                    >
                                      {String(children).replace(/\n$/, '')}
                                    </SyntaxHighlighter>
                                  ) : (
                                    <code className={className} {...props}>
                                      {children}
                                    </code>
                                  );
                                },
                              }}
                            >
                              {message.content}
                            </ReactMarkdown>

                            {/* 引用的笔记 */}
                            {message.referencedNotes && message.referencedNotes.length > 0 && (
                              <div className="mt-6 pt-5 border-t border-gray-200">
                                <p className="text-sm text-gray-600 mb-4 flex items-center gap-2 font-semibold">
                                  <FileText className="w-4 h-4" />
                                  参考了 {message.referencedNotes.length} 条笔记
                                </p>
                                <div className="space-y-3">
                                  {message.referencedNotes.map((note) => (
                                    <div
                                      key={note.id}
                                      className="text-sm p-4 bg-gray-50/80 rounded-xl border border-gray-200 hover:border-blue-300 hover:bg-blue-50/30 transition-all cursor-pointer"
                                    >
                                      <div className="font-semibold text-gray-800 mb-1.5">{note.title}</div>
                                      <div className="text-gray-600 line-clamp-2 leading-relaxed">{note.preview}</div>
                                      {note.similarity !== undefined && (
                                        <div className="text-gray-500 mt-2 text-xs font-medium">
                                          相似度: {(note.similarity * 100).toFixed(1)}%
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="whitespace-pre-wrap leading-relaxed text-base">{message.content}</p>
                        )}
                      </div>
                  </div>
                ))}

              {isStreaming && (
                <div className="flex items-center gap-3 text-gray-500 text-base px-7">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                  <span className="font-medium">AI 正在思考...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
              </div>
            </div>
          </div>

          {/* Input - 居中容器，更宽更美观 */}
          <div className="border-t border-gray-200/80 bg-white/90 backdrop-blur-sm shadow-lg w-full">
            <div className="max-w-5xl mx-auto px-6 py-6 w-full">
              <div className="flex items-end gap-4">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入问题，按 Enter 发送，Shift+Enter 换行..."
                  className="flex-1 resize-none rounded-3xl border-2 border-gray-200 px-6 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-md transition-all hover:shadow-lg text-base"
                  rows={1}
                  style={{
                    minHeight: '60px',
                    maxHeight: '200px',
                  }}
                  disabled={isLoading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!input.trim() || isLoading}
                  className="flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-xl active:scale-95"
                >
                  {isLoading ? (
                    <Loader2 className="w-6 h-6 animate-spin" />
                  ) : (
                    <Send className="w-6 h-6" />
                  )}
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-4 text-center font-medium">
                AI 会自动检索相关笔记来回答你的问题
              </p>
            </div>
          </div>
        </div>
    </div>
  );
};
