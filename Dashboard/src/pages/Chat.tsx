import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { mockChatMessages, ChatMessage } from '../lib/data';
import { Send, Bot, User, Command } from 'lucide-react';
import { cn } from '../lib/utils';
import ReactMarkdown from 'react-markdown';

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>(mockChatMessages);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const newUserMsg: ChatMessage = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, newUserMsg]);
    setInputValue('');
    setIsTyping(true);

    // Simulate Agent Response
    setTimeout(() => {
      setIsTyping(false);
      const newAgentMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: 'He recibido tu comando. Iniciando proceso a través del Agente Director...',
        sender: 'agent',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, newAgentMsg]);
    }, 1500);
  };

  return (
    <div className="h-full flex flex-col max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <motion.h2 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-3xl font-serif font-bold text-[#1B4332]"
          >
            Auka Chat
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-sm text-[#52796F] mt-1"
          >
            Línea directa con el Agente Conversacional
          </motion.p>
        </div>
      </div>

      <div className="flex-1 bg-white border border-[#D8E3DB] rounded-3xl shadow-sm flex flex-col overflow-hidden">
        {/* Messages Area */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6"
        >
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "flex gap-4 max-w-[85%]",
                  msg.sender === 'user' ? "ml-auto flex-row-reverse" : "mr-auto"
                )}
              >
                <div className="shrink-0 mt-1">
                  {msg.sender === 'agent' ? (
                    <div className="w-8 h-8 rounded-full bg-[#1B4332] flex items-center justify-center text-[#D8F3DC] shadow-sm">
                      <Bot size={18} />
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-[#E2E8E4] border border-[#D8E3DB] flex items-center justify-center text-[#1B4332]">
                      <User size={18} />
                    </div>
                  )}
                </div>
                
                <div className={cn(
                  "flex flex-col gap-1",
                  msg.sender === 'user' ? "items-end" : "items-start"
                )}>
                  <div className={cn(
                    "px-4 py-3 rounded-2xl text-sm leading-relaxed",
                    msg.sender === 'user' 
                      ? "bg-[#1B4332] text-white rounded-tr-none shadow-sm" 
                      : "bg-[#F1F5F2] text-[#2D3A3A] border border-[#D8E3DB] rounded-tl-none whitespace-pre-wrap shadow-sm"
                  )}>
                    {msg.sender === 'agent' ? (
                      <div className="markdown-body text-[#2D3A3A]">
                        <ReactMarkdown>{msg.text}</ReactMarkdown>
                      </div>
                    ) : (
                      <p>{msg.text}</p>
                    )}
                  </div>
                  <span className="text-[10px] uppercase font-bold text-[#52796F] px-1">{msg.time}</span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {isTyping && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-4 max-w-[85%] mr-auto"
            >
              <div className="shrink-0 mt-1">
                <div className="w-8 h-8 rounded-full bg-[#1B4332] flex items-center justify-center text-[#D8F3DC] shadow-sm">
                  <Bot size={18} />
                </div>
              </div>
              <div className="bg-[#F1F5F2] border border-[#D8E3DB] shadow-sm rounded-2xl rounded-tl-none px-4 py-3 h-11 flex items-center gap-1">
                <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.4, delay: 0 }} className="w-1.5 h-1.5 bg-[#74C69D] rounded-full" />
                <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.4, delay: 0.2 }} className="w-1.5 h-1.5 bg-[#74C69D] rounded-full" />
                <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.4, delay: 0.4 }} className="w-1.5 h-1.5 bg-[#74C69D] rounded-full" />
              </div>
            </motion.div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-6 bg-[#F8FAF9] border-t border-[#D8E3DB]">
          <form onSubmit={handleSend} className="relative flex items-center">
            <button 
              type="button"
              className="absolute left-4 text-[#52796F] hover:text-[#1B4332] transition-colors"
            >
              <Command size={20} />
            </button>
            <input 
              type="text" 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ej: Busca eventos deportivos en Valencia..."
              className="w-full bg-white border border-[#D8E3DB] rounded-2xl shadow-sm py-4 pl-12 pr-16 text-[#2D3A3A] placeholder-[#52796F] focus:outline-none focus:border-[#52B788] focus:ring-1 focus:ring-[#52B788] transition-all"
            />
            <button 
              type="submit"
              disabled={!inputValue.trim()}
              className="absolute right-3 p-2.5 bg-[#1B4332] hover:bg-[#2D6A4F] disabled:bg-[#E2E8E4] disabled:text-[#52796F] text-white rounded-xl transition-colors shadow-sm"
            >
              <Send size={18} className="translate-x-[-1px] translate-y-[1px]" />
            </button>
          </form>
          <div className="mt-4 text-center">
            <p className="text-[10px] uppercase font-bold tracking-widest text-[#52796F]">Auka AI analiza y ejecuta comandos a través de los agentes del sistema.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
