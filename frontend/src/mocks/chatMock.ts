import { Conversation, Message } from '@/types/chat';

const now = new Date();
const mins = (n: number) => new Date(now.getTime() - n * 60_000).toISOString();

export const mockConversations: Conversation[] = [
  {
    id: '1',
    contactName: 'Ana García',
    contactPhone: '+54 11 4567-8901',
    status: 'open',
    mode: 'ai',
    lastMessage: 'Claro, te ayudo con eso 😊',
    lastMessageAt: mins(4),
    unreadCount: 2,
  },
  {
    id: '2',
    contactName: 'Carlos Méndez',
    contactPhone: '+54 11 2345-6789',
    status: 'open',
    mode: 'human',
    lastMessage: 'Quiero hablar con un asesor',
    lastMessageAt: mins(30),
    unreadCount: 0,
  },
  {
    id: '3',
    contactName: 'Laura Torres',
    contactPhone: '+54 11 9876-5432',
    status: 'open',
    mode: 'ai',
    lastMessage: '¿Cuáles son los horarios de atención?',
    lastMessageAt: mins(120),
    unreadCount: 1,
  },
  {
    id: '4',
    contactName: 'Roberto Suárez',
    contactPhone: '+54 351 123-4567',
    status: 'closed',
    mode: 'human',
    lastMessage: 'Muchas gracias, hasta pronto!',
    lastMessageAt: mins(1440),
    unreadCount: 0,
  },
  {
    id: '5',
    contactName: 'Valentina Ríos',
    contactPhone: '+54 11 8765-4321',
    status: 'open',
    mode: 'ai',
    lastMessage: '¿Tienen descuentos para empresas?',
    lastMessageAt: mins(200),
    unreadCount: 0,
  },
];

export const mockMessages: Record<string, Message[]> = {
  '1': [
    {
      id: 'm1',
      conversationId: '1',
      direction: 'inbound',
      senderType: 'contact',
      content: 'Hola! Necesito info sobre sus productos.',
      createdAt: mins(15),
    },
    {
      id: 'm2',
      conversationId: '1',
      direction: 'outbound',
      senderType: 'bot',
      content: 'Hola Ana! 👋 Claro, te ayudo con eso. ¿Qué producto te interesa?',
      createdAt: mins(14),
    },
    {
      id: 'm3',
      conversationId: '1',
      direction: 'inbound',
      senderType: 'contact',
      content: 'Me interesa el plan empresarial.',
      createdAt: mins(10),
    },
    {
      id: 'm4',
      conversationId: '1',
      direction: 'outbound',
      senderType: 'bot',
      content:
        'El plan empresarial incluye acceso ilimitado a todas las funcionalidades, soporte prioritario 24/7 y un manager de cuenta dedicado. El precio es de $299 USD/mes.',
      createdAt: mins(9),
    },
    {
      id: 'm5',
      conversationId: '1',
      direction: 'inbound',
      senderType: 'contact',
      content: 'Perfecto! ¿Cómo puedo contratar?',
      createdAt: mins(5),
    },
    {
      id: 'm6',
      conversationId: '1',
      direction: 'outbound',
      senderType: 'bot',
      content: 'Claro, te ayudo con eso 😊',
      createdAt: mins(4),
    },
  ],
  '2': [
    {
      id: 'm7',
      conversationId: '2',
      direction: 'inbound',
      senderType: 'contact',
      content: 'Buen día, ¿me podrían pasar el precio del servicio básico?',
      createdAt: mins(45),
    },
    {
      id: 'm8',
      conversationId: '2',
      direction: 'outbound',
      senderType: 'agent',
      content:
        'Hola Carlos! Soy Martín del equipo de ventas. El servicio básico está en $49 USD/mes. ¿Te mando más detalle?',
      createdAt: mins(40),
    },
    {
      id: 'm9',
      conversationId: '2',
      direction: 'inbound',
      senderType: 'contact',
      content: 'Quiero hablar con un asesor',
      createdAt: mins(30),
    },
  ],
  '3': [
    {
      id: 'm10',
      conversationId: '3',
      direction: 'inbound',
      senderType: 'contact',
      content: '¿Cuáles son los horarios de atención?',
      createdAt: mins(120),
    },
  ],
  '4': [
    {
      id: 'm11',
      conversationId: '4',
      direction: 'inbound',
      senderType: 'contact',
      content: 'Muchas gracias por la ayuda!',
      createdAt: mins(1450),
    },
    {
      id: 'm12',
      conversationId: '4',
      direction: 'outbound',
      senderType: 'agent',
      content: 'De nada! Fue un placer ayudarte. Hasta pronto!',
      createdAt: mins(1445),
    },
    {
      id: 'm13',
      conversationId: '4',
      direction: 'inbound',
      senderType: 'contact',
      content: 'Muchas gracias, hasta pronto!',
      createdAt: mins(1440),
    },
  ],
  '5': [
    {
      id: 'm14',
      conversationId: '5',
      direction: 'inbound',
      senderType: 'contact',
      content: '¿Tienen descuentos para empresas?',
      createdAt: mins(200),
    },
  ],
};
