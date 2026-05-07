import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Prospect } from '../lib/data';
import { Search, Filter, Phone, Mail, ChevronRight, X, PhoneCall, NotebookPen, CheckCircle, Clock, Loader2, FileText } from 'lucide-react';
import { useProspects } from '../lib/useProspects';
import { supabase } from '../lib/supabase';
import { cn } from '../lib/utils';
import gsap from 'gsap';
import { ProposalModal } from '../components/ProposalModal';

export function Prospects() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [notesDraft, setNotesDraft] = useState('');
  const [isProposalModalOpen, setIsProposalModalOpen] = useState(false);
  const rowsRef = useRef<HTMLTableSectionElement>(null);

  const { prospects, loading, setProspects } = useProspects();

  // Handlers for Supabase updates
  const handleUpdateStatus = async (id: string, newStatus: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    
    // Optimistic update
    setProspects(prev => prev.map(p => p.id === id ? { ...p, estado: newStatus as any } : p));
    if (selectedProspect && selectedProspect.id === id) {
      setSelectedProspect(prev => prev ? { ...prev, estado: newStatus as any } : null);
    }

    try {
      await supabase.from('auka_prospectos').update({ estado: newStatus }).eq('id', id);
    } catch (err) {
      console.error("Error updating status", err);
    }
  };

  const handleUpdateNotes = async (id: string, newNotes: string) => {
    // Optimistic update
    setProspects(prev => prev.map(p => p.id === id ? { ...p, notas: newNotes } : p));
    if (selectedProspect && selectedProspect.id === id) {
      setSelectedProspect(prev => prev ? { ...prev, notas: newNotes } : null);
    }
    setIsEditingNotes(false);

    try {
      await supabase.from('auka_prospectos').update({ notas: newNotes }).eq('id', id);
    } catch (err) {
      console.error("Error updating notes", err);
    }
  };

  const handleEditNotesClick = () => {
    setNotesDraft(selectedProspect?.notas || '');
    setIsEditingNotes(true);
  };

  const filteredProspects = prospects.filter(p => 
    p.empresa.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.evento.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.ciudad.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    if (rowsRef.current) {
      gsap.from(rowsRef.current.children, {
        opacity: 0,
        y: 20,
        stagger: 0.05,
        duration: 0.4,
        ease: "power2.out"
      });
    }
  }, [searchTerm]);

  const getPriorityColor = (prioridad: string) => {
    switch(prioridad) {
      case 'ALTA': return 'bg-[#D8F3DC] text-[#1B4332]';
      case 'MEDIA': return 'bg-[#F1F5F2] text-[#2D6A4F]';
      case 'BAJA': return 'bg-white border border-[#D8E3DB] text-[#52796F]';
      default: return 'bg-white border border-[#D8E3DB] text-[#52796F]';
    }
  };

  const getStatusColor = (estado: string) => {
    switch(estado) {
      case 'nuevo': return 'bg-[#D8F3DC] text-[#1B4332]';
      case 'contactado': return 'bg-[#F1F5F2] text-[#2D6A4F]';
      case 'enriquecer': return 'bg-[#D8F3DC] text-[#40916C]';
      case 'descartado': return 'bg-white border border-[#D8E3DB] text-[#52796F]';
      case 'cerrado': return 'bg-[#1B4332] text-[#D8F3DC]';
      default: return 'bg-white border border-[#D8E3DB] text-[#52796F]';
    }
  };

  return (
    <div className="h-full flex flex-col p-6 relative overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <motion.h2 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-3xl font-serif font-bold text-[#1B4332]"
          >
            Prospectos
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-sm text-[#52796F] mt-1"
          >
            Directorio de leads generados
          </motion.p>
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex items-center gap-3"
        >
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[#52796F]" size={18} />
            <input 
              type="text" 
              placeholder="Buscar..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full sm:w-64 bg-white border border-[#D8E3DB] rounded-xl pl-11 pr-4 py-3 text-sm text-[#2D3A3A] placeholder-[#52796F] focus:outline-none focus:border-[#52B788] focus:ring-1 focus:ring-[#52B788] transition-shadow shadow-sm"
            />
          </div>
          <button className="flex items-center gap-2 bg-white border border-[#D8E3DB] hover:bg-[#F8FAF9] text-[#1B4332] font-bold px-5 py-3 rounded-xl text-sm transition-colors shadow-sm">
            <Filter size={16} />
            Filtros
          </button>
        </motion.div>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center flex-col">
          <Loader2 className="animate-spin text-[#52B788] w-8 h-8 mb-4" />
          <span className="text-[#1B4332] font-medium">Cargando prospectos...</span>
        </div>
      ) : (
        <div className="flex-1 overflow-hidden bg-white border border-[#D8E3DB] rounded-3xl shadow-sm flex flex-col">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#D8E3DB] text-[10px] font-bold text-[#52796F] uppercase tracking-widest bg-[#F8FAF9]">
                <th className="px-6 py-4">Empresa / Evento</th>
                <th className="px-6 py-4">Ubicación</th>
                <th className="px-6 py-4 hidden md:table-cell">Contacto</th>
                <th className="px-6 py-4">Estado</th>
                <th className="px-6 py-4 text-center">Score</th>
                <th className="px-6 py-4 text-right">Acción</th>
              </tr>
            </thead>
            <tbody ref={rowsRef} className="divide-y divide-[#F1F5F2]">
              {filteredProspects.map((prospect) => (
                <tr 
                  key={prospect.id} 
                  onClick={() => setSelectedProspect(prospect)}
                  className="hover:bg-[#F8FAF9] transition-colors cursor-pointer group"
                >
                  <td className="px-6 py-4">
                    <div className="font-bold text-[#1B4332]">{prospect.empresa}</div>
                    <div className="text-sm text-[#52796F] mt-0.5">{prospect.evento}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-[#2D3A3A]">{prospect.ciudad}</div>
                    <div className="text-[10px] font-bold text-[#52796F] capitalize tracking-wider mt-0.5">{prospect.tipo}</div>
                  </td>
                  <td className="px-6 py-4 hidden md:table-cell">
                    <div className="flex flex-col gap-1 text-sm font-medium text-[#52796F]">
                      {prospect.telefono && <span className="flex items-center gap-1.5"><Phone size={14} />{prospect.telefono}</span>}
                      {prospect.email && <span className="flex items-center gap-1.5"><Mail size={14} /> {prospect.email}</span>}
                      {!prospect.telefono && !prospect.email && <span className="text-[#52796F] italic">No disponible</span>}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <button 
                      onClick={(e) => handleUpdateStatus(prospect.id, prospect.estado === 'contactado' ? 'nuevo' : 'contactado', e)}
                      className={cn(
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] tracking-widest uppercase font-bold transition-all hover:opacity-80", 
                        getStatusColor(prospect.estado)
                      )}
                    >
                      {prospect.estado === 'contactado' && <CheckCircle size={12} />}
                      {prospect.estado}
                    </button>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={cn("inline-flex px-2.5 py-1 rounded text-xs uppercase font-mono font-bold", getPriorityColor(prospect.prioridad))}>
                      {(prospect.score/100).toFixed(2)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-[#52796F] hover:text-[#1B4332] p-1 rounded transition-colors group-hover:translate-x-1 duration-200">
                      <ChevronRight size={20} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredProspects.length === 0 && (
          <div className="flex-1 flex items-center justify-center text-slate-500">
            No se encontraron prospectos.
          </div>
        )}
      </div>
      )}

      {/* Side Panel for Prospect Details */}
      <AnimatePresence>
        {selectedProspect && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedProspect(null)}
              className="absolute inset-0 bg-[#2D3A3A]/20 backdrop-blur-[2px] z-20"
            />
            <motion.div 
              initial={{ x: '100%', opacity: 0.5 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: '100%', opacity: 0.5 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="absolute right-0 top-0 bottom-0 w-full sm:w-[450px] bg-[#F8FAF9] border-l border-[#D8E3DB] shadow-2xl z-30 flex flex-col"
            >
              <div className="flex items-center justify-between px-6 py-5 border-b border-[#D8E3DB] bg-white">
                <h3 className="text-xl font-serif font-bold text-[#1B4332]">Detalle de Empresa</h3>
                <button 
                  onClick={() => setSelectedProspect(null)}
                  className="p-2 bg-[#F1F5F2] hover:bg-[#E2E8E4] text-[#52796F] hover:text-[#1B4332] rounded-xl transition-colors"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="flex-1 overflow-auto p-6 space-y-8">
                <div>
                  <div className="flex items-start justify-between">
                     <div>
                      <h2 className="text-3xl font-serif font-bold text-[#1B4332]">{selectedProspect.empresa}</h2>
                      <p className="text-[#2D6A4F] font-bold mt-1">{selectedProspect.evento}</p>
                    </div>
                    <span className={cn("px-2.5 py-1 rounded text-[10px] uppercase font-bold tracking-widest border", getPriorityColor(selectedProspect.prioridad))}>
                      {selectedProspect.prioridad}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-2 mt-4">
                    <span className="px-3 py-1.5 bg-white border border-[#D8E3DB] text-[#2D3A3A] shadow-sm rounded-lg text-xs font-bold">{selectedProspect.ciudad}</span>
                    <span className="px-3 py-1.5 bg-white border border-[#D8E3DB] text-[#2D3A3A] shadow-sm rounded-lg text-xs font-bold capitalize">{selectedProspect.tipo}</span>
                    <span className={cn("px-3 py-1.5 rounded-lg text-xs font-bold border", getStatusColor(selectedProspect.estado))}>
                      {selectedProspect.estado}
                    </span>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="text-[10px] font-bold text-[#52796F] uppercase tracking-widest">Información de Contacto</h4>
                  
                  <div className="bg-white rounded-2xl p-5 border border-[#D8E3DB] shadow-sm space-y-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-[#D8F3DC] flex items-center justify-center text-[#1B4332]"><Phone size={18} /></div>
                      <div className="flex-1">
                        <div className="text-xs font-bold text-[#52796F] uppercase">Teléfono</div>
                        <div className="text-sm font-bold text-[#2D3A3A]">{selectedProspect.telefono || 'No disponible'}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-[#F1F5F2] flex items-center justify-center text-[#1B4332]"><Mail size={18} /></div>
                      <div className="flex-1">
                        <div className="text-xs font-bold text-[#52796F] uppercase">Email</div>
                        <div className="text-sm font-bold text-[#2D3A3A]">{selectedProspect.email || 'No disponible'}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-[10px] font-bold text-[#52796F] uppercase tracking-widest">Notas y Contexto</h4>
                    {!isEditingNotes && (
                      <button onClick={handleEditNotesClick} className="text-[#52B788] hover:text-[#1B4332] text-xs font-bold flex items-center gap-1">
                        <NotebookPen size={12} /> Editar
                      </button>
                    )}
                  </div>
                  <div className="bg-white rounded-2xl p-5 border border-[#D8E3DB] shadow-sm min-h-[100px]">
                    {isEditingNotes ? (
                      <div className="flex flex-col gap-3">
                        <textarea 
                          value={notesDraft}
                          onChange={(e) => setNotesDraft(e.target.value)}
                          className="w-full h-32 p-3 text-sm text-[#2D3A3A] bg-[#F8FAF9] border border-[#D8E3DB] rounded-xl focus:outline-none focus:border-[#52B788] resize-none"
                          placeholder="Escribe los detalles de la llamada..."
                          autoFocus
                        />
                        <div className="flex justify-end gap-2">
                          <button onClick={() => setIsEditingNotes(false)} className="px-4 py-2 text-xs font-bold text-[#52796F] hover:bg-[#F1F5F2] rounded-lg">Cancelar</button>
                          <button onClick={() => handleUpdateNotes(selectedProspect.id, notesDraft)} className="px-4 py-2 text-xs font-bold text-white bg-[#1B4332] hover:bg-[#2D6A4F] rounded-lg shadow-sm">Guardar</button>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-[#2D3A3A] leading-relaxed whitespace-pre-wrap">
                        {selectedProspect.notas ? selectedProspect.notas : <span className="text-[#52796F] italic">No hay notas registradas. Haz clic en Editar para agregar detalles.</span>}
                      </p>
                    )}
                  </div>
                </div>

              </div>

              {/* Actions Footer */}
              <div className="p-6 border-t border-[#D8E3DB] bg-white space-y-3">
                {selectedProspect.estado === 'contactado' && (
                  <button 
                    onClick={() => setIsProposalModalOpen(true)}
                    className="w-full flex items-center justify-center gap-2 bg-[#22C55E] hover:bg-[#16A34A] text-white py-3 rounded-xl text-sm font-bold transition-colors shadow-sm"
                  >
                    <FileText size={16} />
                    Generar Propuesta y Enviar por WhatsApp
                  </button>
                )}
                <div className="grid grid-cols-2 gap-3">
                  <button className="flex items-center justify-center gap-2 bg-[#1B4332] hover:bg-[#2D6A4F] text-white py-3 rounded-xl text-sm font-bold transition-colors shadow-sm">
                    <PhoneCall size={16} />
                    Llamar
                  </button>
                  <button className="flex items-center justify-center gap-2 bg-white hover:bg-[#F8FAF9] border border-[#D8E3DB] text-[#1B4332] py-3 rounded-xl text-sm font-bold transition-colors shadow-sm">
                    <Mail size={16} />
                    Mensaje
                  </button>
                </div>
                <button 
                  onClick={() => handleUpdateStatus(selectedProspect.id, selectedProspect.estado === 'contactado' ? 'nuevo' : 'contactado')}
                  className={cn(
                    "w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-bold transition-colors shadow-sm",
                    selectedProspect.estado === 'contactado' 
                      ? "bg-white border border-[#D8E3DB] text-[#52796F] hover:bg-[#F8FAF9]" 
                      : "bg-[#F1F5F2] hover:bg-[#E2E8E4] text-[#1B4332]"
                  )}
                >
                  <CheckCircle size={16} className={selectedProspect.estado === 'contactado' ? "text-[#52796F]" : "text-[#52B788]"} />
                  {selectedProspect.estado === 'contactado' ? 'Marcar como No Contactado' : 'Marcar como Contactado'}
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <ProposalModal 
        isOpen={isProposalModalOpen}
        onClose={() => setIsProposalModalOpen(false)}
        prospect={selectedProspect}
      />
    </div>
  );
}
