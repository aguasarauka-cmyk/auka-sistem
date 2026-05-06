import { useEffect, useState } from 'react';
import { supabase } from './supabase';
import { Prospect } from './data';

export function useProspects() {
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchProspects() {
      try {
        setLoading(true);
        // Supabase query
        const { data, error: pbError } = await supabase
          .from('auka_prospectos')
          .select('*')
          .order('creado_en', { ascending: false });

        if (pbError) throw pbError;

        // Map Supabase auka_prospectos to the UI Prospect type
        const mapped: Prospect[] = (data || []).map((row: any) => ({
          id: row.id,
          empresa: row.empresa || 'Sin nombre',
          evento: row.evento || 'Evento Potencial',
          ciudad: row.ciudad || 'Desconocida',
          lat: 10.4806, // default
          lng: -66.9036, // default
          tipo: row.fuente === 'google_maps' ? 'corporativo' : 'otro',
          telefono: row.telefono || '',
          email: row.email || '',
          instagram: row.instagram || '',
          web: row.web || '',
          estado: row.estado || 'nuevo',
          notas: row.notas || '',
          fecha: row.creado_en ? new Date(row.creado_en).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
          score: row.score || 50,
          prioridad: row.prioridad || 'MEDIA',
          raw_data: row.raw_data
        }));

        setProspects(mapped);
      } catch (err: any) {
        console.error("Error fetching prospects:", err);
        setError(err);
      } finally {
        setLoading(false);
      }
    }

    fetchProspects();
    
    // Set up realtime subscription
    const channel = supabase
      .channel('prospectos-changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'auka_prospectos' },
        (payload) => {
          console.log('Change received!', payload);
          fetchProspects(); // refetch on any change for simplicity
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return { prospects, loading, error, setProspects };
}
