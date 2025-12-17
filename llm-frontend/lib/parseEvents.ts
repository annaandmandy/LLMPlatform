import type { Message, Citation, ProductCardData } from '../hooks/useChat';

interface BackendEvent {
    t: number;
    type: string;
    data: any;
}

/**
 * Parse backend session events into Message[] format
 * Extracts prompt/response pairs from the events array
 */
export function parseEventsToMessages(events: BackendEvent[]): Message[] {
    const messages: Message[] = [];

    if (!events || !Array.isArray(events)) {
        return messages;
    }

    // Group events by pairs (prompt + response)
    for (let i = 0; i < events.length; i++) {
        const event = events[i];

        // User message (prompt event)
        if (event.type === 'prompt' && event.data) {
            messages.push({
                role: 'user',
                content: event.data.text || event.data.query || '',
                timestamp: new Date(event.t),
                attachments: event.data.attachments || []
            });
        }

        // Assistant message (response or model_response event)
        if ((event.type === 'response' || event.type === 'model_response') && event.data) {
            messages.push({
                role: 'assistant',
                content: event.data.text || event.data.response || '',
                timestamp: new Date(event.t),
                citations: event.data.citations || [],
                product_cards: event.data.product_cards || event.data.products || [],
                options: event.data.options || []
            });
        }
    }

    return messages;
}
