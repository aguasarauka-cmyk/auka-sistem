export type Prospect = {
  id: string;
  empresa: string;
  evento: string;
  ciudad: string;
  lat: number;
  lng: number;
  tipo: 'corporativo' | 'deportivo' | 'social' | 'cultural' | 'gastronómico' | 'religioso' | 'otro';
  telefono: string;
  email?: string;
  instagram?: string;
  web?: string;
  estado: 'nuevo' | 'contactado' | 'enriquecer' | 'descartado' | 'cerrado';
  notas: string;
  fecha: string;
  score: number;
  prioridad: 'ALTA' | 'MEDIA' | 'BAJA';
};

export const mockProspects: Prospect[] = [
  {
    id: '1',
    empresa: 'XYZ Events',
    evento: 'Fitness Caracas 2026',
    ciudad: 'Caracas',
    lat: 10.4806,
    lng: -66.9036,
    tipo: 'deportivo',
    telefono: '+58-412-1234567',
    email: 'info@xyzevents.com',
    instagram: '@xyzevents',
    estado: 'nuevo',
    notas: 'Empresa con evento próximo, contacto directo disponible.',
    fecha: '2026-03-15',
    score: 85,
    prioridad: 'ALTA'
  },
  {
    id: '2',
    empresa: 'Producciones Alpha',
    evento: 'Congreso Médico',
    ciudad: 'Valencia',
    lat: 10.1620,
    lng: -68.0077,
    tipo: 'corporativo',
    telefono: '+58-414-9876543',
    estado: 'contactado',
    notas: 'Interesado en cotización para 200 personas.',
    fecha: '2026-04-20',
    score: 90,
    prioridad: 'ALTA'
  },
  {
    id: '3',
    empresa: 'Eventos Beta',
    evento: 'Feria Tech 2026',
    ciudad: 'Maracay',
    lat: 10.2469,
    lng: -67.5958,
    tipo: 'corporativo',
    telefono: '+58-424-5551234',
    instagram: '@eventosbeta',
    estado: 'nuevo',
    notas: '',
    fecha: '2026-05-10',
    score: 65,
    prioridad: 'MEDIA'
  },
  {
    id: '4',
    empresa: 'Gran Feria Valencia',
    evento: 'Feria Valencia',
    ciudad: 'Valencia',
    lat: 10.1700,
    lng: -67.9800,
    tipo: 'corporativo',
    telefono: '',
    instagram: '@feriavlc',
    estado: 'enriquecer',
    notas: 'Falta información de contacto directo.',
    fecha: '2026-06-01',
    score: 30,
    prioridad: 'BAJA'
  },
  {
    id: '5',
    empresa: 'Gourmet Fest',
    evento: 'Food Festival Caracas',
    ciudad: 'Caracas',
    lat: 10.4900,
    lng: -66.8900,
    tipo: 'gastronómico',
    telefono: '+58-412-9998877',
    estado: 'nuevo',
    notas: 'Evento masivo, ideal para patrocinio.',
    fecha: '2026-07-15',
    score: 75,
    prioridad: 'MEDIA'
  }
];

export type AgentLog = {
  id: string;
  time: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
};

export const mockAgentLogs: AgentLog[] = [
  { id: '1', time: '10:32:00', message: 'Buscando eventos en Caracas...', type: 'info' },
  { id: '2', time: '10:32:15', message: '12 empresas encontradas en Google Maps', type: 'success' },
  { id: '3', time: '10:33:00', message: 'Analizando Instagram para "Fitness Caracas 2026"', type: 'info' },
  { id: '4', time: '10:33:45', message: 'Estructurando datos de @xyzevents...', type: 'info' },
  { id: '5', time: '10:34:10', message: 'Nuevo prospecto guardado: XYZ Events (Score: 85)', type: 'success' },
  { id: '6', time: '10:35:00', message: 'Búsqueda en Valencia iniciada', type: 'info' },
  { id: '7', time: '10:35:30', message: 'Error al acceder a página web de Eventos Beta, reintentando...', type: 'warning' },
];

export type ChatMessage = {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  time: string;
};

export const mockChatMessages: ChatMessage[] = [
  { id: '1', sender: 'agent', text: '¡Hola! Soy AUKA, tu asistente de prospección para Aguas Arauka. ¿En qué te puedo ayudar hoy?', time: '09:00 AM' },
  { id: '2', sender: 'user', text: 'Dame los prospectos de alta prioridad en Caracas', time: '09:05 AM' },
  { id: '3', sender: 'agent', text: 'Encontré 6 prospectos de ALTA prioridad en Caracas:\n1. XYZ Events — Fitness Caracas 2026\n2. Producciones Gourmet — Food Fest', time: '09:05 AM' },
];
