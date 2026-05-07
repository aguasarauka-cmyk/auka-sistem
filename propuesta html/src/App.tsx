import React, { useEffect, useState } from 'react';
import heroBg from './portada2.png';
import para1Img from './para1.jpeg';
import { Droplet, TrendingUp, Tag } from 'lucide-react';

export default function App() {
  const [currentDate, setCurrentDate] = useState('');

  useEffect(() => {
    setCurrentDate(new Date().toLocaleDateString('es-ES', { 
      year: 'numeric', month: 'long', day: 'numeric' 
    }).toUpperCase());
  }, []);

  return (
    <>
      <div className="page">
        <img 
          alt="Corporativo" 
          className="absolute top-0 left-0 w-full h-full object-cover z-0 pointer-events-none opacity-25 blur-[4px] grayscale" 
          src={heroBg}
        />
        <div className="absolute top-0 right-0 w-[30mm] h-[30mm] bg-secondary z-20"></div>
        <div className="flex flex-col justify-between h-[247mm] relative z-10">
          <div className="max-w-[100mm]">
            <div className="w-[300px] mb-2">
              <svg height="100%" style={{ fillRule: 'evenodd', clipRule: 'evenodd', strokeMiterlimit: 10 }} version="1.1" viewBox="0 0 386 64" width="100%" xmlSpace="preserve" xmlns="http://www.w3.org/2000/svg" xmlnsXlink="http://www.w3.org/1999/xlink">
                <g id="Capa_1-2">
                  <g id="LOGOTIPO">
                    <path d="M380.515,12.185l0,38.78c0,3.952 -3.208,7.16 -7.16,7.16l-192.95,0c-3.952,0 -7.16,-3.208 -7.16,-7.16l0,-38.78c0,-3.952 3.208,-7.16 7.16,-7.16l192.95,0c3.952,0 7.16,3.208 7.16,7.16Z" style={{ fill: '#203f92' }}></path>
                    <path d="M181.535,44.095c4.8,-8.64 9.73,-17.31 14.5,-25.9c4.76,8.58 9.56,17.29 14.34,25.9c-2.06,0 -4.05,0.04 -5.94,0c-0.32,-0.01 -0.72,-0.9 -0.92,-1.27c-2.21,-3.93 -4.38,-7.88 -6.57,-11.82c-0.18,-0.32 -0.42,-0.59 -0.77,-1.06c-0.91,1.61 -1.75,3.06 -2.56,4.53c-1.51,2.72 -3.04,5.43 -4.49,8.18c-0.47,0.9 -1,1.5 -2,1.46l-5.59,0l0,-0.02Z" id="_3" style={{ fill: '#6fc4c4', fillRule: 'nonzero' }}></path>
                    <path d="M245.815,44.095c4.8,-8.64 9.73,-17.31 14.5,-25.9c4.76,8.58 9.56,17.29 14.34,25.9c-2.06,0 -4.05,0.04 -5.94,0c-0.32,-0.01 -0.72,-0.9 -0.92,-1.27c-2.21,-3.93 -4.38,-7.88 -6.57,-11.82c-0.18,-0.32 -0.42,-0.59 -0.77,-1.06c-0.91,1.61 -1.75,3.06 -2.56,4.53c-1.51,2.72 -3.04,5.43 -4.49,8.18c-0.47,0.9 -1,1.5 -2,1.46l-5.59,0l0,-0.02Z" id="_4" style={{ fill: '#6fc4c4', fillRule: 'nonzero' }}></path>
                    <path d="M340.315,44.095c4.8,-8.64 9.73,-17.31 14.5,-25.9c4.76,8.58 9.56,17.29 14.34,25.9c-2.06,0 -4.05,0.04 -5.94,0c-0.32,-0.01 -0.72,-0.9 -0.92,-1.27c-2.21,-3.93 -4.38,-7.88 -6.57,-11.82c-0.18,-0.32 -0.42,-0.59 -0.77,-1.06c-0.91,1.61 -1.75,3.06 -2.56,4.53c-1.51,2.72 -3.04,5.43 -4.49,8.18c-0.47,0.9 -1,1.5 -2,1.46l-5.59,0l0,-0.02Z" id="_4-2" style={{ fill: '#6fc4c4', fillRule: 'nonzero' }}></path>
                    <path d="M233.115,35.015c2.36,3.01 4.66,5.92 7.13,9.06c-2.14,0 -4.08,0.02 -6.03,-0.03c-0.24,0 -0.5,-0.38 -0.7,-0.63c-1.87,-2.33 -3.72,-4.67 -5.58,-7.01c-0.64,-0.81 -3.62,-1.42 -4.45,-0.82c-0.25,0.18 -0.33,0.72 -0.34,1.09c-0.03,2.4 -0.01,4.81 -0.01,7.41c-1.7,0 -3.3,0.02 -4.9,-0.02c-0.18,0 -0.44,-0.32 -0.52,-0.55c-0.1,-0.26 -0.05,-0.57 -0.05,-0.86c0,-7.64 0.02,-15.28 -0.02,-22.93c0,-1.13 0.3,-1.49 1.47,-1.47c3.57,0.08 7.14,0.03 10.72,0.03c4.74,0 8.74,3.01 9.19,8.07c0.28,3.16 -1.78,6.73 -4.96,8.2c-0.25,0.12 -0.5,0.24 -0.93,0.45l-0.02,0.01Zm-5.87,-11.89c-1.04,0 -2.07,0.02 -3.11,0c-0.65,-0.02 -1.01,0.15 -1,0.89c0.03,1.95 -0.02,3.9 0.05,5.85c0.01,0.3 0.49,0.82 0.76,0.83c2.07,0.06 4.16,0.14 6.22,-0.03c2,-0.16 3.48,-2.16 3.31,-4.13c-0.17,-1.98 -1.77,-3.4 -3.86,-3.4l-2.36,0l-0.01,-0.01Z" style={{ fill: '#6fc4c4', fillRule: 'nonzero' }}></path>
                    <path d="M301.175,27.015c0,2.37 0.06,4.74 -0.01,7.1c-0.19,5.91 -5.81,10.58 -11.71,10.12c-5.73,-0.45 -10.19,-5.52 -10.12,-10.96c0.07,-4.65 0.02,-9.3 0,-13.96c0,-0.84 0.25,-1.22 1.14,-1.16l3.11,0c0.91,-0.05 1.13,0.34 1.12,1.17c-0.03,4.44 -0.03,8.89 0,13.33c0.02,2.95 1.49,5.17 3.86,5.93c3.65,1.18 7.24,-1.51 7.27,-5.52c0.04,-4.49 0.05,-8.97 -0.02,-13.46c-0.02,-1.16 0.29,-1.48 1.48,-1.46c0.92,0 1.75,0.02 2.61,0c0.99,-0.02 1.33,0.26 1.31,1.26c-0.05,2.53 -0.02,5.07 -0.02,7.6l-0.03,0l0.01,0.01Z" style={{ fill: '#6fc4c4', fillRule: 'nonzero' }}></path>
                    <g>
                      <path d="M326.635,18.195l5.25,0c-0.28,0.45 -0.53,0.92 -0.83,1.35c-2.35,3.32 -4.71,6.63 -7.08,9.93c-0.7,0.97 -0.9,1.9 -0.05,2.89c3.27,3.8 6.53,7.6 9.79,11.4l0,0.23c-1.82,0 -3.64,0.08 -5.46,0c-0.52,-0.02 -1.16,-0.36 -1.51,-0.75c-3.2,-3.65 -6.33,-7.36 -9.53,-11.01c-0.74,-0.85 -0.71,-1.53 -0.07,-2.41c2.28,-3.12 4.54,-6.27 6.75,-9.44c0.71,-1.02 1.5,-1.86 2.74,-2.18l-0,-0.01Z" style={{ fill: '#6fc4c4', fillRule: 'nonzero' }}></path>
                      <path d="M315.855,18.195c-0.02,0.69 0.06,24.73 0.04,26.02l-5.46,0l0,-26.02l5.42,0Z" style={{ fill: '#6fc4c4', fillRule: 'nonzero' }}></path>
                    </g>
                    <path d="M380.515,13.525l0,36.1c0,4.691 -3.809,8.5 -8.5,8.5l-358.49,0c-4.691,0 -8.5,-3.809 -8.5,-8.5l0,-36.1c0,-4.691 3.809,-8.5 8.5,-8.5l358.49,0c4.691,0 8.5,3.809 8.5,8.5Z" style={{ fill: 'none', stroke: '#203f92', strokeWidth: '1px' }}></path>
                    <path d="M66.955,33.635l-7.81,0l0,-4.84l13.4,0c1.53,6.52 -2.87,13.52 -9.53,15.34c-6.93,1.89 -14.06,-1.86 -16.25,-8.58c-2.39,-7.32 1.37,-14.72 8.37,-17.07c6.79,-2.28 13.88,1.33 16.17,6.7c-2.32,0 -4.58,0.15 -6.82,-0.07c-1.04,-0.1 -1.96,-1.04 -3.01,-1.35c-3.83,-1.13 -7.78,0.92 -9.28,4.71c-1.38,3.5 0.2,7.77 3.52,9.52c3.66,1.92 7.87,0.93 10.12,-2.42c0.36,-0.53 0.64,-1.11 1.12,-1.94Z" style={{ fill: '#203f92', fillRule: 'nonzero' }}></path>
                    <path d="M80.565,18.305l5.57,0c0.02,0.45 0.06,0.89 0.06,1.33c0,4.61 -0.02,9.22 0.01,13.83c0.02,2.87 2.13,5.12 4.98,5.43c2.52,0.27 5.02,-1.51 5.66,-4.07c0.13,-0.51 0.14,-1.07 0.14,-1.61c0.01,-4.49 0,-8.97 0,-13.46l0,-1.43l5.58,0c0.03,0.35 0.08,0.67 0.08,0.99c0,4.86 0.03,9.72 0,14.58c-0.05,6.21 -5.76,11.11 -11.94,10.58c-5.3,-0.45 -9.95,-4.8 -10.11,-10.58c-0.14,-5.14 -0.03,-10.3 -0.03,-15.6l-0,0.01Z" style={{ fill: '#203f92', fillRule: 'nonzero' }}></path>
                    <path d="M141.145,35.975c1.8,0 3.45,-0.01 5.1,0.02c0.19,0 0.48,0.17 0.56,0.34c1.19,2.6 3.39,2.73 5.78,2.36c0.4,-0.06 0.78,-0.25 1.17,-0.39c0.87,-0.31 1.57,-0.78 1.63,-1.81c0.06,-1.06 -0.55,-1.74 -1.43,-2.13c-1.06,-0.47 -2.17,-0.8 -3.25,-1.21c-2.04,-0.78 -4.28,-1.25 -6.06,-2.43c-4.1,-2.7 -3.95,-8.62 0.23,-11.28c3.9,-2.48 9.92,-2.41 13.48,1.49c1.37,1.5 2.05,3.28 2.11,5.46c-1.72,0 -3.41,0.02 -5.09,-0.02c-0.21,0 -0.49,-0.25 -0.61,-0.46c-1.17,-2.08 -2.77,-2.85 -5.16,-2.45c-0.49,0.08 -1.05,0.12 -1.41,0.4c-0.52,0.39 -1.2,0.97 -1.23,1.5c-0.03,0.53 0.52,1.41 1.03,1.62c1.95,0.79 3.96,1.41 5.98,2.01c2.31,0.69 4.48,1.58 5.85,3.68c2.26,3.47 1.27,7.73 -2.27,10.11c-3.93,2.64 -9.76,2.44 -13.38,-0.56c-1.85,-1.54 -2.96,-3.53 -3.01,-6.24l-0.02,-0.01Z" style={{ fill: '#203f92', fillRule: 'nonzero' }}></path>
                    <path d="M12.075,44.095c4.8,-8.64 9.73,-17.31 14.5,-25.9c4.76,8.58 9.56,17.29 14.34,25.9c-2.06,0 -4.05,0.04 -5.94,0c-0.32,-0.01 -0.72,-0.9 -0.92,-1.27c-2.21,-3.93 -4.38,-7.88 -6.57,-11.82c-0.18,-0.32 -0.42,-0.59 -0.77,-1.06c-0.91,1.61 -1.75,3.06 -2.56,4.53c-1.51,2.72 -3.04,5.43 -4.49,8.18c-0.47,0.9 -1,1.5 -2,1.46l-5.59,0l0,-0.02Z" id="_1" style={{ fill: '#203f92', fillRule: 'nonzero' }}></path>
                    <path d="M135.995,44.155c-2.09,0 -3.87,0.05 -5.65,-0.04c-0.41,-0.02 -0.94,-0.47 -1.17,-0.87c-1.87,-3.26 -3.68,-6.56 -5.51,-9.85c-0.56,-1 -1.12,-1.99 -1.79,-3.17c-1.07,1.91 -2.04,3.62 -3,5.34c-1.41,2.54 -2.82,5.07 -4.19,7.63c-0.38,0.71 -0.82,1.01 -1.65,0.98c-1.78,-0.07 -3.57,-0.02 -5.68,-0.02c4.82,-8.68 9.53,-17.15 14.32,-25.79c4.8,8.64 9.49,17.08 14.32,25.78l0,0.01Z" id="_2" style={{ fill: '#203f92', fillRule: 'nonzero' }}></path>
                  </g>
                </g>
              </svg>
            </div>
            <p className="inline-block mt-2 text-primary font-bold text-[10pt] uppercase tracking-[0.05em]">
              Alianza Estratégica 2024
            </p>
          </div>
          <div className="mt-[35mm] relative">
            <p className="text-[14pt] text-gray-dark tracking-[0.1em] uppercase font-semibold mt-[6mm]">Propuesta de Eficiencia Operativa</p>
            <h1 className="text-[40pt] leading-none font-bold mt-2 font-outfit uppercase tracking-tighter">
              OPTIMIZACIÓN DE<br />
              <span className="text-primary">HIDRATACIÓN</span>
            </h1>
          </div>
          <div className="flex justify-between items-end border-t border-border pt-[10mm]">
            <div>
              <div className="text-[9pt] text-primary font-bold mb-[2mm]">PREPARADO EXCLUSIVAMENTE PARA:</div>
              <div className="text-[16pt] font-semibold font-outfit uppercase">[CLIENTE CORPORATIVO]</div>
              <div className="text-[10pt] text-gray-dark mt-[2mm]">{currentDate}</div>
            </div>
            <div className="text-right text-[10pt] leading-[1.4]">
              <span className="font-bold text-primary">AGUAS ARAUKA</span><br />
              Dirección Comercial<br />
              aguasarauka.com
            </div>
          </div>
        </div>
      </div>

      <div className="page">
        <h2 className="border-b-2 border-primary pb-1 mb-[15px] text-[16pt] text-primary mt-[10mm] font-outfit uppercase tracking-tighter font-semibold">Rentabilidad y Diferenciación</h2>
        <div className="grid grid-cols-2 gap-[15px] mb-[20px]">
          <div className="p-[15px] border border-border rounded-lg bg-light flex flex-col">
            <h4 className="text-[11pt] mb-[5px] text-primary font-outfit uppercase tracking-tighter font-semibold">01. Eficiencia en Costos (ROI)</h4>
            <p className="text-[9.5pt] text-gray-dark">Eliminamos el gasto innecesario en envases plásticos rígidos. Nuestro sistema de sachet reduce hasta un 35% los costos operativos de hidratación masiva sin comprometer la pureza.</p>
          </div>
          <div className="p-[15px] border border-border rounded-lg bg-light flex flex-col">
            <h4 className="text-[11pt] mb-[5px] text-primary font-outfit uppercase tracking-tighter font-semibold">02. Exclusividad de Marca</h4>
            <p className="text-[9.5pt] text-gray-dark">No solo suministramos agua; proyectamos su marca. El servicio de Marca Blanca convierte cada sachet en un activo publicitario directo para sus clientes y colaboradores.</p>
          </div>
        </div>

        <h2 className="border-b-2 border-primary pb-1 mb-[15px] text-[16pt] text-primary mt-[10mm] font-outfit uppercase tracking-tighter font-semibold">Estructura Comercial Preferencial</h2>
        <table className="w-full border-collapse my-[20px] text-[10pt] text-left">
          <thead>
            <tr>
              <th className="bg-dark text-white p-3 uppercase text-[8pt] font-semibold">Producto / Servicio</th>
              <th className="bg-dark text-white p-3 uppercase text-[8pt] font-semibold">Especificación Técnica</th>
              <th className="bg-dark text-white p-3 uppercase text-[8pt] font-semibold text-right">Inversión por Unidad</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="p-3 border-b border-border"><strong>Sachet Corporativo Premium</strong></td>
              <td className="p-3 border-b border-border">Agua Mineral 400ml / Empaque de alta resistencia.</td>
              <td className="p-3 border-b border-border text-right"><span className="text-primary font-bold text-[11pt]">$0.125</span></td>
            </tr>
            <tr>
              <td className="p-3 border-b border-border"><strong>Paquete (20 uds)</strong></td>
              <td className="p-3 border-b border-border">Ideal para logística de campo y eventos masivos.</td>
              <td className="p-3 border-b border-border text-right"><span className="text-primary font-bold text-[11pt]">$2.50</span></td>
            </tr>
            <tr className="bg-[#f0f9ff]">
              <td className="p-3 border-b border-border"><strong>Servicio de Rebranding</strong></td>
              <td className="p-3 border-b border-border">Fidelice a sus clientes corporativos. Beneficios y factibilidad a debatir en detalle si el cliente muestra interés.</td>
              <td className="p-3 border-b border-border text-primary font-bold text-[8pt] text-right">A CONVENIR</td>
            </tr>
          </tbody>
        </table>

        <div className="bg-primary text-white p-5 rounded-lg text-center my-[20px]">
          <h3 className="text-[13pt] mb-[5px] font-outfit uppercase tracking-tight font-semibold">CALIDAD, RENTABILIDAD Y MARCA BLANCA</h3>
          <p className="text-[9.5pt] opacity-90 mb-4">Garantice para su empresa un suministro de agua con pureza insuperable y el precio más competitivo del mercado. Transforme nuestro empaque en el embajador de su propia marca.</p>
          <div className="flex flex-wrap justify-center gap-5 text-[9pt] font-semibold tracking-wide">
            <div className="flex items-center gap-2 bg-white/10 px-4 py-1.5 rounded-full border border-white/20"><Droplet className="w-4 h-4 text-secondary" /> PUREZA TOTAL</div>
            <div className="flex items-center gap-2 bg-white/10 px-4 py-1.5 rounded-full border border-white/20"><TrendingUp className="w-4 h-4 text-secondary" /> ALTA RENTABILIDAD</div>
            <div className="flex items-center gap-2 bg-white/10 px-4 py-1.5 rounded-full border border-white/20"><Tag className="w-4 h-4 text-secondary" /> REBRANDING</div>
          </div>
        </div>

        <div className="absolute bottom-[15mm] left-[25mm] right-[25mm] text-center text-[8pt] text-[#ccc] border-t border-[#eee] pt-[5px] flex items-center justify-center gap-[8px]">
          <span>Propuesta Estrictamente Confidencial — Aguas Arauka B2B</span>
        </div>
      </div>

      <div className="page">
        <h2 className="border-b-2 border-primary pb-1 mb-[15px] text-[16pt] text-primary mt-[10mm] font-outfit uppercase tracking-tighter font-semibold">Alcance Logístico Inmediato</h2>
        <div className="grid grid-cols-2 gap-[15px] mb-[20px]">
          <div className="p-[15px] border border-border rounded-lg bg-light flex flex-col">
            <p className="text-[9.5pt]"><strong className="font-semibold">Gran Caracas:</strong> Entregas en 24h para pedidos superiores a 50 paquetes.</p>
          </div>
          <div className="p-[15px] border border-border rounded-lg bg-light flex flex-col">
            <p className="text-[9.5pt]"><strong className="font-semibold">Eje Central:</strong> Cobertura prioritaria en La Guaira, Aragua y Valencia con flota propia.</p>
          </div>
        </div>

        <div className="w-full mb-[20px] flex justify-center">
          <img src={para1Img} alt="Trabajador bebiendo agua" className="w-full h-auto object-contain max-h-[240px] rounded-lg" />
        </div>

        <h2 className="border-b-2 border-primary pb-1 mb-[15px] text-[16pt] text-primary mt-[10mm] font-outfit uppercase tracking-tighter font-semibold">¿Por qué cerrar este acuerdo hoy?</h2>
        <ul className="list-none my-[20px]">
          <li className="mb-[10px] text-[10pt] flex items-start gap-[10px]">
            <span className="text-success font-bold">✓</span>
            <span><strong>Ahorro Inmediato:</strong> Reducción directa de costos logísticos desde el primer despacho.</span>
          </li>
          <li className="mb-[10px] text-[10pt] flex items-start gap-[10px]">
             <span className="text-success font-bold">✓</span>
             <span><strong>Sostenibilidad:</strong> Reducción del 70% en el uso de plástico comparado con botellas PET tradicionales.</span>
          </li>
          <li className="mb-[10px] text-[10pt] flex items-start gap-[10px]">
             <span className="text-success font-bold">✓</span>
             <span><strong>Disponibilidad Garantizada:</strong> Reserva de stock exclusivo para su cadena de suministro.</span>
          </li>
          <li className="mb-[10px] text-[10pt] flex items-start gap-[10px]">
             <span className="text-success font-bold">✓</span>
             <span><strong>Impacto de Marca:</strong> Implementación inmediata de su diseño corporativo en los empaques.</span>
          </li>
        </ul>

        <div className="border-l-4 border-secondary pl-5 mt-[30px]">
          <h3 className="text-primary text-[14pt] mb-[10px] font-outfit uppercase tracking-tight font-semibold">Compromiso de Dirección</h3>
          <p className="italic text-gray-dark text-[10.5pt] mb-[20px]">
            "En Aguas Arauka no buscamos proveedores, buscamos aliados. Esta propuesta está diseñada para optimizar sus recursos y elevar su estándar corporativo. Estamos listos para iniciar mañana mismo."
          </p>
          <div className="font-bold text-[11pt]">Director Comercial</div>
          <div className="text-primary font-semibold">+58 424 600.0311</div>
          <div className="text-[9pt] text-gray-dark">ventas@aguasarauka.com</div>
        </div>

        <div className="absolute bottom-[10mm] left-[25mm] right-[25mm] text-center text-[8pt] text-[#ccc] border-t border-[#eee] pt-[5px] flex items-center justify-center gap-[8px]">
          <p>© 2024 Aguas Arauka. Todos los derechos reservados. Sujeto a términos de contrato corporativo.</p>
        </div>
      </div>
    </>
  );
}
