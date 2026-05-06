import React, { useEffect, useRef } from 'react';
import { motion } from 'motion/react';
import { ArrowUpRight, Users, CheckCircle2, Clock, Calendar, Phone, Mail, Instagram, Loader2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';
import gsap from 'gsap';
import { useProspects } from '../lib/useProspects';

export function Overview() {
  const cardsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (cardsRef.current) {
      gsap.from(cardsRef.current.children, {
        opacity: 0,
        y: 40,
        stagger: 0.1,
        duration: 0.8,
        ease: "power3.out"
      });
    }
  }, []);

  const { prospects, loading } = useProspects();

  const totalProspects = prospects.length;
  const nuevosHoy = prospects.filter(p => p.estado === 'nuevo').length;
  const contactados = prospects.filter(p => p.estado === 'contactado').length;
  const pendientes = prospects.filter(p => p.estado === 'enriquecer').length;

  const cityData = prospects.reduce((acc, curr) => {
    const existing = acc.find(a => a.name === curr.ciudad);
    if (existing) {
      existing.value += 1;
    } else {
      acc.push({ name: curr.ciudad, value: 1 });
    }
    return acc;
  }, [] as { name: string; value: number }[]);

  const typeData = prospects.reduce((acc, curr) => {
    const existing = acc.find(a => a.name === curr.tipo);
    if (existing) {
      existing.value += 1;
    } else {
      acc.push({ name: curr.tipo, value: 1 });
    }
    return acc;
  }, [] as { name: string; value: number }[]);

  const COLORS = ['#1B4332', '#2D6A4F', '#40916C', '#52B788', '#74C69D', '#95D5B2', '#B7E4C7'];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
        <div>
          <motion.h2 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-serif font-bold text-[#1B4332]"
          >
            Lead Machine Dashboard
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-sm text-[#52796F] mt-1"
          >
            Real-time event detection for Central Venezuela
          </motion.p>
        </div>
        <div className="flex gap-4 hidden md:flex">
          <div className="bg-white px-6 py-3 rounded-2xl shadow-sm border border-[#E2E8E4] flex flex-col items-center">
            <span className="text-[10px] uppercase font-bold text-[#95D5B2]">Leads Found</span>
            <span className="text-2xl font-bold text-[#1B4332]">{totalProspects}</span>
          </div>
          <div className="bg-white px-6 py-3 rounded-2xl shadow-sm border border-[#E2E8E4] flex flex-col items-center">
            <span className="text-[10px] uppercase font-bold text-[#95D5B2]">Conversion</span>
            <span className="text-2xl font-bold text-[#1B4332]">12.4%</span>
          </div>
        </div>
      </header>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="animate-spin text-[#52B788] w-8 h-8" />
          <span className="ml-3 text-[#1B4332] font-medium">Cargando datos en tiempo real...</span>
        </div>
      ) : (
        <>
          {/* KPIs */}
          <div ref={cardsRef} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Total Prospectos" value={totalProspects.toString()} icon={<Users size={22} />} trend="+12%" />
        <KpiCard title="Nuevos Hoy" value={nuevosHoy.toString()} icon={<ArrowUpRight size={22} />} trend="+4%" color="text-[#52B788]" />
        <KpiCard title="Contactados" value={contactados.toString()} icon={<CheckCircle2 size={22} />} color="text-[#40916C]" />
        <KpiCard title="Pendientes" value={pendientes.toString()} icon={<Clock size={22} />} color="text-[#2D6A4F]" />
      </div>

      {/* Upcoming Events - Moved UP */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white border border-[#D8E3DB] rounded-3xl shadow-sm overflow-hidden"
      >
        <div className="p-6 border-b border-[#F1F5F2] flex justify-between items-center bg-[#F8FAF9]">
          <div>
            <h3 className="font-serif text-xl font-bold text-[#1B4332]">Eventos Próximos (Top Score)</h3>
            <p className="text-sm text-[#52796F] mt-1">Prospectos ordenados por prioridad y conversión potencial.</p>
          </div>
        </div>
        <div className="divide-y divide-[#F1F5F2]">
          {prospects.slice(0, 3).map((p, i) => (
            <div key={p.id} className="p-6 hover:bg-[#F8FAF9] transition-colors flex flex-col gap-4">
              
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-2xl bg-[#D8F3DC] text-[#1B4332]">
                    <Calendar size={20} />
                  </div>
                  <div>
                    <h4 className="font-bold text-[#1B4332] text-lg leading-tight mb-1">{p.evento}</h4>
                    <span className="text-sm font-bold text-[#2D6A4F]">{p.empresa}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="inline-flex px-3 py-1 rounded bg-[#F1F5F2] text-[10px] font-bold text-[#1B4332] uppercase tracking-widest mb-1 shadow-sm border border-[#E2E8E4]">
                    {p.fecha}
                  </div>
                  <div className="font-mono text-[#52B788] font-bold text-sm">Score: {(p.score / 100).toFixed(2)}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
                <div className="flex flex-col gap-1.5">
                  <span className="text-[10px] uppercase font-bold text-[#95D5B2] tracking-wider">Ubicación</span>
                  <span className="text-sm font-medium text-[#2D3A3A] bg-white border border-[#D8E3DB] px-3 py-1.5 rounded-lg shadow-sm whitespace-nowrap overflow-hidden text-ellipsis">{p.ciudad}</span>
                </div>
                <div className="flex flex-col gap-1.5">
                  <span className="text-[10px] uppercase font-bold text-[#95D5B2] tracking-wider">Tipo</span>
                  <span className="text-sm font-medium text-[#2D3A3A] capitalize bg-white border border-[#D8E3DB] px-3 py-1.5 rounded-lg shadow-sm">{p.tipo}</span>
                </div>
                <div className="flex flex-col gap-1.5">
                  <span className="text-[10px] uppercase font-bold text-[#95D5B2] tracking-wider">Estado</span>
                  <span className="text-sm font-medium text-[#2D3A3A] capitalize bg-white border border-[#D8E3DB] px-3 py-1.5 rounded-lg shadow-sm">{p.estado}</span>
                </div>
                <div className="flex flex-col gap-1.5">
                  <span className="text-[10px] uppercase font-bold text-[#95D5B2] tracking-wider">Prioridad</span>
                  <span className="text-sm font-medium text-[#2D3A3A] capitalize bg-white border border-[#D8E3DB] px-3 py-1.5 rounded-lg shadow-sm">{p.prioridad}</span>
                </div>
              </div>

              <div className="bg-white border border-[#D8E3DB] shadow-sm rounded-2xl p-5 mt-2 grid md:grid-cols-2 gap-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-[#F8FAF9] rounded-bl-full -z-10" />
                <div className="space-y-3">
                  <span className="text-[10px] uppercase font-bold text-[#52796F] tracking-widest flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#52B788]"></div>
                    Contacto
                  </span>
                  <div className="flex flex-col gap-2 text-sm text-[#2D3A3A] font-medium">
                    {p.telefono && <span className="flex items-center gap-2.5"><Phone size={15} className="text-[#52B788]" /> {p.telefono}</span>}
                    {p.email && <span className="flex items-center gap-2.5"><Mail size={15} className="text-[#52B788]" /> {p.email}</span>}
                    {p.instagram && <span className="flex items-center gap-2.5"><Instagram size={15} className="text-[#52B788]" /> {p.instagram}</span>}
                    {!p.telefono && !p.email && !p.instagram && <span className="italic text-[#52796F]">Sin datos de contacto</span>}
                  </div>
                </div>
                <div className="space-y-3">
                  <span className="text-[10px] uppercase font-bold text-[#52796F] tracking-widest flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#52B788]"></div>
                    Notas
                  </span>
                  <p className="text-sm text-[#52796F] leading-relaxed bg-[#F8FAF9] p-3 rounded-xl border border-[#F1F5F2]">{p.notas || 'Sin notas adicionales introducidas para este prospecto.'}</p>
                </div>
              </div>

            </div>
          ))}
        </div>
      </motion.div>

      {/* Charts - Moved DOWN */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
          className="bg-white border border-[#D8E3DB] rounded-3xl p-6 shadow-sm"
        >
          <h3 className="font-serif text-xl font-bold text-[#1B4332] mb-6">Prospectos por Ciudad</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cityData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#52796F" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#52796F" fontSize={12} tickLine={false} axisLine={false} />
                <RechartsTooltip 
                  cursor={{ fill: '#F1F5F2' }}
                  contentStyle={{ backgroundColor: 'white', borderColor: '#D8E3DB', color: '#1B4332', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} 
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {cityData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-white border border-[#D8E3DB] rounded-3xl p-6 shadow-sm"
        >
          <h3 className="font-serif text-xl font-bold text-[#1B4332] mb-6">Tipos de Eventos</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={typeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {typeData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'white', borderColor: '#D8E3DB', color: '#1B4332', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} 
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>
        </>
      )}
    </div>
  );
}

function KpiCard({ title, value, icon, trend, color = "text-[#52B788]" }: { title: string, value: string, icon: React.ReactNode, trend?: string, color?: string }) {
  return (
    <div className="bg-white px-6 py-5 border border-[#E2E8E4] rounded-2xl shadow-sm relative overflow-hidden group">
      <div className="absolute top-0 right-0 p-4 text-[#1B4332] opacity-10 group-hover:opacity-20 transition-opacity">
        {icon}
      </div>
      <div className="flex flex-col gap-1">
        <span className="text-[10px] uppercase font-bold text-[#95D5B2]">{title}</span>
        <div className="flex items-end gap-3 mt-1">
          <span className="text-3xl font-bold text-[#1B4332] tracking-tight">{value}</span>
          {trend && (
            <span className={`text-xs font-bold ${color} mb-1`}>{trend}</span>
          )}
        </div>
      </div>
    </div>
  );
}
