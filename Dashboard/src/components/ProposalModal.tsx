import React, { useState, useRef } from 'react';
import html2pdf from 'html2pdf.js';
import { X, FileText, Send, Download, MessageCircle, Loader2, Check, ChevronLeft, Phone } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Prospect } from '../lib/data';
import ProposalContent from './ProposalContent';

interface ProposalModalProps {
  isOpen: boolean;
  onClose: () => void;
  prospect: Prospect | null;
}

export function ProposalModal({ isOpen, onClose, prospect }: ProposalModalProps) {
  const proposalRef = useRef<HTMLDivElement>(null);
  const [step, setStep] = useState<'create' | 'generating' | 'preview' | 'whatsapp'>('create');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isGenerated, setIsGenerated] = useState(false);
  const [pdfBase64, setPdfBase64] = useState<string>('');
  const [generatedPdfFileName, setGeneratedPdfFileName] = useState('');
  const [customMessage, setCustomMessage] = useState('');

  // Mensaje profesional B2B por defecto escrito por experto en cierres de venta con 20+ aÃ±os de experiencia
  const defaultMessage = `Hola ${prospect?.empresa || ''},

Me complace compartirle nuestra propuesta comercial personalizada, pensada exclusivamente para usted tras nuestra conversaciÃ³n telefÃ³nica.

He analizado en detalle sus necesidades de hidrataciÃ³n corporativa y he confeccionado esta propuesta que incluso antes de verse, aportarÃ¡ un ahorro operativo real de hasta un 35% en costos logÃ­sticos de hidrataciÃ³n, con la posibilidad de proyectar su marca en cada punto de contacto.

Adjunto encontrarÃ¡ el documento completo con toda la estructura comercial preferencial, especificaciones tÃ©cnicas y alcance logÃ­stico. Estoy convencido de que la mejor decisiÃ³n que puede tomar su empresa hoy es asociarse con quien tiene la capacidad de materializar esa ventaja competitiva desde el primer despacho.

Quedo atento a cualquier duda o punto que desee profundizar para concretar esta alianza estratÃ©gica.

Un cordial saludo,`;

  React.useEffect(() => {
    if (isOpen) {
      setStep('create');
      setIsGenerated(false);
      setPdfBase64('');
      setGeneratedPdfFileName('');
      setCustomMessage('');
    }
  }, [isOpen]);

  const handleGenerate = async () => {
    if (!proposalRef.current || !prospect) return;
    setIsGenerating(true);
    setStep('generating');

    try {
      const opt = {
        margin: [0, 0, 0, 0],
        filename: `${prospect.empresa}_Propuesta_AguasArauka.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
          scale: 2, 
          useCORS: true,
          logging: false 
        },
        jsPDF: { 
          unit: 'mm', 
          format: 'a4', 
          orientation: 'portrait' 
        }
      };

      // Save to disk using File System Access API
      try {
        const dirHandle = await (window as any).showDirectoryPicker({ mode: 'readwrite' });
        const folderName = prospect.empresa.replace(/[^a-zA-Z0-9\s]/g, '').replace(/\s+/g, '_');
        const folderHandle = await dirHandle.getDirectoryHandle(folderName, { create: true });
        
        const fileName = `${prospect.empresa}_Propuesta.pdf`;
        
        // Generate PDF blob
        const pdfOutput = await html2pdf().set(opt).from(proposalRef.current).output('blob');
        
        const fileHandle = await folderHandle.getFileHandle(fileName, { create: true });
        const writable = await fileHandle.createWritable();
        await writable.write(pdfOutput);
        await writable.close();

        setGeneratedPdfFileName(fileName);
      } catch (err) {
        // If File System Access API failed, still generate for download
        console.log('File System Access API not available or cancelled, generating download only');
        const pdf = await html2pdf().set(opt).from(proposalRef.current).toPdf().get('pdf');
        const pdfBlob = pdf.output('blob');
        setGeneratedPdfFileName(opt.filename);
      }

      // Also store base64 for download
      const pdfForBase64 = await html2pdf().set(opt).from(proposalRef.current).toPdf().get('pdf');
      const pdfBlobForBase64 = pdfForBase64.output('blob');
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = (reader.result as string);
        setPdfBase64(base64);
        setIsGenerated(true);
        setStep('preview');
        setIsGenerating(false);
      };
      reader.readAsDataURL(pdfBlobForBase64);
    } catch (err) {
      console.error('Error generating PDF:', err);
      setIsGenerating(false);
    }
  };

  const fileName = prospect ? `${prospect.empresa}_Propuesta_AguasArauka.pdf` : 'Propuesta_AguasArauka.pdf';

  const handleContinueToWhatsApp = () => {
    setStep('whatsapp');
  };

  const handleDownload = () => {
    if (pdfBase64) {
      const link = document.createElement('a');
      link.href = pdfBase64;
      link.download = fileName;
      link.click();
    }
  };

  const getWhatsAppLink = () => {
    const phone = prospect?.telefono || '';
    const cleanPhone = phone.replace(/\D/g, '');
    const prefix = cleanPhone.startsWith('58') ? '' : '58';
    const fullNumber = prefix + cleanPhone;
    const message = encodeURIComponent(customMessage || defaultMessage);
    return `https://wa.me/${fullNumber}?text=${message}`;
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={!isGenerating ? onClose : undefined}
            className="fixed inset-0 bg-[#2D3A3A]/40 backdrop-blur-sm z-40"
          />
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed inset-4 md:inset-10 z-50 bg-white rounded-3xl shadow-2xl flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#D8E3DB] bg-[#F8FAF9] flex-shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#1B4332] rounded-xl flex items-center justify-center">
                  <FileText className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-serif font-bold text-[#1B4332]">Propuesta Comercial</h2>
                  <p className="text-xs text-[#52796F]">{prospect?.empresa || 'Prospecto'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {step !== 'create' && step !== 'generating' && (
                  <button 
                    onClick={() => {
                      if (step === 'preview') setStep('create');
                      else if (step === 'whatsapp') setStep('preview');
                    }}
                    className="flex items-center gap-1 px-4 py-2 text-sm font-bold text-[#52796F] hover:bg-[#F1F5F2] rounded-xl transition-colors"
                  >
                    <ChevronLeft size={16} />
                    Atrás
                  </button>
                )}
                <button 
                  onClick={!isGenerating ? onClose : undefined}
                  className="p-2 bg-[#F1F5F2] hover:bg-[#E2E8E4] text-[#52796F] hover:text-[#1B4332] rounded-xl transition-colors"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-auto p-6 min-h-0">
              
              {/* Step: Create */}
              {step === 'create' && (
                <div className="space-y-6">
                  <div className="text-center py-8">
                    <div className="w-20 h-20 bg-[#D8F3DC] rounded-full flex items-center justify-center mx-auto mb-4">
                      <FileText className="w-10 h-10 text-[#1B4332]" />
                    </div>
                    <h3 className="text-2xl font-serif font-bold text-[#1B4332] mb-2">Generar Propuesta Comercial</h3>
                    <p className="text-[#52796F] text-sm max-w-md mx-auto">
                      Se generarÃ¡ una propuesta personalizada con el formato oficial de Aguas Arauka para {prospect?.empresa}.
                      El PDF se guardarÃ¡ en una carpeta con el nombre de la empresa.
                    </p>
                  </div>

                  <div className="max-w-lg mx-auto space-y-4">
                    <div className="bg-white border border-[#D8E3DB] rounded-2xl p-5 space-y-3">
                      <h4 className="text-sm font-bold text-[#1B4332] uppercase tracking-wider">Datos del Prospecto</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-[#52796F]">Empresa</span>
                          <span className="font-bold text-[#1B4332]">{prospect?.empresa}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-[#52796F]">Evento</span>
                          <span className="font-bold text-[#1B4332]">{prospect?.evento}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-[#52796F]">Ciudad</span>
                          <span className="font-bold text-[#1B4332]">{prospect?.ciudad}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-[#52796F]">Teléfono</span>
                          <span className="font-bold text-[#1B4332]">{prospect?.telefono || 'No disponible'}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-[#E8F5E9] border border-[#A5D6A7] rounded-2xl p-4 text-sm text-[#1B4332]">
                      <strong>Icon: Tip:</strong> AsegÃºrate de que el estado del prospecto sea &quot;Contactado&quot; antes de enviar la propuesta. Esto indicarÃ¡ que ya realizaste la llamada de seguimiento.
                    </div>
                  </div>
                </div>
              )}

              {/* Step: Generating */}
              {step === 'generating' && (
                <div className="text-center py-20">
                  <Loader2 className="w-12 h-12 text-[#52B788] animate-spin mx-auto mb-6" />
                  <h3 className="text-xl font-serif font-bold text-[#1B4332] mb-2">Generando propuesta...</h3>
                  <p className="text-[#52796F] text-sm">Estamos creando el PDF oficial con el formato de Aguas Arauka.</p>
                </div>
              )}

              {/* Step: Preview */}
              {step === 'preview' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-[#1B4332]">Vista Previa del PDF</h3>
                    {isGenerated && (
                      <button 
                        onClick={handleDownload}
                        className="flex items-center gap-2 px-4 py-2 bg-white border border-[#D8E3DB] hover:bg-[#F8FAF9] text-[#1B4332] rounded-xl text-sm font-bold transition-colors"
                      >
                        <Download size={16} />
                        Descargar PDF
                      </button>
                    )}
                  </div>

                  <div className="border border-[#D8E3DB] rounded-2xl overflow-hidden bg-white">
                    {/* Hidden proposal for PDF generation */}
                    <div className="opacity-0 absolute -left-[9999px]">
                      <div ref={proposalRef}>
                        <ProposalContent prospectName={prospect?.empresa} />
                      </div>
                    </div>
                    
                    {/* Preview */}
                    <div className="p-4 max-h-[500px] overflow-auto">
                      {!isGenerating && isGenerated ? (
                        <div className="text-center py-12">
                          <div className="w-16 h-16 bg-[#D8F3DC] rounded-full flex items-center justify-center mx-auto mb-4">
                            <Check className="w-8 h-8 text-[#1B4332]" />
                          </div>
                          <p className="text-[#1B4332] font-bold mb-2">¡Propuesta Generada!</p>
                          <p className="text-[#52796F] text-sm">El PDF ha sido guardado en:</p>
                          <p className="text-[#52796F] text-sm mt-2">
                            <code className="bg-[#F1F5F2] px-2 py-1 rounded-lg text-[#1B4332] font-mono text-xs">
                              /{prospect?.empresa}/Propuesta.pdf
                            </code>
                          </p>
                          {pdfBase64 && (
                            <div className="mt-4 inline-block border border-[#D8E3DB] rounded-xl p-3 bg-[#F8FAF9]">
                              <p className="text-xs text-[#52796F] mb-2">Archivo generado:</p>
                              <p className="text-sm font-bold text-[#1B4332]">{generatedPdfFileName}</p>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-center py-12">
                          <Loader2 className="w-8 h-8 text-[#52B788] animate-spin mx-auto mb-4" />
                          <p className="text-[#52796F] font-medium">Generando propuesta...</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Step: WhatsApp */}
              {step === 'whatsapp' && (
                <div className="space-y-6 max-w-2xl mx-auto">
                  <div className="text-center">
                    <div className="w-20 h-20 bg-[#DCFCE7] rounded-full flex items-center justify-center mx-auto mb-4">
                      <MessageCircle className="w-10 h-10 text-[#22C55E]" />
                    </div>
                    <h3 className="text-2xl font-serif font-bold text-[#1B4332] mb-2">Enviar por WhatsApp</h3>
                    <p className="text-[#52796F] text-sm">
                      Revisa el mensaje profesional que se enviarÃ¡ al prospecto. Puedes personalizarlo antes de enviar.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="bg-white border border-[#D8E3DB] rounded-2xl overflow-hidden">
                      <div className="bg-[#1B4332] px-5 py-3 flex items-center gap-3">
                        <div className="w-10 h-10 bg-[#D8F3DC] rounded-full flex items-center justify-center">
                          <Phone className="w-5 h-5 text-[#1B4332]" />
                        </div>
                        <div>
                          <div className="text-white text-sm font-bold">{prospect?.empresa}</div>
                          <div className="text-[#95D5B2] text-xs">{prospect?.telefono}</div>
                        </div>
                      </div>
                      <div className="p-5 bg-[#F8FAF9]">
                        <textarea
                          value={customMessage || defaultMessage}
                          onChange={(e) => setCustomMessage(e.target.value)}
                          className="w-full min-h-[200px] p-4 text-sm text-[#2D3A3A] bg-white border border-[#D8E3DB] rounded-xl focus:outline-none focus:border-[#52B788] resize-none leading-relaxed"
                          placeholder="Escribe tu mensaje..."
                        />
                      </div>
                    </div>

                    <div className="bg-[#F0FDF4] border border-[#86EFAC] rounded-2xl p-4">
                      <p className="text-xs text-[#166534] font-semibold mb-2"> Icon: PDF Adjunto:</p>
                      <div className="flex items-center gap-3 bg-white rounded-xl p-3 border border-[#BBF7D0]">
                        <FileText className="w-8 h-8 text-[#1B4332]" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-bold text-[#1B4332] truncate">{fileName}</p>
                          <p className="text-xs text-[#52796F]">Propuesta Comercial B2B</p>
                        </div>
                        <Check className="w-5 h-5 text-[#22C55E] flex-shrink-0" />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Footer Actions */}
            <div className="p-6 border-t border-[#D8E3DB] bg-white flex-shrink-0">
              {step === 'create' && (
                <div className="flex justify-end gap-3">
                  <button 
                    onClick={onClose}
                    className="px-6 py-3 text-sm font-bold text-[#52796F] hover:bg-[#F1F5F2] rounded-xl transition-colors"
                    disabled={isGenerating}
                  >
                    Cancelar
                  </button>
                  <button 
                    onClick={() => {
                      handleGenerate();
                    }}
                    disabled={isGenerating}
                    className="flex items-center gap-2 px-6 py-3 bg-[#1B4332] hover:bg-[#2D6A4F] text-white rounded-xl text-sm font-bold transition-colors disabled:opacity-50"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Generando...
                      </>
                    ) : (
                      <>
                        <FileText size={16} />
                        Generar Propuesta
                      </>
                    )}
                  </button>
                </div>
              )}

              {step === 'preview' && (
                <div className="flex justify-between items-center">
                  <button 
                    onClick={handleDownload}
                    className="flex items-center gap-2 px-5 py-3 bg-white border border-[#D8E3DB] hover:bg-[#F8FAF9] text-[#1B4332] rounded-xl text-sm font-bold transition-colors"
                  >
                    <Download size={16} />
                    Descargar PDF
                  </button>
                  <div className="flex gap-3">
                    <button 
                      onClick={() => setStep('create')}
                      className="px-6 py-3 text-sm font-bold text-[#52796F] hover:bg-[#F1F5F2] rounded-xl transition-colors"
                    >
                      Volver
                    </button>
                    <button 
                      onClick={handleContinueToWhatsApp}
                      className="flex items-center gap-2 px-6 py-3 bg-[#22C55E] hover:bg-[#16A34A] text-white rounded-xl text-sm font-bold transition-colors"
                    >
                      <MessageCircle size={16} />
                      Enviar por WhatsApp
                    </button>
                  </div>
                </div>
              )}

              {step === 'whatsapp' && (
                <div className="flex justify-between items-center">
                  <button 
                    onClick={handleDownload}
                    className="flex items-center gap-2 px-5 py-3 bg-white border border-[#D8E3DB] hover:bg-[#F8FAF9] text-[#1B4332] rounded-xl text-sm font-bold transition-colors"
                  >
                    <Download size={16} />
                    Descargar PDF
                  </button>
                  <a
                    href={getWhatsAppLink()}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-[#22C55E] hover:bg-[#16A34A] text-white rounded-xl text-sm font-bold transition-colors"
                  >
                    <Send size={16} />
                    Abrir WhatsApp
                  </a>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
