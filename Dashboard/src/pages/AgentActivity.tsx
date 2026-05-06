import React, { useEffect, useRef } from 'react';
import { motion } from 'motion/react';
import { mockAgentLogs } from '../lib/data';
import { Terminal, Info, CheckCircle2, AlertCircle, AlertTriangle } from 'lucide-react';
import { cn } from '../lib/utils';
import gsap from 'gsap';

export function AgentActivity() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom on mount
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, []);

  const getLogIcon = (type: string) => {
    switch (type) {
      case 'info': return <Info size={16} className="text-blue-400" />;
      case 'success': return <CheckCircle2 size={16} className="text-green-400" />;
      case 'warning': return <AlertTriangle size={16} className="text-yellow-400" />;
      case 'error': return <AlertCircle size={16} className="text-red-400" />;
      default: return <Info size={16} className="text-slate-400" />;
    }
  };

  return (
    <div className="h-full flex flex-col p-6 md:p-8 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center gap-4">
        <div className="p-3 bg-[#D8F3DC] rounded-xl text-[#1B4332] border border-[#B7E4C7]">
          <Terminal size={24} />
        </div>
        <div>
          <motion.h2 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-3xl font-serif font-bold text-[#1B4332]"
          >
            Actividad del Agente
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-sm text-[#52796F] mt-1"
          >
            Monitor de acciones del sistema autónomo en tiempo real
          </motion.p>
        </div>
      </div>

      <div className="flex-1 bg-[#1B4332] border border-[#1B4332] rounded-3xl shadow-xl overflow-hidden flex flex-col relative font-mono text-[#D8F3DC]">
        <div className="h-10 bg-[#081C15] border-b border-[#081C15] flex items-center px-4 gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-[#2D6A4F]"></div>
            <div className="w-3 h-3 rounded-full bg-[#2D6A4F]"></div>
            <div className="w-3 h-3 rounded-full bg-[#2D6A4F]"></div>
          </div>
          <span className="text-xs text-[#52B788] ml-4 font-sans opacity-70">auka-system-logs / var/log/agentes</span>
        </div>
        
        <div 
          ref={containerRef}
          className="flex-1 p-6 overflow-auto space-y-3"
        >
          {mockAgentLogs.map((log, index) => (
            <motion.div 
              key={log.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-start gap-4 text-sm font-medium hover:bg-[#2D6A4F]/50 p-1.5 -mx-1.5 rounded transition-colors"
            >
              <div className="text-[#52796F] shrink-0">[{log.time}]</div>
              <div className="shrink-0 mt-0.5">{getLogIcon(log.type)}</div>
              <div className={cn(
                "flex-1",
                log.type === 'info' ? 'text-[#B7E4C7]' :
                log.type === 'success' ? 'text-[#74C69D]' :
                log.type === 'warning' ? 'text-[#95D5B2]' : 'text-red-300'
              )}>
                {log.message}
              </div>
            </motion.div>
          ))}

          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: mockAgentLogs.length * 0.1, repeat: Infinity, duration: 1.5 }}
            className="flex items-center gap-4 text-sm mt-4 text-[#52796F]"
          >
            <div>[{new Date().toLocaleTimeString()}]</div>
            <div className="w-2 h-4 bg-[#74C69D]"></div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
